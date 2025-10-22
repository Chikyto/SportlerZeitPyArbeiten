#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelos de Datos para Race Tracking
src/core/race_tracking/models.py

Define las estructuras de datos para el sistema de cronometraje:
- Athlete: Participante con chip RFID
- RaceCategory: Categoría de carrera
- DetectionEvent: Evento de detección de chip
- AthleteResult: Resultado de un atleta

Versión: 1.2.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from enum import Enum
import uuid


# ============================================================================
# ENUMERACIONES
# ============================================================================

class AthleteStatus(Enum):
    """Estados posibles de un atleta durante la carrera"""
    NOT_STARTED = "not_started"     # No ha largado
    RUNNING = "running"             # En carrera
    FINISHED = "finished"           # Finalizó
    DNF = "dnf"                     # Did Not Finish (no terminó)
    DNS = "dns"                     # Did Not Start (no largó)
    DSQ = "dsq"                     # Disqualified (descalificado)


class RaceStatus(Enum):
    """Estados posibles de una categoría/carrera"""
    PENDING = "pending"             # Pendiente de configuración
    READY = "ready"                 # Lista para iniciar
    RUNNING = "running"             # En curso
    PAUSED = "paused"               # Pausada
    FINISHED = "finished"           # Finalizada
    CANCELLED = "cancelled"         # Cancelada


class EventType(Enum):
    """Tipos de eventos de detección"""
    START = "start"                 # Largada
    CHECKPOINT = "checkpoint"       # Punto intermedio
    FINISH = "finish"               # Meta


# ============================================================================
# MODELOS DE DATOS
# ============================================================================

