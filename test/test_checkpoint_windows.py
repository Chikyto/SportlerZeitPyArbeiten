#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests de ventanas de tiempo para checkpoints.

Escenarios reales que el validador debe resolver:
- Relectura en el mismo CP no puede convertirse en el CP siguiente
- CP perdido no corre la numeración (identificación por antena)
- CP prematuro (físicamente imposible) se rechaza
- Antena combinada checkpoint+meta: meta prematura cae a checkpoint
- Sin definiciones de km: comportamiento histórico (secuencial)
- Persistencia: los checkpoints sobreviven al ciclo guardar/restaurar
"""

import sys
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.race_tracking.models import (
    Athlete, RaceDistance, AthleteResult, EventType
)
from src.core.race_tracking.checkpoint_config import CheckpointDef
from src.core.race_tracking.detection_validator import resolve_event, checkpoint_km_for_event
from src.core.race_tracking.race_manager import RaceManager
from src.core.race_tracking.persistence import RaceStatePersistence


def build_10k():
    """10K con CP1 en km 2.5 (antena 3) y CP2 en km 7 (antena 5)"""
    distance = RaceDistance(
        distance_id="10k",
        name="10 Kilómetros",
        distance_meters=10000.0,
        expected_checkpoints=2,
        checkpoints=[
            CheckpointDef(number=1, km=2.5, antenna_port=3),
            CheckpointDef(number=2, km=7.0, antenna_port=5),
        ],
    )
    athlete = Athlete(tag_id="A001", bib_number=1, name="Corredor Uno",
                      distance_id="10k")
    distance.add_participant(athlete)
    return distance, athlete


def started_result(athlete, distance, t0):
    result = AthleteResult(athlete=athlete, distance_id=distance.distance_id)
    result.record_start(t0)
    return result


def test_premature_checkpoint_rejected():
    distance, athlete = build_10k()
    t0 = datetime.now()
    result = started_result(athlete, distance, t0)

    # km 2.5 a velocidad máx de fondo (6 m/s) = mínimo ~417s
    ev, cp, reason = resolve_event(
        ['checkpoint'], 3, result, distance, t0 + timedelta(seconds=30))
    assert ev is None, f"CP a los 30s debe rechazarse: {reason}"
    assert "prematuro" in reason

    ev, cp, _ = resolve_event(
        ['checkpoint'], 3, result, distance, t0 + timedelta(seconds=500))
    assert ev == EventType.CHECKPOINT and cp == 1
    print("✅ CP prematuro rechazado; CP en tiempo plausible aceptado")


def test_reread_does_not_become_next_cp():
    distance, athlete = build_10k()
    t0 = datetime.now()
    result = started_result(athlete, distance, t0)

    result.record_checkpoint(1, t0 + timedelta(seconds=500))

    # Relectura en la MISMA antena 10s después: la antena 3 ya no tiene
    # CPs pendientes → rechazada (antes se registraba como CP2 falso)
    ev, cp, reason = resolve_event(
        ['checkpoint'], 3, result, distance, t0 + timedelta(seconds=510))
    assert ev is None, f"Relectura no debe ser CP2: {reason}"

    # Y en la antena del CP2, demasiado pronto → rechazada (ventana
    # total: km 7 necesita ≥ ~1167s desde la largada)
    ev, cp, reason = resolve_event(
        ['checkpoint'], 5, result, distance, t0 + timedelta(seconds=520))
    assert ev is None, f"CP2 a los 520s debe rechazarse: {reason}"

    # Caso ventana de TRAMO: tiempo total suficiente para km 7, pero
    # el tramo CP1(km2.5 @500s)→CP2(km4.5 de tramo) en ~700s es imposible
    result_b = started_result(athlete, distance, t0 - timedelta(seconds=3600))
    result_b.record_checkpoint(1, t0 + timedelta(seconds=500))
    ev, cp, reason = resolve_event(
        ['checkpoint'], 5, result_b, distance, t0 + timedelta(seconds=600))
    assert ev is None and "imposible" in reason, \
        f"Tramo imposible debe rechazarse por ventana de segmento: {reason}"

    # CP2 en tiempo plausible (tramo 4.5km ≥ 750s) → aceptado
    ev, cp, _ = resolve_event(
        ['checkpoint'], 5, result, distance, t0 + timedelta(seconds=500 + 800))
    assert ev == EventType.CHECKPOINT and cp == 2
    print("✅ Relectura no genera CP fantasma; CP2 real aceptado")


def test_missed_cp1_does_not_shift_numbering():
    distance, athlete = build_10k()
    t0 = datetime.now()
    result = started_result(athlete, distance, t0)

    # Al corredor NO le leyeron el CP1. Su lectura en la antena del CP2
    # debe registrarse como CP2 (con secuencia pura quedaría "CP1")
    ev, cp, _ = resolve_event(
        ['checkpoint'], 5, result, distance, t0 + timedelta(seconds=1300))
    assert ev == EventType.CHECKPOINT and cp == 2, \
        "El CP debe identificarse por antena, no por secuencia"
    print("✅ CP1 perdido no corre la numeración (CP2 por antena)")


def test_combined_finish_checkpoint_antenna():
    """Antena con roles checkpoint+finish: meta prematura cae a checkpoint"""
    distance = RaceDistance(
        distance_id="5k", name="5K", distance_meters=5000.0,
        expected_checkpoints=1,
        checkpoints=[CheckpointDef(number=1, km=2.0, antenna_port=7)],
    )
    athlete = Athlete(tag_id="B001", bib_number=2, name="Corredora Dos",
                      distance_id="5k")
    distance.add_participant(athlete)
    t0 = datetime.now()
    result = started_result(athlete, distance, t0)

    # A los 400s: meta imposible (mínimo 5000/6≈833s) pero el CP del
    # km 2 sí es plausible (mínimo 2000/6≈333s) → CHECKPOINT
    ev, cp, _ = resolve_event(
        ['checkpoint', 'finish'], 7, result, distance,
        t0 + timedelta(seconds=400))
    assert ev == EventType.CHECKPOINT and cp == 1, \
        "Meta prematura en antena combinada debe evaluarse como checkpoint"

    # A los 900s (CP1 ya registrado): meta válida → FINISH
    result.record_checkpoint(1, t0 + timedelta(seconds=400))
    ev, cp, _ = resolve_event(
        ['checkpoint', 'finish'], 7, result, distance,
        t0 + timedelta(seconds=900))
    assert ev == EventType.FINISH
    print("✅ Antena combinada: meta prematura → checkpoint; meta válida → meta")


def test_no_definitions_keeps_legacy_behavior():
    distance = RaceDistance(
        distance_id="5k", name="5K", distance_meters=5000.0,
        expected_checkpoints=2,
    )
    athlete = Athlete(tag_id="C001", bib_number=3, name="Corredor Tres",
                      distance_id="5k")
    distance.add_participant(athlete)
    t0 = datetime.now()
    result = started_result(athlete, distance, t0)

    ev, cp, _ = resolve_event(
        ['checkpoint'], 4, result, distance, t0 + timedelta(seconds=10))
    assert ev == EventType.CHECKPOINT and cp == 1
    result.record_checkpoint(1, t0 + timedelta(seconds=10))

    ev, cp, _ = resolve_event(
        ['checkpoint'], 4, result, distance, t0 + timedelta(seconds=20))
    assert ev == EventType.CHECKPOINT and cp == 2
    print("✅ Sin definiciones de km: comportamiento secuencial histórico")


def test_full_flow_through_race_manager():
    """Integración: process_detection aplica las ventanas"""
    manager = RaceManager()
    distance, athlete = build_10k()
    manager.add_distance(distance)
    manager.start_distance("10k")

    t0 = datetime.now() - timedelta(minutes=30)
    manager.results["10k"][athlete.athlete_id].record_start(t0)

    # Lectura en antena CP1 (puerto 3) con tiempo plausible
    event = manager.process_detection(
        tag_id="A001",
        timestamp=t0 + timedelta(seconds=600),
        antenna_port=3,
        roles=['checkpoint'],
    )
    assert event is not None and event.checkpoint_number == 1

    # Relectura 30s después en la misma antena (pasada la ventana
    # anti-duplicado de 3s): rechazada por ventanas de checkpoint
    event = manager.process_detection(
        tag_id="A001",
        timestamp=t0 + timedelta(seconds=630),
        antenna_port=3,
        roles=['checkpoint'],
    )
    assert event is None, "Relectura no debe registrar CP2 fantasma"

    result = manager.results["10k"][athlete.athlete_id]
    assert list(result.checkpoint_times.keys()) == [1]

    # checkpoint_km_for_event para el payload al backend
    assert checkpoint_km_for_event(distance, 1) == 2.5
    assert checkpoint_km_for_event(distance, 99) is None
    print("✅ Integración con RaceManager y km para el backend")


def test_checkpoints_persistence_roundtrip():
    tmpdir = tempfile.mkdtemp(prefix="cp_persist_")
    try:
        persistence = RaceStatePersistence(data_dir=tmpdir)
        manager = RaceManager()
        distance, athlete = build_10k()
        manager.add_distance(distance)
        manager.attach_persistence(persistence)
        manager.save_now()

        persistence2 = RaceStatePersistence(data_dir=tmpdir)
        manager2 = RaceManager()
        assert persistence2.restore_into(manager2)

        restored = manager2.get_distance("10k")
        assert len(restored.checkpoints) == 2
        assert restored.checkpoints[0].number == 1
        assert restored.checkpoints[0].km == 2.5
        assert restored.checkpoints[0].antenna_port == 3
        assert restored.checkpoints[1].km == 7.0

        persistence.close()
        persistence2.close()
        print("✅ Checkpoints sobreviven al ciclo guardar/restaurar (SQLite)")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    test_premature_checkpoint_rejected()
    test_reread_does_not_become_next_cp()
    test_missed_cp1_does_not_shift_numbering()
    test_combined_finish_checkpoint_antenna()
    test_no_definitions_keeps_legacy_behavior()
    test_full_flow_through_race_manager()
    test_checkpoints_persistence_roundtrip()

    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS DE VENTANAS DE CHECKPOINT PASARON")
    print("=" * 60)


if __name__ == "__main__":
    main()
