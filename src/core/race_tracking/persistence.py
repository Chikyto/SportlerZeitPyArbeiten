#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Persistencia local del estado de carrera
src/core/race_tracking/persistence.py

Protege el estado del RaceManager contra cortes de energía o cierres
inesperados de la aplicación:

1. Snapshot atómico: después de cada mutación (largada, detección, llegada,
   DNF, etc.) se serializa todo el estado a data/race_state.json. La escritura
   es atómica (archivo temporal + fsync + os.replace), por lo que un corte de
   luz en medio de la escritura nunca deja un archivo corrupto: queda la
   versión anterior completa.

2. Journal de detecciones: cada lectura cruda del lector se agrega a
   data/detections_YYYYMMDD.jsonl (append-only, con fsync). Aunque se pierda
   el snapshot, las lecturas crudas permiten reconstruir la carrera.

Al iniciar la aplicación, si existe un snapshot, se ofrece restaurarlo.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import (
    Athlete, RaceDistance, DetectionEvent, AthleteResult,
    AthleteStatus, RaceStatus, EventType, RaceMode, AwardCategory
)

logger = logging.getLogger(__name__)

STATE_VERSION = 1


def _dt(value: Optional[datetime]) -> Optional[str]:
    """datetime → ISO string (o None)"""
    return value.isoformat() if value else None


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """ISO string → datetime (o None)"""
    return datetime.fromisoformat(value) if value else None


class RaceStatePersistence:
    """
    Guarda y restaura el estado completo del RaceManager en disco.

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
        self.state_file = self.data_dir / "race_state.json"
        self._journal_file = None  # handle abierto del journal del día
        self._journal_date = None

    # ========================================================================
    # SNAPSHOT DEL ESTADO
    # ========================================================================

    def save_state(self, manager) -> bool:
        """
        Serializar todo el estado del RaceManager y escribirlo atómicamente.

        Returns:
            bool: True si se guardó correctamente
        """
        try:
            state = self._serialize(manager)
            tmp_path = self.state_file.with_suffix(".json.tmp")

            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            # Reemplazo atómico: o queda el archivo nuevo completo,
            # o queda el anterior. Nunca un archivo a medias.
            os.replace(tmp_path, self.state_file)
            return True

        except Exception as e:
            # Guardar nunca debe interrumpir el cronometraje
            logger.error(f"❌ Error guardando estado de carrera: {e}", exc_info=True)
            return False

    def has_saved_state(self) -> bool:
        """Verificar si existe un snapshot guardado con contenido"""
        try:
            return self.state_file.exists() and self.state_file.stat().st_size > 2
        except OSError:
            return False

    def load_state(self) -> Optional[dict]:
        """
        Leer el snapshot guardado.

        Returns:
            dict con el estado, o None si no existe o está corrupto
        """
        if not self.has_saved_state():
            return None
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Error leyendo estado guardado: {e}")
            return None

    def get_state_summary(self) -> Optional[dict]:
        """
        Resumen del snapshot para mostrar al usuario antes de restaurar.

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

    def archive(self) -> Optional[Path]:
        """
        Archivar el snapshot actual (al descartar una sesión anterior).
        No lo borra: lo renombra con timestamp por si hay que volver a él.
        """
        if not self.state_file.exists():
            return None
        try:
            backup = self.data_dir / f"race_state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.replace(self.state_file, backup)
            logger.info(f"📦 Estado anterior archivado en {backup}")
            return backup
        except OSError as e:
            logger.error(f"❌ Error archivando estado: {e}")
            return None

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
        """Cerrar el journal (al salir de la aplicación)"""
        if self._journal_file:
            try:
                self._journal_file.close()
            except OSError:
                pass
            self._journal_file = None

    # ========================================================================
    # SERIALIZACIÓN
    # ========================================================================

    def _serialize(self, manager) -> dict:
        return {
            'version': STATE_VERSION,
            'saved_at': _dt(datetime.now()),
            'distances': [self._serialize_distance(d) for d in manager.distances.values()],
            'results': {
                distance_id: {
                    athlete_id: self._serialize_result(result)
                    for athlete_id, result in dist_results.items()
                }
                for distance_id, dist_results in manager.results.items()
            },
            'award_categories': [
                self._serialize_award_category(ac)
                for ac in manager.award_categories.values()
            ],
            'detection_history': [
                self._serialize_event(e) for e in manager.detection_history
            ],
            'last_detections': [
                [athlete_id, port, _dt(ts)]
                for (athlete_id, port), ts in manager.last_detections.items()
            ],
        }

    @staticmethod
    def _serialize_athlete(athlete: Athlete) -> dict:
        return {
            'tag_id': athlete.tag_id,
            'bib_number': athlete.bib_number,
            'name': athlete.name,
            'distance_id': athlete.distance_id,
            'gender': athlete.gender,
            'birth_date': _dt(athlete.birth_date),
            'team': athlete.team,
            'notes': athlete.notes,
            'athlete_id': athlete.athlete_id,
        }

    def _serialize_distance(self, distance: RaceDistance) -> dict:
        return {
            'distance_id': distance.distance_id,
            'name': distance.name,
            'distance_meters': distance.distance_meters,
            'expected_checkpoints': distance.expected_checkpoints,
            'participants': [self._serialize_athlete(a) for a in distance.participants],
            'status': distance.status.value,
            'start_time': _dt(distance.start_time),
            'end_time': _dt(distance.end_time),
            'notes': distance.notes,
            'race_mode': distance.race_mode.value,
            'duration_hours': distance.duration_hours,
        }

    @staticmethod
    def _serialize_result(result: AthleteResult) -> dict:
        return {
            'athlete_id': result.athlete.athlete_id,
            'distance_id': result.distance_id,
            'status': result.status.value,
            'start_time': _dt(result.start_time),
            'finish_time': _dt(result.finish_time),
            'total_time': result.total_time.total_seconds() if result.total_time else None,
            'splits': {str(cp): td.total_seconds() for cp, td in result.splits.items()},
            'checkpoint_times': {str(cp): _dt(ts) for cp, ts in result.checkpoint_times.items()},
            'position': result.position,
        }

    @staticmethod
    def _serialize_award_category(ac: AwardCategory) -> dict:
        return {
            'award_category_id': ac.award_category_id,
            'name': ac.name,
            'gender': ac.gender,
            'min_age': ac.min_age,
            'max_age': ac.max_age,
            'distance_ids': ac.distance_ids,
            'is_iaaf': ac.is_iaaf,
            'description': ac.description,
        }

    @staticmethod
    def _serialize_event(event: DetectionEvent) -> dict:
        return {
            'event_id': event.event_id,
            'tag_id': event.tag_id,
            'timestamp': _dt(event.timestamp),
            'antenna_port': event.antenna_port,
            'event_type': event.event_type.value,
            'checkpoint_number': event.checkpoint_number,
            'athlete_id': event.athlete.athlete_id if event.athlete else None,
            'distance_id': event.distance_id,
        }

    # ========================================================================
    # RESTAURACIÓN
    # ========================================================================

    def restore_into(self, manager) -> bool:
        """
        Restaurar el estado guardado dentro de un RaceManager.

        Reemplaza por completo distancias, resultados, categorías de
        premiación, historial y anti-duplicados del manager.

        Returns:
            bool: True si se restauró correctamente
        """
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
            logger.info(f"   Guardado: {state.get('saved_at')}")
            logger.info(f"   Distancias: {len(distances)}")
            logger.info(f"   Atletas: {total_athletes}")
            logger.info(f"   Detecciones en historial: {len(detection_history)}")
            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"❌ Error restaurando estado: {e}", exc_info=True)
            return False