@dataclass
class Athlete:
    """
    Participante en una carrera
    
    Attributes:
        tag_id: ID del chip RFID (ej: "7662")
        bib_number: Número de dorsal (ej: 101)
        name: Nombre completo del atleta
        category_id: ID de la categoría a la que pertenece
        team: Equipo o club (opcional)
        notes: Notas adicionales (opcional)
        athlete_id: ID único generado automáticamente
    
    Example:
        >>> athlete = Athlete(
        ...     tag_id="7662",
        ...     bib_number=101,
        ...     name="Juan Pérez",
        ...     category_id="100m-varones"
        ... )
    """
    tag_id: str
    bib_number: int
    name: str
    category_id: str
    team: Optional[str] = None
    notes: Optional[str] = None
    athlete_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validar datos al crear"""
        if not self.tag_id:
            raise ValueError("tag_id no puede estar vacío")
        if self.bib_number <= 0:
            raise ValueError("bib_number debe ser mayor a 0")
        if not self.name or not self.name.strip():
            raise ValueError("name no puede estar vacío")
    
    def __str__(self) -> str:
        """Representación legible"""
        return f"#{self.bib_number} {self.name} (Tag: {self.tag_id})"
    
    def __repr__(self) -> str:
        """Representación para debugging"""
        return f"<Athlete {self.bib_number}: {self.name}>"


@dataclass
class RaceCategory:
    """
    Categoría de carrera
    
    Attributes:
        category_id: ID único de la categoría
        name: Nombre descriptivo (ej: "100m Varones")
        distance: Distancia en metros
        expected_checkpoints: Número de checkpoints esperados (sin contar largada/meta)
        participants: Lista de atletas inscritos
        status: Estado actual de la carrera
        start_time: Momento de largada oficial (opcional)
        end_time: Momento de finalización (opcional)
        notes: Notas adicionales
    
    Example:
        >>> category = RaceCategory(
        ...     category_id="100m-varones",
        ...     name="100 Metros Varones",
        ...     distance=100.0,
        ...     expected_checkpoints=0
        ... )
    """
    category_id: str
    name: str
    distance: float
    expected_checkpoints: int = 0
    participants: List[Athlete] = field(default_factory=list)
    status: RaceStatus = RaceStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validar datos al crear"""
        if not self.category_id:
            raise ValueError("category_id no puede estar vacío")
        if not self.name or not self.name.strip():
            raise ValueError("name no puede estar vacío")
        if self.distance <= 0:
            raise ValueError("distance debe ser mayor a 0")
        if self.expected_checkpoints < 0:
            raise ValueError("expected_checkpoints no puede ser negativo")
    
    def add_participant(self, athlete: Athlete):
        """
        Agregar participante a la categoría
        
        Args:
            athlete: Atleta a agregar
        
        Raises:
            ValueError: Si el atleta ya está inscrito o si el tag_id ya existe
        """
        # Verificar que no esté duplicado por athlete_id
        if any(p.athlete_id == athlete.athlete_id for p in self.participants):
            raise ValueError(f"Atleta {athlete.name} ya está inscrito en esta categoría")
        
        # Verificar que no haya tag_id duplicado
        if any(p.tag_id == athlete.tag_id for p in self.participants):
            raise ValueError(f"Tag {athlete.tag_id} ya está asignado a otro atleta")
        
        # Verificar que no haya dorsal duplicado
        if any(p.bib_number == athlete.bib_number for p in self.participants):
            raise ValueError(f"Dorsal {athlete.bib_number} ya está asignado a otro atleta")
        
        # Actualizar category_id del atleta
        athlete.category_id = self.category_id
        
        self.participants.append(athlete)
    
    def remove_participant(self, athlete_id: str) -> bool:
        """
        Eliminar participante de la categoría
        
        Args:
            athlete_id: ID del atleta a eliminar
        
        Returns:
            bool: True si se eliminó, False si no se encontró
        """
        initial_count = len(self.participants)
        self.participants = [p for p in self.participants if p.athlete_id != athlete_id]
        return len(self.participants) < initial_count
    
    def get_participant_by_tag(self, tag_id: str) -> Optional[Athlete]:
        """
        Buscar participante por tag_id
        
        Args:
            tag_id: ID del chip RFID
        
        Returns:
            Athlete si se encuentra, None si no
        """
        for athlete in self.participants:
            if athlete.tag_id == tag_id:
                return athlete
        return None
    
    def get_participant_by_bib(self, bib_number: int) -> Optional[Athlete]:
        """
        Buscar participante por número de dorsal
        
        Args:
            bib_number: Número de dorsal
        
        Returns:
            Athlete si se encuentra, None si no
        """
        for athlete in self.participants:
            if athlete.bib_number == bib_number:
                return athlete
        return None
    
    def __len__(self) -> int:
        """Número de participantes"""
        return len(self.participants)
    
    def __str__(self) -> str:
        """Representación legible"""
        return f"{self.name} ({len(self.participants)} participantes)"
    
    def __repr__(self) -> str:
        """Representación para debugging"""
        return f"<RaceCategory '{self.name}': {len(self.participants)} athletes, {self.status.value}>"


