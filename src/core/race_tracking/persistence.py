#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Persistencia local del estado de carrera (SQLite)
src/core/race_tracking/persistence.py

Protege el estado del RaceManager contra cortes de energía o cierres
inesperados de la aplicación:

1. Base de datos SQLite (data/race_event.db) en modo WAL con
   synchronous=FULL: cada commit queda físicamente en disco y un corte
   de luz a mitad de escritura nunca corrompe la base (el WAL se
   descarta o aplica completo al reabrir).

   - Mutaciones grandes y poco frecuentes (alta de distancias, largada,
     finalización, reset, chips) → save_state(): resincroniza todo.
   - Hot path de detecciones → record_detection(): escritura incremental
     (un INSERT + upserts de la distancia afectada), costo constante
     aunque el evento tenga miles de lecturas acumuladas.

2. Journal de detecciones: cada lectura cruda del lector se agrega a
   data/detections_YYYYMMDD.jsonl (append-only, con fsync). Aunque se
   pierda la base, las lecturas crudas permiten reconstruir la carrera.

Al iniciar la aplicación, si existe estado guardado, se ofrece
restaurarlo. Al descartar una sesión o empezar un evento nuevo, la base
no se borra: se archiva con timestamp (un archivo .db por evento).

Compatibilidad: si existe un data/race_state.json de la versión anterior
(snapshot JSON) y la base está vacía, se migra automáticamente.
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import (
    Athlete, RaceDistance, DetectionEvent, AthleteResult,
    AthleteStatus, RaceStatus, EventType, RaceMode, AwardCategory
)

logger = logging.getLogger(__name__)

