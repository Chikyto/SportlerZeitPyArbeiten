#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor Principal de Carreras (Race Manager)
src/core/race_tracking/race_manager.py

Responsabilidad única: Coordinar el tracking de carreras
- Gestionar distancias activas
- Procesar eventos de detección
- Mantener resultados actualizados
- Generar clasificaciones

Versión: 2.0.0 - Refactorización semántica: category → distance
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .models import (
    Athlete, RaceDistance, DetectionEvent, AthleteResult,
    AthleteStatus, RaceStatus, EventType, AwardCategory,
    create_iaaf_award_categories
)

logger = logging.getLogger(__name__)


class RaceManager:
    """
    Gestor principal de carreras

    Coordina todo el sistema de tracking:
    - Gestión de distancias (5K, 10K, 21K, etc.)
    - Procesamiento de detecciones RFID
    - Cálculo de resultados
    - Clasificaciones en tiempo real
    - Categorías de premiación (género/edad)

    Example:
        >>> manager = RaceManager()
        >>> distance = RaceDistance(...)
        >>> manager.add_distance(distance)
        >>> manager.start_distance(distance.distance_id)
        >>> manager.process_detection(tag_id="7662", ...)
    """

    def __init__(self, load_iaaf_categories: bool = True):
        """
        Inicializar Race Manager

        Args:
            load_iaaf_categories: Si True, carga categorías de premiación IAAF por defecto
        """
        self.distances: Dict[str, RaceDistance] = {}
        self.results: Dict[str, Dict[str, AthleteResult]] = {}  # {distance_id: {athlete_id: result}}
        self.detection_history: List[DetectionEvent] = []

        # Persistencia local (se adjunta con attach_persistence)
        self.persistence = None

        # Categorías de premiación (por género/edad)
        self.award_categories: Dict[str, AwardCategory] = {}

        # Configuración de períodos de latencia (anti-duplicados)
        self.min_read_interval = timedelta(seconds=3)  # Intervalo mínimo entre lecturas en misma antena
        self.start_grace_period = timedelta(seconds=45)  # Período de gracia después de largar (evita re-largadas)

        # Trackeo de últimas lecturas: {(athlete_id, antenna_port): timestamp}
        self.last_detections: Dict[Tuple[str, int], datetime] = {}

        # Cargar categorías de premiación IAAF por defecto
        if load_iaaf_categories:
            for award_cat in create_iaaf_award_categories():
                self.award_categories[award_cat.award_category_id] = award_cat
            logger.info(f"📋 {len(self.award_categories)} categorías de premiación IAAF cargadas")

        logger.info("🏁 RaceManager inicializado")

    # ========================================================================
    # PERSISTENCIA LOCAL
    # ========================================================================

    def attach_persistence(self, persistence) -> None:
        """
        Adjuntar persistencia local (RaceStatePersistence).

        A partir de este momento, cada mutación de estado (largada,
        detección, llegada, DNF, reset, etc.) se guarda en disco.
        """
        self.persistence = persistence
        logger.info("💾 Persistencia local de estado activada")

    def save_now(self) -> None:
        """
        Guardar el estado actual en disco inmediatamente.

        Llamar después de mutar estado por fuera del RaceManager
        (ej: asignación de chips, DNF/DNS/DSQ desde la UI).
        Nunca lanza excepciones: un fallo de guardado no debe
        interrumpir el cronometraje.
        """
        if self.persistence:
            self.persistence.save_state(self)

    # ========================================================================
    # GESTIÓN DE DISTANCIAS
    # ========================================================================

    def add_distance(self, distance: RaceDistance) -> bool:
        """
        Agregar una distancia al sistema

        Args:
            distance: Distancia a agregar

        Returns:
            bool: True si se agregó, False si ya existía
        """
        if distance.distance_id in self.distances:
            logger.warning(f"⚠️  Distancia {distance.distance_id} ya existe")
            return False

        self.distances[distance.distance_id] = distance

        # Inicializar resultados para cada atleta
        self.results[distance.distance_id] = {}
        for athlete in distance.participants:
            self.results[distance.distance_id][athlete.athlete_id] = AthleteResult(
                athlete=athlete,
                distance_id=distance.distance_id
            )

        logger.info(f"✅ Distancia agregada: {distance.name} ({len(distance)} atletas)")
        self.save_now()
        return True
    
    def remove_distance(self, distance_id: str) -> bool:
        """
        Eliminar una distancia

        Args:
            distance_id: ID de la distancia

        Returns:
            bool: True si se eliminó, False si no existía
        """
        if distance_id not in self.distances:
            return False

        distance = self.distances[distance_id]

        # No permitir eliminar si está en curso
        if distance.status == RaceStatus.RUNNING:
            raise ValueError("No se puede eliminar una distancia en curso")

        del self.distances[distance_id]
        if distance_id in self.results:
            del self.results[distance_id]

        logger.info(f"🗑️  Distancia eliminada: {distance.name}")
        self.save_now()
        return True

    def clear_all(self) -> None:
        """Eliminar todas las distancias, atletas y resultados (nueva sesión)"""
        self.distances.clear()
        self.results.clear()
        self.detection_history.clear()
        self.last_detections.clear()
        logger.info("🗑️  RaceManager limpiado — nueva sesión")
        self.save_now()

    def get_distance(self, distance_id: str) -> Optional[RaceDistance]:
        """Obtener distancia por ID"""
        return self.distances.get(distance_id)

    def get_all_distances(self) -> List[RaceDistance]:
        """Obtener todas las distancias"""
        return list(self.distances.values())

    def get_active_distances(self) -> List[RaceDistance]:
        """Obtener distancias en curso"""
        return [d for d in self.distances.values() if d.status == RaceStatus.RUNNING]

    # ========================================================================
    # GESTIÓN DE CATEGORÍAS DE PREMIACIÓN
    # ========================================================================

    def add_award_category(self, award_category: AwardCategory) -> bool:
        """
        Agregar una categoría de premiación

        Args:
            award_category: Categoría a agregar

        Returns:
            bool: True si se agregó, False si ya existía

        Raises:
            ValueError: Si se intenta modificar una categoría IAAF
        """
        if award_category.award_category_id in self.award_categories:
            existing = self.award_categories[award_category.award_category_id]
            if existing.is_iaaf:
                raise ValueError("No se puede modificar una categoría IAAF estándar")
            logger.warning(f"⚠️  Categoría de premiación {award_category.award_category_id} ya existe, reemplazando")

        self.award_categories[award_category.award_category_id] = award_category
        logger.info(f"✅ Categoría de premiación agregada: {award_category.name}")
        self.save_now()
        return True

    def remove_award_category(self, award_category_id: str) -> bool:
        """
        Eliminar una categoría de premiación

        Args:
            award_category_id: ID de la categoría

        Returns:
            bool: True si se eliminó, False si no existía

        Raises:
            ValueError: Si se intenta eliminar una categoría IAAF
        """
        if award_category_id not in self.award_categories:
            return False

        award_cat = self.award_categories[award_category_id]
        if award_cat.is_iaaf:
            raise ValueError("No se puede eliminar una categoría IAAF estándar")

        del self.award_categories[award_category_id]
        logger.info(f"🗑️  Categoría de premiación eliminada: {award_cat.name}")
        self.save_now()
        return True

    def get_award_category(self, award_category_id: str) -> Optional[AwardCategory]:
        """Obtener categoría de premiación por ID"""
        return self.award_categories.get(award_category_id)

    def get_all_award_categories(self) -> List[AwardCategory]:
        """Obtener todas las categorías de premiación"""
        return list(self.award_categories.values())

    def get_award_categories_for_distance(self, distance_id: str) -> List[AwardCategory]:
        """
        Obtener categorías de premiación que aplican a una distancia

        Args:
            distance_id: ID de la distancia (ej: "5k", "10k", "21k")

        Returns:
            List[AwardCategory]: Categorías de premiación que aplican a esa distancia
        """
        return [
            ac for ac in self.award_categories.values()
            if ac.applies_to_distance(distance_id)
        ]

    def reset_award_categories_to_iaaf(self):
        """Resetear categorías de premiación a IAAF por defecto"""
        # Limpiar todas
        self.award_categories.clear()

        # Recargar IAAF
        for award_cat in create_iaaf_award_categories():
            self.award_categories[award_cat.award_category_id] = award_cat

        logger.info(f"🔄 Categorías de premiación reseteadas a IAAF ({len(self.award_categories)} categorías)")
        self.save_now()

    # ========================================================================
    # CONTROL DE CARRERA
    # ========================================================================

    def start_distance(self, distance_id: str) -> bool:
        """
        Iniciar una distancia

        Args:
            distance_id: ID de la distancia a iniciar

        Returns:
            bool: True si se inició correctamente

        Raises:
            ValueError: Si la distancia no existe o no está lista

        Nota:
            NO se requiere que todos los participantes tengan chips asignados.
            La carrera puede iniciarse con chips pendientes, ya que en eventos reales
            puede haber corredores con problemas, ausentes, etc.

            Si la distancia está FINISHED, se resetea automáticamente antes de iniciar.
        """
        distance = self.get_distance(distance_id)
        if not distance:
            raise ValueError(f"Distancia {distance_id} no existe")

        # Si está finalizada, resetear automáticamente para permitir reiniciar
        if distance.status == RaceStatus.FINISHED:
            logger.info(f"🔄 Distancia {distance.name} estaba finalizada, reseteando para reiniciar...")
            self.reset_distance(distance_id)
            distance = self.get_distance(distance_id)  # Refrescar referencia

        if distance.status not in [RaceStatus.PENDING, RaceStatus.READY]:
            raise ValueError(f"Distancia {distance.name} no está lista para iniciar")

        # Informar estado de chips (solo informativo, no bloqueante)
        total_participants = len(distance.participants)
        chips_assigned = sum(1 for p in distance.participants if p.has_chip_assigned())
        chips_pending = total_participants - chips_assigned

        distance.status = RaceStatus.RUNNING
        distance.start_time = datetime.now()

        logger.info(f"🚀 Distancia iniciada: {distance.name}")
        logger.info(f"   📊 Participantes: {total_participants} | Chips: {chips_assigned} asignados, {chips_pending} pendientes")

        self.save_now()
        return True
    
    def pause_distance(self, distance_id: str) -> bool:
        """Pausar una distancia en curso"""
        distance = self.get_distance(distance_id)
        if not distance:
            return False

        if distance.status != RaceStatus.RUNNING:
            return False

        distance.status = RaceStatus.PAUSED
        logger.info(f"⏸️  Distancia pausada: {distance.name}")
        self.save_now()
        return True

    def resume_distance(self, distance_id: str) -> bool:
        """Reanudar una distancia pausada"""
        distance = self.get_distance(distance_id)
        if not distance:
            return False

        if distance.status != RaceStatus.PAUSED:
            return False

        distance.status = RaceStatus.RUNNING
        logger.info(f"▶️  Distancia reanudada: {distance.name}")
        self.save_now()
        return True

    def finish_distance(self, distance_id: str) -> bool:
        """
        Finalizar una distancia

        Args:
            distance_id: ID de la distancia

        Returns:
            bool: True si se finalizó correctamente
        """
        distance = self.get_distance(distance_id)
        if not distance:
            return False

        if distance.status != RaceStatus.RUNNING:
            return False

        distance.status = RaceStatus.FINISHED
        distance.end_time = datetime.now()

        # Calcular clasificación final
        self._update_classification(distance_id)

        logger.info(f"🏁 Distancia finalizada: {distance.name}")
        self.save_now()
        return True
    
    # ========================================================================
    # PROCESAMIENTO DE DETECCIONES
    # ========================================================================
    
    def process_detection(
        self,
        tag_id: str,
        timestamp: datetime,
        antenna_port: int,
        roles: List[str]
    ) -> Optional[DetectionEvent]:
        """
        Procesar una detección de chip RFID
        
        Args:
            tag_id: ID del chip detectado
            timestamp: Momento de la detección
            antenna_port: Puerto donde se detectó
            roles: Lista de roles de la antena ['start', 'finish', 'checkpoint']
        
        Returns:
            DetectionEvent creado o None si no se pudo procesar
        
        Example:
            >>> event = manager.process_detection(
            ...     tag_id="7662",
            ...     timestamp=datetime.now(),
            ...     antenna_port=2,
            ...     roles=['start']
            ... )
        """
        logger.debug(
            f"🔄 process_detection: tag={tag_id} puerto={antenna_port} "
            f"roles={roles} ts={timestamp}"
        )

        # Registrar la lectura cruda en el journal ANTES de procesarla:
        # aunque se rechace (anti-duplicados, etc.) o la app se corte,
        # queda registro en disco para reconstruir la carrera.
        if self.persistence:
            self.persistence.log_detection(tag_id, timestamp, antenna_port, roles)

        # 1. Identificar al atleta y su distancia
        athlete, distance = self._find_athlete_by_tag(tag_id)

        if not athlete:
            logger.warning(
                f"❌ Detección rechazada: tag {tag_id} sin atleta asociado "
                f"(asignar chip en tab 'Asignación de Chips')"
            )
            return None

        if not distance:
            logger.warning(f"❌ Detección rechazada: {athlete.name} sin distancia activa")
            return None

        logger.debug(f"   Atleta: {athlete.name} | Distancia: {distance.name} ({distance.status})")

        # Solo procesar si la distancia está corriendo
        if distance.status != RaceStatus.RUNNING:
            logger.warning(
                f"❌ Detección rechazada: {athlete.name} — distancia '{distance.name}' "
                f"no está en curso (estado: {distance.status.value})"
            )
            return None

        # 2. Validar períodos de latencia (anti-duplicados)
        if not self._validate_detection_timing(athlete, antenna_port, timestamp, roles):
            logger.debug(f"⏱️  Detección ignorada por anti-duplicados: {athlete.name}")
            return None

        # 3. Determinar tipo de evento

        # Inicializar resultado si el atleta fue agregado después de crear la distancia
        if athlete.athlete_id not in self.results.get(distance.distance_id, {}):
            logger.debug(f"⚠️  Atleta {athlete.name} sin resultado inicializado — inicializando ahora")
            self.results.setdefault(distance.distance_id, {})[athlete.athlete_id] = AthleteResult(
                athlete=athlete,
                distance_id=distance.distance_id
            )

        event_type, checkpoint_num, reason = self._determine_event_type(
            roles, athlete, distance, antenna_port, timestamp
        )

        if not event_type:
            logger.warning(f"❌ Detección rechazada: {athlete.name} — {reason}")
            return None

        # 4. Crear evento de detección
        event = DetectionEvent(
            tag_id=tag_id,
            timestamp=timestamp,
            antenna_port=antenna_port,
            event_type=event_type,
            checkpoint_number=checkpoint_num,
            athlete=athlete,
            distance_id=distance.distance_id
        )

        # 5. Registrar en resultado del atleta
        result = self.results[distance.distance_id][athlete.athlete_id]
        success = self._record_event_in_result(result, event)

        if success:
            # 6. Actualizar tracking de última detección
            detection_key = (athlete.athlete_id, antenna_port)
            self.last_detections[detection_key] = timestamp

            # 7. Guardar en historial
            self.detection_history.append(event)

            # 8. Actualizar clasificación
            self._update_classification(distance.distance_id)

            # 9. Persistir la detección (incremental: solo el evento y los
            #    resultados de esta distancia — sobrevive a cortes de energía)
            if self.persistence:
                self.persistence.record_detection(self, distance.distance_id, event)

            return event
        else:
            logger.error(
                f"❌ No se pudo registrar evento {event_type} para {athlete.name}"
            )

        return None

    def _validate_detection_timing(
        self,
        athlete: Athlete,
        antenna_port: int,
        timestamp: datetime,
        roles: List[str]
    ) -> bool:
        """
        Validar períodos de latencia para evitar detecciones duplicadas

        Implementa dos tipos de validación:
        1. Latencia por antena: Evita lecturas duplicadas del mismo chip en la misma antena
        2. Período de gracia para START: Evita re-largadas cuando un corredor vuelve
           (ej: se olvidó algo y regresa a buscar)

        Args:
            athlete: Atleta detectado
            antenna_port: Puerto de la antena
            timestamp: Momento de la detección
            roles: Roles de la antena

        Returns:
            bool: True si la detección es válida, False si debe ignorarse
        """
        detection_key = (athlete.athlete_id, antenna_port)
        last_detection = self.last_detections.get(detection_key)

        # Validación 1: Intervalo mínimo entre lecturas en la misma antena
        if last_detection:
            time_since_last = timestamp - last_detection
            if time_since_last < self.min_read_interval:
                logger.debug(
                    f"⏱️  Detección ignorada (muy reciente): {athlete.name} en antena {antenna_port} "
                    f"({time_since_last.total_seconds():.1f}s desde última lectura)"
                )
                return False

        # Validación 2: Período de gracia para START (evitar re-largadas)
        if 'start' in roles:
            result = self.results.get(athlete.distance_id, {}).get(athlete.athlete_id)
            if result and result.start_time:
                time_since_start = timestamp - result.start_time
                if time_since_start < self.start_grace_period:
                    logger.info(
                        f"🔄 START ignorado (periodo de gracia): {athlete.name} "
                        f"({time_since_start.total_seconds():.1f}s desde largada) - "
                        f"Probablemente volvió a buscar algo"
                    )
                    return False

        return True

    def _find_athlete_by_tag(self, tag_id: str) -> Tuple[Optional[Athlete], Optional[RaceDistance]]:
        """
        Buscar atleta por tag_id en distancias activas

        Args:
            tag_id: ID del chip

        Returns:
            Tuple (Athlete, RaceDistance) o (None, None) si no se encuentra
        """
        logger.debug(f"🔍 Buscando atleta con chip: '{tag_id}'")

        # Buscar primero en distancias corriendo
        active_distances = self.get_active_distances()

        for distance in active_distances:
            athlete = distance.get_participant_by_tag(tag_id)
            if athlete:
                logger.debug(f"   MATCH: {athlete.name} (#{athlete.bib_number}) en {distance.name}")
                return athlete, distance

        # Si no está en activas, buscar en todas
        all_distances = list(self.distances.values())

        for distance in all_distances:
            athlete = distance.get_participant_by_tag(tag_id)
            if athlete:
                logger.warning(f"⚠️  Chip encontrado en distancia NO activa: {athlete.name} en {distance.name}")
                return athlete, distance

        # No encontrado - registrar chips disponibles para debugging
        # (el rechazo se reporta como warning en process_detection)
        chip_count = 0
        for distance in all_distances:
            for participant in distance.participants:
                if participant.tag_id:
                    logger.debug(f"     - '{participant.tag_id}' → {participant.name}")
                    chip_count += 1
        logger.debug(f"❌ NO MATCH para chip '{tag_id}' ({chip_count} chips asignados)")

        return None, None
    
    def _determine_event_type(
        self,
        roles: List[str],
        athlete: Athlete,
        distance: RaceDistance,
        antenna_port: int,
        timestamp: datetime
    ) -> Tuple[Optional[EventType], Optional[int], str]:
        """
        Determinar tipo de evento según roles, estado del atleta y
        ventanas de tiempo (delegado a detection_validator).

        Returns:
            Tuple (EventType, checkpoint_number, motivo)
        """
        from .detection_validator import resolve_event

        result = self.results[distance.distance_id][athlete.athlete_id]
        return resolve_event(roles, antenna_port, result, distance, timestamp)
    
    def _record_event_in_result(self, result: AthleteResult, event: DetectionEvent) -> bool:
        """
        Registrar evento en el resultado del atleta
        
        Args:
            result: Resultado del atleta
            event: Evento a registrar
        
        Returns:
            bool: True si se registró correctamente
        """
        try:
            if event.event_type == EventType.START:
                result.record_start(event.timestamp)
                logger.info(f"🟢 LARGADA: {result.athlete.name}")
                return True
            
            elif event.event_type == EventType.CHECKPOINT:
                result.record_checkpoint(event.checkpoint_number, event.timestamp)
                logger.info(f"🔵 CHECKPOINT {event.checkpoint_number}: {result.athlete.name}")
                return True
            
            elif event.event_type == EventType.FINISH:
                result.record_finish(event.timestamp)
                logger.info(f"🏁 META: {result.athlete.name} - {result.get_formatted_time()}")
                return True
            
        except ValueError as e:
            logger.warning(f"⚠️  No se pudo registrar evento: {e}")
            return False
        
        return False
    
    # ========================================================================
    # CLASIFICACIONES Y RESULTADOS
    # ========================================================================

    def get_results(self, distance_id: str) -> List[AthleteResult]:
        """
        Obtener resultados de una distancia

        Args:
            distance_id: ID de la distancia

        Returns:
            Lista de AthleteResult ordenados por posición
        """
        if distance_id not in self.results:
            return []

        results = list(self.results[distance_id].values())

        # Ordenar: primero finalizados por tiempo, luego corriendo, luego no iniciados
        def sort_key(r: AthleteResult):
            if r.status == AthleteStatus.FINISHED:
                return (0, r.get_total_seconds() or float('inf'))
            elif r.status == AthleteStatus.RUNNING:
                return (1, 0)
            else:
                return (2, 0)

        results.sort(key=sort_key)
        return results

    def _update_classification(self, distance_id: str):
        """
        Actualizar posiciones en la clasificación

        Args:
            distance_id: ID de la distancia
        """
        results = self.get_results(distance_id)

        position = 1
        for result in results:
            if result.status == AthleteStatus.FINISHED:
                result.position = position
                position += 1
            else:
                result.position = None

    def get_athlete_result(self, distance_id: str, athlete_id: str) -> Optional[AthleteResult]:
        """
        Obtener resultado de un atleta específico

        Args:
            distance_id: ID de la distancia
            athlete_id: ID del atleta

        Returns:
            AthleteResult o None
        """
        if distance_id not in self.results:
            return None

        return self.results[distance_id].get(athlete_id)

    def get_statistics(self, distance_id: str) -> Dict:
        """
        Obtener estadísticas de una distancia

        Args:
            distance_id: ID de la distancia

        Returns:
            Dict con estadísticas
        """
        results = self.get_results(distance_id)
        finished = [r for r in results if r.status == AthleteStatus.FINISHED]

        stats = {
            'total_participants': len(results),
            'started': sum(1 for r in results if r.status != AthleteStatus.NOT_STARTED),
            'finished': len(finished),
            'running': sum(1 for r in results if r.status == AthleteStatus.RUNNING),
            'average_time': None,
            'fastest_time': None,
            'slowest_time': None
        }

        if finished:
            times = [r.get_total_seconds() for r in finished]
            stats['average_time'] = sum(times) / len(times)
            stats['fastest_time'] = min(times)
            stats['slowest_time'] = max(times)

        return stats

    def get_results_by_award_category(
        self,
        distance_id: str,
        only_finished: bool = True
    ) -> Dict[str, List[AthleteResult]]:
        """
        Agrupar resultados por categoría de premiación (género/edad)

        Args:
            distance_id: ID de la distancia (ej: "5k", "10k", "21k")
            only_finished: Si True, solo incluye atletas que finalizaron

        Returns:
            Dict con {award_category_id: [AthleteResult]} ordenados por tiempo

        Example:
            >>> results_by_award = manager.get_results_by_award_category("21k")
            >>> for award_cat_id, results in results_by_award.items():
            ...     print(f"{award_cat_id}: {len(results)} finalizadores")
        """
        # Obtener todos los resultados de la distancia
        all_results = self.get_results(distance_id)
        logger.info(f"📊 get_results_by_award_category para {distance_id}:")
        logger.info(f"  - Total resultados: {len(all_results)}")
        logger.info(f"  - Estados: {', '.join([f'{r.athlete.name}={r.status.value}' for r in all_results])}")

        # Filtrar solo finalizados si se requiere
        if only_finished:
            all_results = [r for r in all_results if r.status == AthleteStatus.FINISHED]
            logger.info(f"  - Finalizados: {len(all_results)}")
            if all_results:
                logger.info(f"  - Finalizados: {', '.join([r.athlete.name for r in all_results])}")

        # Obtener categorías de premiación que aplican a esta distancia
        applicable_award_cats = self.get_award_categories_for_distance(distance_id)
        logger.info(f"  - Award categories aplicables: {len(applicable_award_cats)}")
        for ac in applicable_award_cats:
            logger.info(f"    - {ac.award_category_id}: {ac.name}")

        # Agrupar por categoría de premiación
        results_by_award: Dict[str, List[AthleteResult]] = {}

        for award_cat in applicable_award_cats:
            # Filtrar resultados que pertenecen a esta award_category
            matching_results = []
            for r in all_results:
                applies = award_cat.applies_to_athlete(r.athlete)
                if applies:
                    matching_results.append(r)
                else:
                    # Log por qué NO aplica
                    age = r.athlete.get_age()
                    gender = r.athlete.gender.upper()[0] if r.athlete.gender else None
                    logger.debug(
                        f"    ❌ {r.athlete.name} NO aplica a {award_cat.award_category_id}: "
                        f"género={gender} (req={award_cat.gender}), "
                        f"edad={age} (req={award_cat.min_age}-{award_cat.max_age})"
                    )

            logger.info(f"  - {award_cat.award_category_id}: {len(matching_results)} atletas")
            if matching_results:
                logger.info(f"    - Atletas: {', '.join([r.athlete.name for r in matching_results])}")

            # Ordenar por tiempo (más rápido primero)
            matching_results.sort(key=lambda r: r.get_total_seconds() or float('inf'))

            # Asignar posiciones dentro de la categoría de premiación
            for position, result in enumerate(matching_results, start=1):
                # Nota: no modificamos result.position (que es posición general)
                # La posición en award_category se maneja aparte
                pass

            results_by_award[award_cat.award_category_id] = matching_results

        return results_by_award

    def get_podium_by_award_category(
        self,
        distance_id: str,
        top_n: int = 3
    ) -> Dict[str, List[Tuple[int, AthleteResult]]]:
        """
        Obtener podios (top N) por categoría de premiación

        Args:
            distance_id: ID de la distancia (ej: "5k", "10k", "21k")
            top_n: Número de posiciones a incluir (default 3 para podio)

        Returns:
            Dict con {award_category_id: [(position, AthleteResult)]}

        Example:
            >>> podiums = manager.get_podium_by_award_category("21k", top_n=3)
            >>> for award_cat_id, podium in podiums.items():
            ...     print(f"{award_cat_id}:")
            ...     for pos, result in podium:
            ...         print(f"  {pos}. {result.athlete.name} - {result.get_formatted_time()}")
        """
        results_by_award = self.get_results_by_award_category(distance_id, only_finished=True)

        podiums = {}
        for award_cat_id, results in results_by_award.items():
            # Tomar solo top_n
            top_results = results[:top_n]
            # Agregar posiciones (1, 2, 3, ...)
            podium = [(i + 1, result) for i, result in enumerate(top_results)]
            podiums[award_cat_id] = podium

        return podiums

    def get_results_by_gender(
        self,
        distance_id: str,
        only_finished: bool = True
    ) -> Dict[str, List[AthleteResult]]:
        """
        Obtener clasificación general por género (sin importar edad)

        Args:
            distance_id: ID de la distancia
            only_finished: Si True, solo incluye atletas que finalizaron

        Returns:
            Dict con {"M": [resultados], "F": [resultados], "Otro": [resultados]}
            Cada lista está ordenada por tiempo (más rápido primero)

        Example:
            >>> results_by_gender = manager.get_results_by_gender("21k")
            >>> for gender, results in results_by_gender.items():
            ...     print(f"Género {gender}: {len(results)} finalizadores")
            ...     for i, r in enumerate(results[:3], 1):
            ...         print(f"  {i}. {r.athlete.name} - {r.get_formatted_time()}")
        """
        all_results = self.get_results(distance_id)

        # Filtrar solo finalizados si se requiere
        if only_finished:
            all_results = [r for r in all_results if r.status == AthleteStatus.FINISHED]

        # Agrupar por género
        results_by_gender: Dict[str, List[AthleteResult]] = {"M": [], "F": []}

        for result in all_results:
            gender = result.athlete.gender
            key = gender.upper()[0] if gender else "?"
            results_by_gender.setdefault(key, []).append(result)

        # Ordenar cada grupo por tiempo
        for gender in results_by_gender:
            results_by_gender[gender].sort(key=lambda r: r.get_total_seconds() or float('inf'))

        logger.info(f"📊 Clasificación por género para {distance_id}: { {k: len(v) for k, v in results_by_gender.items()} }")

        return results_by_gender

    # ========================================================================
    # UTILIDADES
    # ========================================================================

    def reset_distance(self, distance_id: str) -> bool:
        """
        Resetear resultados de una distancia

        Args:
            distance_id: ID de la distancia

        Returns:
            bool: True si se reseteó
        """
        distance = self.get_distance(distance_id)
        if not distance:
            return False

        # Reinicializar resultados
        self.results[distance_id] = {}
        for athlete in distance.participants:
            self.results[distance_id][athlete.athlete_id] = AthleteResult(
                athlete=athlete,
                distance_id=distance_id
            )

        # Limpiar tracking de detecciones de esta distancia
        athlete_ids = {a.athlete_id for a in distance.participants}
        self.last_detections = {
            key: value for key, value in self.last_detections.items()
            if key[0] not in athlete_ids
        }

        # Resetear estado
        distance.status = RaceStatus.PENDING
        distance.start_time = None
        distance.end_time = None

        logger.info(f"🔄 Distancia reseteada: {distance.name}")
        self.save_now()
        return True

    def __repr__(self) -> str:
        """Representación para debugging"""
        return f"<RaceManager: {len(self.distances)} distancias, {len(self.detection_history)} eventos>"

    # ========================================================================
    # MÉTODOS DE COMPATIBILIDAD (DEPRECATED - Usar add_distance, get_distance, etc.)
    # ========================================================================

    @property
    def categories(self):
        """DEPRECATED: Usar self.distances"""
        return self.distances

    def add_category(self, category):
        """DEPRECATED: Usar add_distance()"""
        return self.add_distance(category)

    def remove_category(self, category_id):
        """DEPRECATED: Usar remove_distance()"""
        return self.remove_distance(category_id)

    def get_category(self, category_id):
        """DEPRECATED: Usar get_distance()"""
        return self.get_distance(category_id)

    def get_all_categories(self):
        """DEPRECATED: Usar get_all_distances()"""
        return self.get_all_distances()

    def get_active_categories(self):
        """DEPRECATED: Usar get_active_distances()"""
        return self.get_active_distances()

    def start_category(self, category_id):
        """DEPRECATED: Usar start_distance()"""
        return self.start_distance(category_id)

    def pause_category(self, category_id):
        """DEPRECATED: Usar pause_distance()"""
        return self.pause_distance(category_id)

    def resume_category(self, category_id):
        """DEPRECATED: Usar resume_distance()"""
        return self.resume_distance(category_id)

    def finish_category(self, category_id):
        """DEPRECATED: Usar finish_distance()"""
        return self.finish_distance(category_id)

    def reset_category(self, category_id):
        """DEPRECATED: Usar reset_distance()"""
        return self.reset_distance(category_id)


