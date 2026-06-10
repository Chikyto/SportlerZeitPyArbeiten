#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de persistencia local del estado de carrera.

Simula el escenario real: carrera en curso → corte de energía →
reinicio de la app → restauración del estado.
"""

import sys
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.race_tracking.race_manager import RaceManager
from src.core.race_tracking.models import (
    Athlete, RaceDistance, AthleteStatus, RaceStatus
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


def main():
    tmpdir = tempfile.mkdtemp(prefix="race_persist_test_")
    print(f"Directorio temporal: {tmpdir}")

    try:
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

        # Atleta 1 termina en 18:30
        manager.results["5k"][athletes[0].athlete_id].record_finish(
            t0 + timedelta(minutes=18, seconds=30))
        manager._update_classification("5k")
        manager.save_now()

        # Journal de detecciones crudas
        persistence.log_detection("A001", t0, 3, ["start"])
        persistence.log_detection("A001", t0 + timedelta(minutes=18, seconds=30), 7, ["finish"])

        state_file = Path(tmpdir) / "race_state.json"
        assert state_file.exists(), "El snapshot no se creó"
        print(f"✅ Snapshot creado ({state_file.stat().st_size} bytes)")

        journals = list(Path(tmpdir).glob("detections_*.jsonl"))
        assert journals and journals[0].stat().st_size > 0, "Journal vacío"
        print(f"✅ Journal de detecciones: {journals[0].name} ({journals[0].stat().st_size} bytes)")

        # ====== CORTE DE ENERGÍA (no hay shutdown limpio) ======
        persistence.close()
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

        # Edad/categoría siguen funcionando tras restaurar (birth_date OK)
        assert r1.athlete.get_age() is not None
        assert r1.athlete.get_award_category() is not None

        # Anti-duplicados e historial restaurados sin romper
        assert isinstance(manager2.last_detections, dict)

        # El manager restaurado puede seguir operando y guardando
        manager2.attach_persistence(persistence2)
        manager2.results["5k"][r2.athlete.athlete_id].record_finish(
            t0 + timedelta(minutes=22))
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

        # ====== Archivar ======
        backup = persistence3.archive()
        assert backup and backup.exists()
        assert not persistence3.has_saved_state()
        print(f"✅ Archive funciona: {backup.name}")

        print("\n" + "=" * 60)
        print("✅ TODOS LOS TESTS DE PERSISTENCIA PASARON")
        print("=" * 60)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
