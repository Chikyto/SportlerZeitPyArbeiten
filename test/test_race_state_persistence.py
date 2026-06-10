#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de persistencia local del estado de carrera (SQLite).

Simula el escenario real: carrera en curso → corte de energía →
reinicio de la app → restauración del estado.

También verifica la migración automática desde el snapshot JSON
de la versión anterior (data/race_state.json).
"""

import json
import sys
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.race_tracking.race_manager import RaceManager
from src.core.race_tracking.models import (
    Athlete, RaceDistance, DetectionEvent, EventType,
    AthleteStatus, RaceStatus
)
from src.core.race_tracking.persistence import RaceStatePersistence


def build_race(manager):
    """Armar una carrera de prueba: 5K con 3 atletas"""
    distance = RaceDistance(
        distance_id="5k",
        name="5 Kilómetros",
        distance_meters=5000.0,
        expected_checkpoints=1,
    )
    athletes = [
        Athlete(tag_id="A001", bib_number=1, name="Juanito Ganador",
                distance_id="5k", gender="M", birth_date=datetime(2007, 3, 1)),
        Athlete(tag_id="A002", bib_number=2, name="Elba Nana",
                distance_id="5k", gender="M", birth_date=datetime(1980, 6, 15)),
        Athlete(tag_id="A003", bib_number=3, name="Probando LoNuevo",
                distance_id="5k", gender="F", birth_date=datetime(1998, 1, 20)),
    ]
    for a in athletes:
        distance.add_participant(a)
    manager.add_distance(distance)
    return athletes


def test_power_cut_cycle(tmpdir):
    """Carrera en curso → corte → restauración → seguir operando"""
    # ====== SESIÓN 1: carrera en curso ======
    persistence = RaceStatePersistence(data_dir=tmpdir)
    manager = RaceManager()
    manager.attach_persistence(persistence)

    athletes = build_race(manager)
    manager.start_distance("5k")

    t0 = datetime.now() - timedelta(minutes=20)

    # Largada de los 3 (timestamps directos para no depender del grace period)
    for a in athletes:
        manager.results["5k"][a.athlete_id].record_start(t0)
    manager.save_now()

    # Checkpoint del atleta 1
    manager.results["5k"][athletes[0].athlete_id].record_checkpoint(
        1, t0 + timedelta(minutes=10))

    # Atleta 1 termina en 18:30 — persistido por el hot path incremental
    finish_ts = t0 + timedelta(minutes=18, seconds=30)
    manager.results["5k"][athletes[0].athlete_id].record_finish(finish_ts)
    manager._update_classification("5k")

    finish_event = DetectionEvent(
        tag_id="A001",
        timestamp=finish_ts,
        antenna_port=7,
        event_type=EventType.FINISH,
        athlete=athletes[0],
        distance_id="5k",
    )
    manager.detection_history.append(finish_event)
    manager.last_detections[(athletes[0].athlete_id, 7)] = finish_ts
    assert persistence.record_detection(manager, "5k", finish_event)

    # Journal de detecciones crudas
    persistence.log_detection("A001", t0, 3, ["start"])
    persistence.log_detection("A001", finish_ts, 7, ["finish"])

    db_file = Path(tmpdir) / "race_event.db"
    assert db_file.exists(), "La base SQLite no se creó"
    print(f"✅ Base SQLite creada ({db_file.stat().st_size} bytes)")

    journals = list(Path(tmpdir).glob("detections_*.jsonl"))
    assert journals and journals[0].stat().st_size > 0, "Journal vacío"
    print(f"✅ Journal de detecciones: {journals[0].name} ({journals[0].stat().st_size} bytes)")

    # ====== CORTE DE ENERGÍA (sin shutdown limpio: no llamamos close) ======
    del manager, persistence

    # ====== SESIÓN 2: reinicio y restauración ======
    persistence2 = RaceStatePersistence(data_dir=tmpdir)
    assert persistence2.has_saved_state(), "No se detectó el estado guardado"

    summary = persistence2.get_state_summary()
    print(f"✅ Resumen: {summary['distances']} distancias, {summary['athletes']} atletas, "
          f"{summary['running']} en carrera, {summary['finished']} finalizados")
    assert summary['athletes'] == 3
    assert summary['running'] == 2
    assert summary['finished'] == 1
    assert summary['distances_running'] == ["5 Kilómetros"]

    manager2 = RaceManager()
    ok = persistence2.restore_into(manager2)
    assert ok, "restore_into falló"

    # Verificar distancia
    dist = manager2.get_distance("5k")
    assert dist is not None
    assert dist.status == RaceStatus.RUNNING
    assert dist.start_time is not None
    assert len(dist.participants) == 3

    # Verificar resultados
    results = {r.athlete.name: r for r in manager2.get_results("5k")}
    r1 = results["Juanito Ganador"]
    assert r1.status == AthleteStatus.FINISHED
    assert r1.position == 1
    assert abs(r1.total_time.total_seconds() - (18 * 60 + 30)) < 0.001
    assert 1 in r1.checkpoint_times and 1 in r1.splits

    r2 = results["Elba Nana"]
    assert r2.status == AthleteStatus.RUNNING
    assert r2.start_time is not None
    assert r2.finish_time is None

    # Evento del hot path restaurado
    assert len(manager2.detection_history) == 1
    assert manager2.detection_history[0].event_type == EventType.FINISH
    assert manager2.detection_history[0].athlete.name == "Juanito Ganador"

    # Anti-duplicados restaurado
    assert (r1.athlete.athlete_id, 7) in manager2.last_detections

    # Edad/categoría siguen funcionando tras restaurar (birth_date OK)
    assert r1.athlete.get_age() is not None
    assert r1.athlete.get_award_category() is not None

    # El manager restaurado puede seguir operando y guardando
    manager2.attach_persistence(persistence2)
    manager2.results["5k"][r2.athlete.athlete_id].record_finish(
        datetime.now() - timedelta(minutes=20) + timedelta(minutes=22))
    manager2._update_classification("5k")
    manager2.save_now()
    print("✅ Estado restaurado y operativo: el 2º atleta pudo finalizar tras el reinicio")

    # ====== Restauración tras el segundo guardado ======
    persistence3 = RaceStatePersistence(data_dir=tmpdir)
    manager3 = RaceManager()
    assert persistence3.restore_into(manager3)
    results3 = {r.athlete.name: r for r in manager3.get_results("5k")}
    assert results3["Elba Nana"].status == AthleteStatus.FINISHED
    assert results3["Elba Nana"].position == 2
    print("✅ Segunda restauración correcta (posiciones 1 y 2 intactas)")

    # ====== Archivar evento ======
    persistence2.close()
    backup = persistence3.archive()
    assert backup and backup.exists()
    assert not persistence3.has_saved_state()
    print(f"✅ Archive funciona: {backup.name}")
    persistence3.close()


def test_legacy_json_migration(tmpdir):
    """El snapshot JSON de la versión anterior se migra a SQLite"""
    athlete_id = "legacy-athlete-1"
    legacy_state = {
        'version': 1,
        'saved_at': datetime.now().isoformat(),
        'distances': [{
            'distance_id': '10k',
            'name': '10 Kilómetros',
            'distance_meters': 10000.0,
            'expected_checkpoints': 0,
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'notes': None,
            'race_mode': 'linear',
            'duration_hours': None,
            'participants': [{
                'tag_id': 'B001',
                'bib_number': 10,
                'name': 'Atleta Legado',
                'distance_id': '10k',
                'gender': 'F',
                'birth_date': None,
                'team': None,
                'notes': None,
                'athlete_id': athlete_id,
            }],
        }],
        'results': {'10k': {athlete_id: {
            'athlete_id': athlete_id,
            'distance_id': '10k',
            'status': 'running',
            'start_time': datetime.now().isoformat(),
            'finish_time': None,
            'total_time': None,
            'splits': {},
            'checkpoint_times': {},
            'position': None,
        }}},
        'award_categories': [],
        'detection_history': [],
        'last_detections': [],
    }

    legacy_file = Path(tmpdir) / "race_state.json"
    with open(legacy_file, 'w', encoding='utf-8') as f:
        json.dump(legacy_state, f)

    persistence = RaceStatePersistence(data_dir=tmpdir)
    assert persistence.has_saved_state(), "No detectó el JSON legado"

    summary = persistence.get_state_summary()
    assert summary['athletes'] == 1 and summary['running'] == 1

    manager = RaceManager()
    assert persistence.restore_into(manager)
    assert manager.get_distance("10k") is not None
    assert manager.results["10k"][athlete_id].status == AthleteStatus.RUNNING

    # Tras la migración: la DB tiene los datos y el JSON quedó archivado
    assert not legacy_file.exists(), "El JSON legado no se archivó"
    assert list(Path(tmpdir).glob("race_state_migrated_*.json")), "Falta el archivo migrado"

    persistence2 = RaceStatePersistence(data_dir=tmpdir)
    manager2 = RaceManager()
    assert persistence2.restore_into(manager2), "La DB migrada no restaura"
    assert manager2.get_distance("10k") is not None
    print("✅ Migración JSON legado → SQLite correcta")

    persistence.close()
    persistence2.close()


def main():
    for test_fn in (test_power_cut_cycle, test_legacy_json_migration):
        tmpdir = tempfile.mkdtemp(prefix="race_persist_test_")
        print(f"\n--- {test_fn.__name__} ({tmpdir}) ---")
        try:
            test_fn(tmpdir)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS DE PERSISTENCIA PASARON")
    print("=" * 60)


if __name__ == "__main__":
    main()