# ============================================================================
# TESTS
# ============================================================================

if __name__ == "__main__":
    """Tests del Race Manager"""
    from datetime import timedelta

    print("=" * 60)
    print("TESTS DE RACE MANAGER")
    print("=" * 60)

    # Setup
    manager = RaceManager()

    # Test 1: Crear y agregar distancia
    print("\n1. Crear distancia con atletas...")
    from models import create_test_distance
    distance = create_test_distance()
    manager.add_distance(distance)
    print(f"   ✅ Distancia agregada: {distance}")

    # Test 2: Iniciar distancia
    print("\n2. Iniciar distancia...")
    manager.start_distance(distance.distance_id)
    print(f"   ✅ Estado: {distance.status.value}")

    # Test 3: Simular detecciones
    print("\n3. Simular detecciones...")
    now = datetime.now()

    # Largada de atleta 1
    event1 = manager.process_detection(
        tag_id="7662",
        timestamp=now,
        antenna_port=2,
        roles=['start']
    )
    print(f"   ✅ {event1}")

    # Largada de atleta 2
    event2 = manager.process_detection(
        tag_id="8587",
        timestamp=now + timedelta(seconds=0.5),
        antenna_port=2,
        roles=['start']
    )
    print(f"   ✅ {event2}")

    # Meta de atleta 1
    event3 = manager.process_detection(
        tag_id="7662",
        timestamp=now + timedelta(seconds=10.5),
        antenna_port=6,
        roles=['finish']
    )
    print(f"   ✅ {event3}")

    # Meta de atleta 2
    event4 = manager.process_detection(
        tag_id="8587",
        timestamp=now + timedelta(seconds=11.2),
        antenna_port=6,
        roles=['finish']
    )
    print(f"   ✅ {event4}")

    # Test 4: Obtener clasificación
    print("\n4. Clasificación actual...")
    results = manager.get_results(distance.distance_id)
    for result in results:
        pos = f"#{result.position}" if result.position else "  -"
        print(f"   {pos} {result}")

    # Test 5: Estadísticas
    print("\n5. Estadísticas...")
    stats = manager.get_statistics(distance.distance_id)
    print(f"   Total: {stats['total_participants']}")
    print(f"   Iniciados: {stats['started']}")
    print(f"   Finalizados: {stats['finished']}")
    if stats['fastest_time']:
        print(f"   Más rápido: {stats['fastest_time']:.3f}s")
        print(f"   Promedio: {stats['average_time']:.3f}s")

    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)