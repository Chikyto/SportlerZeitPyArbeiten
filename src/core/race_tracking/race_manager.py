#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor Principal de Carreras (Race Manager)
src/core/race_tracking/race_manager.py

Responsabilidad única: Coordinar el tracking de carreras
- Gestionar categorías activas
- Procesar eventos de detección
- Mantener resultados actualizados
- Generar clasificaciones

Versión: 1.2.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .models import Athlete, RaceCategory, DetectionEvent, AthleteResult, AthleteStatus, RaceStatus, EventType

logger = logging.getLogger(__name__)


class RaceManager:
    """
    Gestor principal de carreras
    
    Coordina todo el sistema de tracking:
    - Gestión de categorías
    - Procesamiento de detecciones
    - Cálculo de resultados
    - Clasificaciones en tiempo real
    
    Example:
        >>> manager = RaceManager()
        >>> category = RaceCategory(...)
        >>> manager.add_category(category)
        >>> manager.start_category(category.category_id)
        >>> manager.process_detection(tag_id="7662", ...)
    """
    
    def __init__(self):
        """Inicializar Race Manager"""
        self.categories: Dict[str, RaceCategory] = {}
        self.results: Dict[str, Dict[str, AthleteResult]] = {}  # {category_id: {athlete_id: result}}
        self.detection_history: List[DetectionEvent] = []

        # Configuración de períodos de latencia (anti-duplicados)
        self.min_read_interval = timedelta(seconds=3)  # Intervalo mínimo entre lecturas en misma antena
        self.start_grace_period = timedelta(seconds=45)  # Período de gracia después de largar (evita re-largadas)

        # Trackeo de últimas lecturas: {(athlete_id, antenna_port): timestamp}
        self.last_detections: Dict[Tuple[str, int], datetime] = {}

        logger.info("🏁 RaceManager inicializado")
    
    # ========================================================================
    # GESTIÓN DE CATEGORÍAS
    # ========================================================================
    
    def add_category(self, category: RaceCategory) -> bool:
        """
        Agregar una categoría al sistema
        
        Args:
            category: Categoría a agregar
        
        Returns:
            bool: True si se agregó, False si ya existía
        
        Raises:
            ValueError: Si la categoría no tiene participantes
        """
        if category.category_id in self.categories:
            logger.warning(f"⚠️  Categoría {category.category_id} ya existe")
            return False
        
        if len(category.participants) == 0:
            raise ValueError("La categoría debe tener al menos un participante")
        
        self.categories[category.category_id] = category
        
        # Inicializar resultados para cada atleta
        self.results[category.category_id] = {}
        for athlete in category.participants:
            self.results[category.category_id][athlete.athlete_id] = AthleteResult(
                athlete=athlete,
                category_id=category.category_id
            )
        
        logger.info(f"✅ Categoría agregada: {category.name} ({len(category)} atletas)")
        return True
    
    def remove_category(self, category_id: str) -> bool:
        """
        Eliminar una categoría
        
        Args:
            category_id: ID de la categoría
        
        Returns:
            bool: True si se eliminó, False si no existía
        """
        if category_id not in self.categories:
            return False
        
        category = self.categories[category_id]
        
        # No permitir eliminar si está en curso
        if category.status == RaceStatus.RUNNING:
            raise ValueError("No se puede eliminar una categoría en curso")
        
        del self.categories[category_id]
        if category_id in self.results:
            del self.results[category_id]
        
        logger.info(f"🗑️  Categoría eliminada: {category.name}")
        return True
    
    def get_category(self, category_id: str) -> Optional[RaceCategory]:
        """Obtener categoría por ID"""
        return self.categories.get(category_id)
    
    def get_all_categories(self) -> List[RaceCategory]:
        """Obtener todas las categorías"""
        return list(self.categories.values())
    
    def get_active_categories(self) -> List[RaceCategory]:
        """Obtener categorías en curso"""
        return [c for c in self.categories.values() if c.status == RaceStatus.RUNNING]
    
    # ========================================================================
    # CONTROL DE CARRERA
    # ========================================================================
    
    def start_category(self, category_id: str) -> bool:
        """
        Iniciar una categoría

        Args:
            category_id: ID de la categoría a iniciar

        Returns:
            bool: True si se inició correctamente

        Raises:
            ValueError: Si la categoría no existe o no está lista

        Nota:
            NO se requiere que todos los participantes tengan chips asignados.
            La carrera puede iniciarse con chips pendientes, ya que en eventos reales
            puede haber corredores con problemas, ausentes, etc.
        """
        category = self.get_category(category_id)
        if not category:
            raise ValueError(f"Categoría {category_id} no existe")

        if category.status not in [RaceStatus.PENDING, RaceStatus.READY]:
            raise ValueError(f"Categoría {category.name} no está lista para iniciar")

        # Informar estado de chips (solo informativo, no bloqueante)
        total_participants = len(category.participants)
        chips_assigned = sum(1 for p in category.participants if p.has_chip_assigned())
        chips_pending = total_participants - chips_assigned

        category.status = RaceStatus.RUNNING
        category.start_time = datetime.now()

        logger.info(f"🚀 Categoría iniciada: {category.name}")
        logger.info(f"   📊 Participantes: {total_participants} | Chips: {chips_assigned} asignados, {chips_pending} pendientes")

        return True
    
    def pause_category(self, category_id: str) -> bool:
        """Pausar una categoría en curso"""
        category = self.get_category(category_id)
        if not category:
            return False
        
        if category.status != RaceStatus.RUNNING:
            return False
        
        category.status = RaceStatus.PAUSED
        logger.info(f"⏸️  Categoría pausada: {category.name}")
        return True
    
    def resume_category(self, category_id: str) -> bool:
        """Reanudar una categoría pausada"""
        category = self.get_category(category_id)
        if not category:
            return False
        
        if category.status != RaceStatus.PAUSED:
            return False
        
        category.status = RaceStatus.RUNNING
        logger.info(f"▶️  Categoría reanudada: {category.name}")
        return True
    
    def finish_category(self, category_id: str) -> bool:
        """
        Finalizar una categoría
        
        Args:
            category_id: ID de la categoría
        
        Returns:
            bool: True si se finalizó correctamente
        """
        category = self.get_category(category_id)
        if not category:
            return False
        
        if category.status != RaceStatus.RUNNING:
            return False
        
        category.status = RaceStatus.FINISHED
        category.end_time = datetime.now()
        
        # Calcular clasificación final
        self._update_classification(category_id)
        
        logger.info(f"🏁 Categoría finalizada: {category.name}")
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
        logger.debug(f"📡 Procesando detección: Tag {tag_id} en puerto {antenna_port}")
        
        # 1. Identificar al atleta y su categoría
        athlete, category = self._find_athlete_by_tag(tag_id)
        
        if not athlete:
            logger.warning(f"⚠️  Tag {tag_id} no asociado a ningún atleta")
            return None
        
        if not category:
            logger.warning(f"⚠️  Atleta {athlete.name} sin categoría activa")
            return None
        
        # Solo procesar si la categoría está corriendo
        if category.status != RaceStatus.RUNNING:
            logger.debug(f"Categoría {category.name} no está en curso, ignorando detección")
            return None

        # 2. Validar períodos de latencia (anti-duplicados)
        if not self._validate_detection_timing(athlete, antenna_port, timestamp, roles):
            return None

        # 3. Determinar tipo de evento según roles
        event_type, checkpoint_num = self._determine_event_type(roles, athlete, category)

        if not event_type:
            logger.warning(f"⚠️  No se pudo determinar tipo de evento para roles: {roles}")
            return None

        # 4. Crear evento de detección
        event = DetectionEvent(
            tag_id=tag_id,
            timestamp=timestamp,
            antenna_port=antenna_port,
            event_type=event_type,
            checkpoint_number=checkpoint_num,
            athlete=athlete,
            category_id=category.category_id
        )

        # 5. Registrar en resultado del atleta
        result = self.results[category.category_id][athlete.athlete_id]
        success = self._record_event_in_result(result, event)

        if success:
            # 6. Actualizar tracking de última detección
            detection_key = (athlete.athlete_id, antenna_port)
            self.last_detections[detection_key] = timestamp

            # 7. Guardar en historial
            self.detection_history.append(event)

            # 8. Actualizar clasificación
            self._update_classification(category.category_id)

            logger.info(f"✅ {event}")
            return event
        
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
            result = self.results.get(athlete.category_id, {}).get(athlete.athlete_id)
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

    def _find_athlete_by_tag(self, tag_id: str) -> Tuple[Optional[Athlete], Optional[RaceCategory]]:
        """
        Buscar atleta por tag_id en categorías activas
        
        Args:
            tag_id: ID del chip
        
        Returns:
            Tuple (Athlete, RaceCategory) o (None, None) si no se encuentra
        """
        # Buscar primero en categorías corriendo
        for category in self.get_active_categories():
            athlete = category.get_participant_by_tag(tag_id)
            if athlete:
                return athlete, category
        
        # Si no está en activas, buscar en todas
        for category in self.categories.values():
            athlete = category.get_participant_by_tag(tag_id)
            if athlete:
                return athlete, category
        
        return None, None
    
    def _determine_event_type(
        self,
        roles: List[str],
        athlete: Athlete,
        category: RaceCategory
    ) -> Tuple[Optional[EventType], Optional[int]]:
        """
        Determinar tipo de evento según roles y estado del atleta
        
        Args:
            roles: Roles de la antena
            athlete: Atleta que pasó
            category: Categoría
        
        Returns:
            Tuple (EventType, checkpoint_number) o (None, None)
        """
        result = self.results[category.category_id][athlete.athlete_id]
        
        # Si no ha largado y la antena tiene rol 'start'
        if 'start' in roles and result.status == AthleteStatus.NOT_STARTED:
            return EventType.START, None
        
        # Si está corriendo
        if result.status == AthleteStatus.RUNNING:
            # Si tiene rol 'finish'
            if 'finish' in roles:
                return EventType.FINISH, None
            
            # Si tiene rol 'checkpoint'
            if 'checkpoint' in roles:
                # Determinar número de checkpoint
                next_checkpoint = len(result.checkpoint_times) + 1
                return EventType.CHECKPOINT, next_checkpoint
        
        return None, None
    
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
    
    def get_results(self, category_id: str) -> List[AthleteResult]:
        """
        Obtener resultados de una categoría
        
        Args:
            category_id: ID de la categoría
        
        Returns:
            Lista de AthleteResult ordenados por posición
        """
        if category_id not in self.results:
            return []
        
        results = list(self.results[category_id].values())
        
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
    
    def _update_classification(self, category_id: str):
        """
        Actualizar posiciones en la clasificación
        
        Args:
            category_id: ID de la categoría
        """
        results = self.get_results(category_id)
        
        position = 1
        for result in results:
            if result.status == AthleteStatus.FINISHED:
                result.position = position
                position += 1
            else:
                result.position = None
    
    def get_athlete_result(self, category_id: str, athlete_id: str) -> Optional[AthleteResult]:
        """
        Obtener resultado de un atleta específico
        
        Args:
            category_id: ID de la categoría
            athlete_id: ID del atleta
        
        Returns:
            AthleteResult o None
        """
        if category_id not in self.results:
            return None
        
        return self.results[category_id].get(athlete_id)
    
    def get_statistics(self, category_id: str) -> Dict:
        """
        Obtener estadísticas de una categoría
        
        Args:
            category_id: ID de la categoría
        
        Returns:
            Dict con estadísticas
        """
        results = self.get_results(category_id)
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
    
    # ========================================================================
    # UTILIDADES
    # ========================================================================
    
    def reset_category(self, category_id: str) -> bool:
        """
        Resetear resultados de una categoría
        
        Args:
            category_id: ID de la categoría
        
        Returns:
            bool: True si se reseteó
        """
        category = self.get_category(category_id)
        if not category:
            return False
        
        # Reinicializar resultados
        self.results[category_id] = {}
        for athlete in category.participants:
            self.results[category_id][athlete.athlete_id] = AthleteResult(
                athlete=athlete,
                category_id=category_id
            )

        # Limpiar tracking de detecciones de esta categoría
        athlete_ids = {a.athlete_id for a in category.participants}
        self.last_detections = {
            key: value for key, value in self.last_detections.items()
            if key[0] not in athlete_ids
        }

        # Resetear estado
        category.status = RaceStatus.PENDING
        category.start_time = None
        category.end_time = None

        logger.info(f"🔄 Categoría reseteada: {category.name}")
        return True
    
    def __repr__(self) -> str:
        """Representación para debugging"""
        return f"<RaceManager: {len(self.categories)} categorías, {len(self.detection_history)} eventos>"


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
    
    # Test 1: Crear y agregar categoría
    print("\n1. Crear categoría con atletas...")
    from models import create_test_category
    category = create_test_category()
    manager.add_category(category)
    print(f"   ✅ Categoría agregada: {category}")
    
    # Test 2: Iniciar categoría
    print("\n2. Iniciar categoría...")
    manager.start_category(category.category_id)
    print(f"   ✅ Estado: {category.status.value}")
    
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
    results = manager.get_results(category.category_id)
    for result in results:
        pos = f"#{result.position}" if result.position else "  -"
        print(f"   {pos} {result}")
    
    # Test 5: Estadísticas
    print("\n5. Estadísticas...")
    stats = manager.get_statistics(category.category_id)
    print(f"   Total: {stats['total_participants']}")
    print(f"   Iniciados: {stats['started']}")
    print(f"   Finalizados: {stats['finished']}")
    if stats['fastest_time']:
        print(f"   Más rápido: {stats['fastest_time']:.3f}s")
        print(f"   Promedio: {stats['average_time']:.3f}s")
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)