STATE_VERSION = 2

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS distances (
    distance_id          TEXT PRIMARY KEY,
    name                 TEXT NOT NULL,
    distance_meters      REAL NOT NULL,
    expected_checkpoints INTEGER,
    status               TEXT NOT NULL,
    start_time           TEXT,
    end_time             TEXT,
    notes                TEXT,
    race_mode            TEXT,
    duration_hours       REAL
);
CREATE TABLE IF NOT EXISTS athletes (
    athlete_id  TEXT PRIMARY KEY,
    distance_id TEXT NOT NULL,
    tag_id      TEXT,
    bib_number  INTEGER,
    name        TEXT NOT NULL,
    gender      TEXT,
    birth_date  TEXT,
    team        TEXT,
    notes       TEXT
);
CREATE TABLE IF NOT EXISTS results (
    distance_id      TEXT NOT NULL,
    athlete_id       TEXT NOT NULL,
    status           TEXT NOT NULL,
    start_time       TEXT,
    finish_time      TEXT,
    total_time       REAL,
    splits           TEXT,
    checkpoint_times TEXT,
    position         INTEGER,
    PRIMARY KEY (distance_id, athlete_id)
);
CREATE TABLE IF NOT EXISTS detection_events (
    event_id          TEXT PRIMARY KEY,
    tag_id            TEXT NOT NULL,
    timestamp         TEXT NOT NULL,
    antenna_port      INTEGER,
    event_type        TEXT NOT NULL,
    checkpoint_number INTEGER,
    athlete_id        TEXT,
    distance_id       TEXT
);
CREATE TABLE IF NOT EXISTS last_detections (
    athlete_id   TEXT NOT NULL,
    antenna_port INTEGER NOT NULL,
    timestamp    TEXT NOT NULL,
    PRIMARY KEY (athlete_id, antenna_port)
);
CREATE TABLE IF NOT EXISTS award_categories (
    award_category_id TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    gender            TEXT,
    min_age           INTEGER,
    max_age           INTEGER,
    distance_ids      TEXT,
    is_iaaf           INTEGER,
    description       TEXT
);
"""

_TABLES = [
    'distances', 'athletes', 'results',
    'detection_events', 'last_detections', 'award_categories'
]


def _dt(value: Optional[datetime]) -> Optional[str]:
    """datetime → ISO string (o None)"""
    return value.isoformat() if value else None


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """ISO string → datetime (o None)"""
    return datetime.fromisoformat(value) if value else None


class RaceStatePersistence:
    """
    Guarda y restaura el estado completo del RaceManager en SQLite.

    Example:
        >>> persistence = RaceStatePersistence()
        >>> manager.attach_persistence(persistence)
        >>> # ... ante un reinicio:
        >>> if persistence.has_saved_state():
        ...     persistence.restore_into(manager)
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.data_dir / "race_event.db"
        # Snapshot JSON de la versión anterior (solo lectura/migración)
        self.legacy_state_file = self.data_dir / "race_state.json"

        self._lock = threading.Lock()
        self._conn = None
        self._journal_file = None  # handle abierto del journal del día
        self._journal_date = None

        self._open_db()

    # ========================================================================
    # BASE DE DATOS
    # ========================================================================

    def _open_db(self):
        self._conn = sqlite3.connect(str(self.db_file), check_same_thread=False)
        # WAL + FULL: cada commit queda en disco; un corte de energía
        # nunca deja la base corrupta (el WAL se recupera al reabrir).
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def _db_has_data(self) -> bool:
        try:
            cur = self._conn.execute("SELECT 1 FROM distances LIMIT 1")
            return cur.fetchone() is not None
        except sqlite3.Error:
            return False

    # ========================================================================
    # GUARDADO
    # ========================================================================

    def save_state(self, manager) -> bool:
        """
        Resincronizar TODO el estado del RaceManager con la base.

        Para mutaciones poco frecuentes (alta/baja de distancias, largada,
        finalización, reset, chips, DNF). Para detecciones usar
        record_detection(), que es incremental.

        Returns:
            bool: True si se guardó correctamente
        """
        try:
            with self._lock, self._conn:
                c = self._conn
                for table in _TABLES:
                    c.execute(f"DELETE FROM {table}")

                for distance in manager.distances.values():
                    self._upsert_distance(c, distance)
                    for athlete in distance.participants:
                        self._upsert_athlete(c, athlete)

                for distance_id, dist_results in manager.results.items():
                    for result in dist_results.values():
                        self._upsert_result(c, distance_id, result)

                for ac in manager.award_categories.values():
                    self._upsert_award_category(c, ac)

                c.executemany(
                    "INSERT OR REPLACE INTO detection_events VALUES (?,?,?,?,?,?,?,?)",
                    [self._event_row(e) for e in manager.detection_history]
                )

                c.executemany(
                    "INSERT OR REPLACE INTO last_detections VALUES (?,?,?)",
                    [(athlete_id, port, _dt(ts))
                     for (athlete_id, port), ts in manager.last_detections.items()]
                )

                self._touch_meta(c)
            return True

        except Exception as e:
            # Guardar nunca debe interrumpir el cronometraje
            logger.error(f"❌ Error guardando estado de carrera: {e}", exc_info=True)
            return False

    def record_detection(self, manager, distance_id: str,
                         event: DetectionEvent) -> bool:
        """
        Persistir una detección procesada (hot path, incremental).

        Escribe solo lo que cambió: el evento, los resultados de la
        distancia afectada (posiciones incluidas) y el anti-duplicados.
        Costo constante por detección, sin importar el tamaño del evento.
        """
        try:
            with self._lock, self._conn:
                c = self._conn

                c.execute(
                    "INSERT OR REPLACE INTO detection_events VALUES (?,?,?,?,?,?,?,?)",
                    self._event_row(event)
                )

                # Resultados de la distancia (las posiciones pueden
                # reordenarse con cada llegada)
                for result in manager.results.get(distance_id, {}).values():
                    self._upsert_result(c, distance_id, result)

                if event.athlete:
                    key = (event.athlete.athlete_id, event.antenna_port)
                    ts = manager.last_detections.get(key)
                    if ts:
                        c.execute(
                            "INSERT OR REPLACE INTO last_detections VALUES (?,?,?)",
                            (key[0], key[1], _dt(ts))
                        )

                self._touch_meta(c)
            return True

        except Exception as e:
            logger.error(f"❌ Error persistiendo detección: {e}", exc_info=True)
            return False

    @staticmethod
    def _touch_meta(c):
        c.execute("INSERT OR REPLACE INTO meta VALUES ('saved_at', ?)",
                  (_dt(datetime.now()),))
        c.execute("INSERT OR REPLACE INTO meta VALUES ('version', ?)",
                  (str(STATE_VERSION),))

    @staticmethod
    def _upsert_distance(c, distance: RaceDistance):
        c.execute(
            "INSERT OR REPLACE INTO distances VALUES (?,?,?,?,?,?,?,?,?,?)",
            (distance.distance_id, distance.name, distance.distance_meters,
             distance.expected_checkpoints, distance.status.value,
             _dt(distance.start_time), _dt(distance.end_time), distance.notes,
             distance.race_mode.value, distance.duration_hours)
        )

    @staticmethod
    def _upsert_athlete(c, athlete: Athlete):
        c.execute(
            "INSERT OR REPLACE INTO athletes VALUES (?,?,?,?,?,?,?,?,?)",
            (athlete.athlete_id, athlete.distance_id, athlete.tag_id,
             athlete.bib_number, athlete.name, athlete.gender,
             _dt(athlete.birth_date), athlete.team, athlete.notes)
        )

    @staticmethod
    def _upsert_result(c, distance_id: str, result: AthleteResult):
        c.execute(
            "INSERT OR REPLACE INTO results VALUES (?,?,?,?,?,?,?,?,?)",
            (distance_id, result.athlete.athlete_id, result.status.value,
             _dt(result.start_time), _dt(result.finish_time),
             result.total_time.total_seconds() if result.total_time else None,
             json.dumps({str(cp): td.total_seconds()
                         for cp, td in result.splits.items()}),
             json.dumps({str(cp): _dt(ts)
                         for cp, ts in result.checkpoint_times.items()}),
             result.position)
        )

    @staticmethod
    def _upsert_award_category(c, ac: AwardCategory):
        c.execute(
            "INSERT OR REPLACE INTO award_categories VALUES (?,?,?,?,?,?,?,?)",
            (ac.award_category_id, ac.name, ac.gender, ac.min_age, ac.max_age,
             json.dumps(ac.distance_ids) if ac.distance_ids is not None else None,
             1 if ac.is_iaaf else 0, ac.description)
        )

    @staticmethod
    def _event_row(event: DetectionEvent):
        return (event.event_id, event.tag_id, _dt(event.timestamp),
                event.antenna_port, event.event_type.value,
                event.checkpoint_number,
                event.athlete.athlete_id if event.athlete else None,
                event.distance_id)

    # ========================================================================
    # LECTURA / RESUMEN
    # ========================================================================

    def has_saved_state(self) -> bool:
        """Verificar si existe estado guardado (en DB o JSON legado)"""
        if self._db_has_data():
            return True
        try:
            return (self.legacy_state_file.exists()
                    and self.legacy_state_file.stat().st_size > 2)
        except OSError:
            return False

    def load_state(self) -> Optional[dict]:
        """
        Leer el estado guardado como dict (desde la DB, o desde el
        snapshot JSON de la versión anterior si la DB está vacía).

        Returns:
            dict con el estado, o None si no existe o está corrupto
        """
        if self._db_has_data():
            try:
                return self._load_state_from_db()
            except Exception as e:
                logger.error(f"❌ Error leyendo base de datos: {e}", exc_info=True)
                return None

        if self.legacy_state_file.exists():
            try:
                with open(self.legacy_state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info("📂 Estado leído desde snapshot JSON legado")
                return state
            except Exception as e:
                logger.error(f"❌ Error leyendo snapshot JSON legado: {e}")

        return None

    def _load_state_from_db(self) -> dict:
        """Reconstruir el dict de estado desde las tablas SQLite"""
        with self._lock:
            c = self._conn

            meta = dict(c.execute("SELECT key, value FROM meta").fetchall())

            athletes_by_distance = {}
            for row in c.execute(
                    "SELECT athlete_id, distance_id, tag_id, bib_number, name,"
                    " gender, birth_date, team, notes FROM athletes"):
                athletes_by_distance.setdefault(row[1], []).append({
                    'athlete_id': row[0],
                    'distance_id': row[1],
                    'tag_id': row[2] or '',
                    'bib_number': row[3],
                    'name': row[4],
                    'gender': row[5],
                    'birth_date': row[6],
                    'team': row[7],
                    'notes': row[8],
                })

            distances = []
            for row in c.execute(
                    "SELECT distance_id, name, distance_meters, expected_checkpoints,"
                    " status, start_time, end_time, notes, race_mode, duration_hours"
                    " FROM distances"):
                distances.append({
                    'distance_id': row[0],
                    'name': row[1],
                    'distance_meters': row[2],
                    'expected_checkpoints': row[3],
                    'status': row[4],
                    'start_time': row[5],
                    'end_time': row[6],
                    'notes': row[7],
                    'race_mode': row[8],
                    'duration_hours': row[9],
                    'participants': athletes_by_distance.get(row[0], []),
                })

            results = {}
            for row in c.execute(
                    "SELECT distance_id, athlete_id, status, start_time, finish_time,"
                    " total_time, splits, checkpoint_times, position FROM results"):
                results.setdefault(row[0], {})[row[1]] = {
                    'athlete_id': row[1],
                    'distance_id': row[0],
                    'status': row[2],
                    'start_time': row[3],
                    'finish_time': row[4],
                    'total_time': row[5],
                    'splits': json.loads(row[6]) if row[6] else {},
                    'checkpoint_times': json.loads(row[7]) if row[7] else {},
                    'position': row[8],
                }

            award_categories = []
            for row in c.execute(
                    "SELECT award_category_id, name, gender, min_age, max_age,"
                    " distance_ids, is_iaaf, description FROM award_categories"):
                award_categories.append({
                    'award_category_id': row[0],
                    'name': row[1],
                    'gender': row[2],
                    'min_age': row[3],
                    'max_age': row[4],
                    'distance_ids': json.loads(row[5]) if row[5] else None,
                    'is_iaaf': bool(row[6]),
                    'description': row[7],
                })

            detection_history = []
            for row in c.execute(
                    "SELECT event_id, tag_id, timestamp, antenna_port, event_type,"
                    " checkpoint_number, athlete_id, distance_id FROM detection_events"
                    " ORDER BY timestamp"):
                detection_history.append({
                    'event_id': row[0],
                    'tag_id': row[1],
                    'timestamp': row[2],
                    'antenna_port': row[3],
                    'event_type': row[4],
                    'checkpoint_number': row[5],
                    'athlete_id': row[6],
                    'distance_id': row[7],
                })

            last_detections = [
                [row[0], row[1], row[2]]
                for row in c.execute(
                    "SELECT athlete_id, antenna_port, timestamp FROM last_detections")
            ]

            return {
                'version': int(meta.get('version', STATE_VERSION)),
                'saved_at': meta.get('saved_at'),
                'distances': distances,
                'results': results,
                'award_categories': award_categories,
                'detection_history': detection_history,
                'last_detections': last_detections,
            }

    def get_state_summary(self) -> Optional[dict]:
        """
        Resumen del estado guardado para mostrar al usuario antes de restaurar.

        Returns:
            dict con saved_at, distancias, atletas, en_carrera, finalizados
        """
        state = self.load_state()
        if not state:
            return None

        athletes = 0
        running = 0
        finished = 0
        distances_running = []

        for dist in state.get('distances', []):
            athletes += len(dist.get('participants', []))
            if dist.get('status') == RaceStatus.RUNNING.value:
                distances_running.append(dist.get('name', dist.get('distance_id')))

        for dist_results in state.get('results', {}).values():
            for res in dist_results.values():
                if res.get('status') == AthleteStatus.RUNNING.value:
                    running += 1
                elif res.get('status') == AthleteStatus.FINISHED.value:
                    finished += 1

        return {
            'saved_at': state.get('saved_at'),
            'distances': len(state.get('distances', [])),
            'distances_running': distances_running,
            'athletes': athletes,
            'running': running,
            'finished': finished,
        }

    # ========================================================================
    # ARCHIVO DE EVENTOS ANTERIORES
    # ========================================================================

    def archive(self) -> Optional[Path]:
        """
        Archivar el evento actual (al descartar una sesión anterior o
        empezar un evento nuevo). No borra nada: renombra la base con
        timestamp, dejando un archivo .db histórico por evento.
        """
        archived = None
        try:
            with self._lock:
                # Compactar WAL dentro del .db antes de archivarlo
                self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self._conn.commit()
                self._conn.close()
                self._conn = None

                if self.db_file.exists():
                    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archived = self.data_dir / f"race_event_backup_{stamp}.db"
                    os.replace(self.db_file, archived)
                    logger.info(f"📦 Evento archivado en {archived}")

                # Limpiar restos de WAL del archivo original
                for suffix in ('-wal', '-shm'):
                    leftover = Path(str(self.db_file) + suffix)
                    if leftover.exists():
                        leftover.unlink()

            self._open_db()

            # Archivar también el snapshot JSON legado si quedara
            self._archive_legacy_json()

            return archived

        except Exception as e:
            logger.error(f"❌ Error archivando evento: {e}", exc_info=True)
            if self._conn is None:
                self._open_db()
            return archived

    def _archive_legacy_json(self):
        """Renombrar el snapshot JSON de la versión anterior (ya migrado)"""
        try:
            if self.legacy_state_file.exists():
                stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup = self.data_dir / f"race_state_migrated_{stamp}.json"
                os.replace(self.legacy_state_file, backup)
                logger.info(f"📦 Snapshot JSON legado archivado en {backup}")
        except OSError as e:
            logger.warning(f"⚠️ No se pudo archivar JSON legado: {e}")

    # ========================================================================
    # JOURNAL DE DETECCIONES (append-only)
    # ========================================================================

    def log_detection(self, tag_id: str, timestamp: datetime,
                      antenna_port: int, roles: list) -> None:
        """
        Registrar una lectura cruda en el journal del día.

        Se escribe ANTES de procesar la detección, así queda registro
        incluso de lecturas rechazadas (anti-duplicados, etc.).
        """
        try:
            today = datetime.now().strftime('%Y%m%d')
            if self._journal_file is None or self._journal_date != today:
                if self._journal_file:
                    self._journal_file.close()
                journal_path = self.data_dir / f"detections_{today}.jsonl"
                self._journal_file = open(journal_path, 'a', encoding='utf-8')
                self._journal_date = today

            line = json.dumps({
                'tag_id': tag_id,
                'timestamp': _dt(timestamp),
                'antenna_port': antenna_port,
                'roles': roles,
            }, ensure_ascii=False)
            self._journal_file.write(line + "\n")
            self._journal_file.flush()
            os.fsync(self._journal_file.fileno())

        except Exception as e:
            logger.error(f"❌ Error escribiendo journal de detecciones: {e}")

    def close(self):
        """Cerrar base y journal (al salir de la aplicación)"""
        if self._journal_file:
            try:
                self._journal_file.close()
            except OSError:
                pass
            self._journal_file = None

        with self._lock:
            if self._conn:
                try:
                    self._conn.commit()
                    self._conn.close()
                except sqlite3.Error:
                    pass
                self._conn = None

    # ========================================================================
    # RESTAURACIÓN
    # ========================================================================

    def restore_into(self, manager) -> bool:
        """
        Restaurar el estado guardado dentro de un RaceManager.

        Reemplaza por completo distancias, resultados, categorías de
        premiación, historial y anti-duplicados del manager.

        Si el origen fue el snapshot JSON de la versión anterior, migra
        automáticamente los datos a la base SQLite.

        Returns:
            bool: True si se restauró correctamente
        """
        from_legacy = not self._db_has_data() and self.legacy_state_file.exists()

        state = self.load_state()
        if not state:
            return False

        try:
            athletes_by_id = {}

            # 1. Distancias y atletas
            distances = {}
            for dist_data in state.get('distances', []):
                distance = RaceDistance(
                    distance_id=dist_data['distance_id'],
                    name=dist_data['name'],
                    distance_meters=dist_data['distance_meters'],
                    expected_checkpoints=dist_data.get('expected_checkpoints', 0),
                    status=RaceStatus(dist_data['status']),
                    start_time=_parse_dt(dist_data.get('start_time')),
                    end_time=_parse_dt(dist_data.get('end_time')),
                    notes=dist_data.get('notes'),
                    race_mode=RaceMode(dist_data.get('race_mode', RaceMode.LINEAR.value)),
                    duration_hours=dist_data.get('duration_hours'),
                )
                for ath_data in dist_data.get('participants', []):
                    athlete = Athlete(
                        tag_id=ath_data.get('tag_id', ''),
                        bib_number=ath_data['bib_number'],
                        name=ath_data['name'],
                        distance_id=ath_data['distance_id'],
                        gender=ath_data.get('gender'),
                        birth_date=_parse_dt(ath_data.get('birth_date')),
                        team=ath_data.get('team'),
                        notes=ath_data.get('notes'),
                        athlete_id=ath_data['athlete_id'],
                    )
                    distance.participants.append(athlete)
                    athletes_by_id[athlete.athlete_id] = athlete
                distances[distance.distance_id] = distance

            # 2. Resultados
            results = {}
            for distance_id, dist_results in state.get('results', {}).items():
                results[distance_id] = {}
                for athlete_id, res_data in dist_results.items():
                    athlete = athletes_by_id.get(athlete_id)
                    if not athlete:
                        logger.warning(f"⚠️  Resultado sin atleta conocido: {athlete_id}, omitido")
                        continue
                    total_time = res_data.get('total_time')
                    result = AthleteResult(
                        athlete=athlete,
                        distance_id=distance_id,
                        status=AthleteStatus(res_data['status']),
                        start_time=_parse_dt(res_data.get('start_time')),
                        finish_time=_parse_dt(res_data.get('finish_time')),
                        total_time=timedelta(seconds=total_time) if total_time is not None else None,
                        splits={int(cp): timedelta(seconds=s) for cp, s in res_data.get('splits', {}).items()},
                        checkpoint_times={int(cp): _parse_dt(ts) for cp, ts in res_data.get('checkpoint_times', {}).items()},
                        position=res_data.get('position'),
                    )
                    results[distance_id][athlete_id] = result

            # 3. Categorías de premiación
            award_categories = {}
            for ac_data in state.get('award_categories', []):
                ac = AwardCategory(
                    award_category_id=ac_data['award_category_id'],
                    name=ac_data['name'],
                    gender=ac_data.get('gender'),
                    min_age=ac_data.get('min_age', 0),
                    max_age=ac_data.get('max_age'),
                    distance_ids=ac_data.get('distance_ids'),
                    is_iaaf=ac_data.get('is_iaaf', False),
                    description=ac_data.get('description'),
                )
                award_categories[ac.award_category_id] = ac

            # 4. Historial de detecciones
            detection_history = []
            for ev_data in state.get('detection_history', []):
                try:
                    event = DetectionEvent(
                        tag_id=ev_data['tag_id'],
                        timestamp=_parse_dt(ev_data['timestamp']),
                        antenna_port=ev_data['antenna_port'],
                        event_type=EventType(ev_data['event_type']),
                        checkpoint_number=ev_data.get('checkpoint_number'),
                        athlete=athletes_by_id.get(ev_data.get('athlete_id')),
                        distance_id=ev_data.get('distance_id'),
                        event_id=ev_data.get('event_id', ''),
                    )
                    detection_history.append(event)
                except (ValueError, KeyError) as e:
                    logger.warning(f"⚠️  Evento del historial omitido: {e}")

            # 5. Anti-duplicados
            last_detections = {}
            for athlete_id, port, ts in state.get('last_detections', []):
                last_detections[(athlete_id, int(port))] = _parse_dt(ts)

            # Aplicar todo al manager (atómico a nivel de objeto:
            # solo se reemplaza si toda la deserialización fue exitosa)
            manager.distances = distances
            manager.results = results
            if award_categories:
                manager.award_categories = award_categories
            manager.detection_history = detection_history
            manager.last_detections = last_detections

            total_athletes = sum(len(d.participants) for d in distances.values())
            logger.info("=" * 60)
            logger.info("♻️  ESTADO DE CARRERA RESTAURADO")
            logger.info(f"   Origen: {'JSON legado' if from_legacy else 'SQLite'}")
            logger.info(f"   Guardado: {state.get('saved_at')}")
            logger.info(f"   Distancias: {len(distances)}")
            logger.info(f"   Atletas: {total_athletes}")
            logger.info(f"   Detecciones en historial: {len(detection_history)}")
            logger.info("=" * 60)

            # Migración: sembrar la base SQLite y archivar el JSON
            if from_legacy:
                if self.save_state(manager):
                    self._archive_legacy_json()
                    logger.info("✅ Estado migrado de JSON a SQLite")

            return True

        except Exception as e:
            logger.error(f"❌ Error restaurando estado: {e}", exc_info=True)
            return False