@dataclass
class DetectionEvent:
    """
    Evento de detección de chip RFID
    
    Attributes:
        event_id: ID único del evento
        tag_id: ID del chip detectado
        timestamp: Momento exacto de la detección
        antenna_port: Puerto donde se detectó
        event_type: Tipo de evento (start/checkpoint/finish)
        checkpoint_number: Número de checkpoint (si aplica)
        athlete: Referencia al atleta (se asigna después)
        category_id: ID de la categoría (se asigna después)
    
    Example:
        >>> event = DetectionEvent(
        ...     tag_id="7662",
        ...     timestamp=datetime.now(),
        ...     antenna_port=2,
        ...     event_type=EventType.START
        ... )
    """
    tag_id: str
    timestamp: datetime
    antenna_port: int
    event_type: EventType
    checkpoint_number: Optional[int] = None
    athlete: Optional[Athlete] = None
    category_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Validar datos al crear"""
        if not self.tag_id:
            raise ValueError("tag_id no puede estar vacío")
        if not isinstance(self.timestamp, datetime):
            raise ValueError("timestamp debe ser un datetime")
        if self.antenna_port < 0:
            raise ValueError("antenna_port debe ser >= 0")
        if not isinstance(self.event_type, EventType):
            raise ValueError("event_type debe ser un EventType")
        
        # Validar checkpoint_number según event_type
        if self.event_type == EventType.CHECKPOINT:
            if self.checkpoint_number is None:
                raise ValueError("checkpoint_number requerido para eventos CHECKPOINT")
            if self.checkpoint_number <= 0:
                raise ValueError("checkpoint_number debe ser > 0")
        elif self.checkpoint_number is not None:
            raise ValueError("checkpoint_number solo válido para eventos CHECKPOINT")
    
    def __str__(self) -> str:
        """Representación legible"""
        time_str = self.timestamp.strftime('%H:%M:%S.%f')[:-3]
        if self.event_type == EventType.CHECKPOINT:
            return f"{time_str} - Tag {self.tag_id} → CP{self.checkpoint_number} (Puerto {self.antenna_port})"
        else:
            return f"{time_str} - Tag {self.tag_id} → {self.event_type.value.upper()} (Puerto {self.antenna_port})"
    
    def __repr__(self) -> str:
        """Representación para debugging"""
        return f"<DetectionEvent {self.event_type.value}: {self.tag_id} @ {self.timestamp}>"


@dataclass
class AthleteResult:
    """
    Resultado de un atleta en una carrera
    
    Attributes:
        athlete: Atleta
        category_id: ID de la categoría
        status: Estado actual del atleta
        start_time: Momento de largada
        finish_time: Momento de llegada
        total_time: Tiempo total (calculado)
        splits: Tiempos parciales por checkpoint {checkpoint_num: timedelta}
        checkpoint_times: Timestamps de cada checkpoint {checkpoint_num: datetime}
        position: Posición en la clasificación
        
    Example:
        >>> result = AthleteResult(
        ...     athlete=athlete,
        ...     category_id="100m-varones"
        ... )
    """
    athlete: Athlete
    category_id: str
    status: AthleteStatus = AthleteStatus.NOT_STARTED
    start_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    total_time: Optional[timedelta] = None
    splits: Dict[int, timedelta] = field(default_factory=dict)
    checkpoint_times: Dict[int, datetime] = field(default_factory=dict)
    position: Optional[int] = None
    
    def record_start(self, timestamp: datetime):
        """
        Registrar largada
        
        Args:
            timestamp: Momento de largada
        """
        if self.start_time is not None:
            raise ValueError(f"Atleta {self.athlete.name} ya tiene hora de largada registrada")
        
        self.start_time = timestamp
        self.status = AthleteStatus.RUNNING
    
    def record_checkpoint(self, checkpoint_number: int, timestamp: datetime):
        """
        Registrar paso por checkpoint
        
        Args:
            checkpoint_number: Número del checkpoint (1, 2, 3...)
            timestamp: Momento del paso
        
        Raises:
            ValueError: Si no ha largado o si el checkpoint ya fue registrado
        """
        if self.start_time is None:
            raise ValueError(f"Atleta {self.athlete.name} no ha largado aún")
        
        if checkpoint_number in self.checkpoint_times:
            raise ValueError(f"Checkpoint {checkpoint_number} ya registrado para {self.athlete.name}")
        
        # Registrar timestamp del checkpoint
        self.checkpoint_times[checkpoint_number] = timestamp
        
        # Calcular split (tiempo desde largada o desde checkpoint anterior)
        if checkpoint_number == 1:
            # Primer checkpoint: tiempo desde largada
            split_time = timestamp - self.start_time
        else:
            # Checkpoints siguientes: tiempo desde checkpoint anterior
            prev_checkpoint_time = self.checkpoint_times.get(checkpoint_number - 1)
            if prev_checkpoint_time:
                split_time = timestamp - prev_checkpoint_time
            else:
                # Si falta checkpoint anterior, calcular desde largada
                split_time = timestamp - self.start_time
        
        self.splits[checkpoint_number] = split_time
    
    def record_finish(self, timestamp: datetime):
        """
        Registrar llegada a meta
        
        Args:
            timestamp: Momento de llegada
        
        Raises:
            ValueError: Si no ha largado o ya finalizó
        """
        if self.start_time is None:
            raise ValueError(f"Atleta {self.athlete.name} no ha largado aún")
        
        if self.finish_time is not None:
            raise ValueError(f"Atleta {self.athlete.name} ya tiene hora de llegada registrada")
        
        self.finish_time = timestamp
        self.total_time = timestamp - self.start_time
        self.status = AthleteStatus.FINISHED
    
    def get_total_seconds(self) -> Optional[float]:
        """
        Obtener tiempo total en segundos
        
        Returns:
            float con segundos totales, None si no ha finalizado
        """
        if self.total_time:
            return self.total_time.total_seconds()
        return None
    
    def get_formatted_time(self) -> str:
        """
        Obtener tiempo formateado como string
        
        Returns:
            String con formato "MM:SS.mmm" o "-" si no ha finalizado
        """
        if not self.total_time:
            return "-"
        
        total_seconds = self.total_time.total_seconds()
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        
        if minutes > 0:
            return f"{minutes}:{seconds:06.3f}"
        else:
            return f"{seconds:.3f}s"
    
    def __str__(self) -> str:
        """Representación legible"""
        return f"{self.athlete.name}: {self.get_formatted_time()} ({self.status.value})"
    
    def __repr__(self) -> str:
        """Representación para debugging"""
        return f"<AthleteResult {self.athlete.name}: {self.get_formatted_time()}>"


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def create_test_category() -> RaceCategory:
    """
    Crear categoría de prueba para testing
    
    Returns:
        RaceCategory con datos de ejemplo
    """
    category = RaceCategory(
        category_id="100m-varones-test",
        name="100 Metros Varones (Test)",
        distance=100.0,
        expected_checkpoints=0
    )
    
    # Agregar atletas de prueba
    test_athletes = [
        Athlete("7662", 101, "Juan Pérez", category.category_id),
        Athlete("8587", 102, "Pedro López", category.category_id, team="Club A"),
        Athlete("1923", 103, "Carlos Ruiz", category.category_id, team="Club B"),
    ]
    
    for athlete in test_athletes:
        category.add_participant(athlete)
    
    return category


if __name__ == "__main__":
    """Tests básicos de los modelos"""
    
    print("=" * 60)
    print("TESTS DE MODELOS")
    print("=" * 60)
    
    # Test 1: Crear categoría
    print("\n1. Crear categoría...")
    category = create_test_category()
    print(f"   ✅ {category}")
    print(f"   Participantes: {len(category)}")
    
    # Test 2: Buscar por tag
    print("\n2. Buscar atleta por tag...")
    athlete = category.get_participant_by_tag("7662")
    if athlete:
        print(f"   ✅ Encontrado: {athlete}")
    
    # Test 3: Crear evento de detección
    print("\n3. Crear evento de detección...")
    event = DetectionEvent(
        tag_id="7662",
        timestamp=datetime.now(),
        antenna_port=2,
        event_type=EventType.START
    )
    print(f"   ✅ {event}")
    
    # Test 4: Crear resultado y registrar tiempos
    print("\n4. Simular carrera...")
    result = AthleteResult(athlete=athlete, category_id=category.category_id)
    
    now = datetime.now()
    result.record_start(now)
    print(f"   ✅ Largada registrada: {result.start_time}")
    
    # Simular llegada 10 segundos después
    finish_time = now + timedelta(seconds=10.5)
    result.record_finish(finish_time)
    print(f"   ✅ Meta registrada: {result.get_formatted_time()}")
    print(f"   Estado: {result.status.value}")
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)