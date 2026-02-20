#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modelos de Datos para Race Tracking
src/core/race_tracking/models.py

Define las estructuras de datos para el sistema de cronometraje:
- Athlete: Participante con chip RFID
- RaceDistance: Distancia de carrera (5K, 10K, 21K, etc.)
- DetectionEvent: Evento de detección de chip
- AthleteResult: Resultado de un atleta
- AwardCategory: Categoría de premiación por género y edad

Versión: 2.0.0 - Refactorización semántica: category → distance
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
    """Estados posibles de una distancia de carrera"""
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
    LAP = "lap"                     # Vuelta completada (para carreras por vueltas)


class RaceMode(Enum):
    """Modos de carrera"""
    LINEAR = "linear"               # Carrera lineal: largada → checkpoints → meta
    LAPS = "laps"                   # Carrera por vueltas: misma antena múltiples veces
    TIME_BASED = "time_based"       # Carrera por tiempo: máximo de vueltas en X horas


# ============================================================================
# MODELOS DE DATOS
# ============================================================================

@dataclass
class Athlete:
    """
    Participante en una carrera

    Attributes:
        tag_id: ID del chip RFID (ej: "7662") - puede estar vacío si aún no se asignó
        bib_number: Número de dorsal (ej: 101)
        name: Nombre completo del atleta
        distance_id: ID de la distancia a la que está inscrito (ej: "5k", "10k", "21k")
        gender: Género (M/F/Otro) - opcional
        birth_date: Fecha de nacimiento - opcional
        team: Equipo o club (opcional)
        notes: Notas adicionales (opcional)
        athlete_id: ID único generado automáticamente

    Example:
        >>> athlete = Athlete(
        ...     tag_id="7662",
        ...     bib_number=101,
        ...     name="Juan Pérez",
        ...     distance_id="5k",
        ...     gender="M",
        ...     birth_date=datetime(1990, 5, 15)
        ... )
    """
    tag_id: str = ""  # Vacío por defecto, se asigna luego
    bib_number: int = 0
    name: str = ""
    distance_id: str = ""
    gender: Optional[str] = None  # M, F, Otro
    birth_date: Optional[datetime] = None
    team: Optional[str] = None
    notes: Optional[str] = None
    athlete_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chip_aliases: List[str] = field(default_factory=list)  # IDs alternativos del mismo chip

    def __post_init__(self):
        """Validar datos al crear"""
        # tag_id puede estar vacío (se asigna después)
        if self.bib_number < 0:
            raise ValueError("bib_number debe ser mayor o igual a 0")
        if not self.name or not self.name.strip():
            raise ValueError("name no puede estar vacío")
        if not self.distance_id or not self.distance_id.strip():
            raise ValueError("distance_id no puede estar vacío")

    def has_chip_assigned(self) -> bool:
        """Verifica si el atleta tiene chip asignado"""
        return bool(self.tag_id and self.tag_id.strip())

    def matches_tag(self, tag_id: str) -> bool:
        """
        Verificar si un tag_id coincide con este atleta (tag principal o alias)

        Args:
            tag_id: ID del chip a verificar

        Returns:
            True si coincide con el tag principal o algún alias
        """
        if self.tag_id == tag_id:
            return True
        return tag_id in self.chip_aliases

    def add_chip_alias(self, alias_tag_id: str) -> bool:
        """
        Agregar un alias de chip (ID alternativo para el mismo chip físico)

        Útil cuando USB y TCP/IP reportan diferentes IDs para el mismo chip.

        Args:
            alias_tag_id: ID alternativo a registrar

        Returns:
            True si se agregó, False si ya existía
        """
        if alias_tag_id == self.tag_id:
            return False
        if alias_tag_id in self.chip_aliases:
            return False
        self.chip_aliases.append(alias_tag_id)
        return True

    def get_age(self) -> Optional[int]:
        """
        Calcular edad actual del atleta

        Returns:
            int con edad en años, None si no hay fecha de nacimiento
        """
        if not self.birth_date:
            return None

        today = datetime.now()
        age = today.year - self.birth_date.year

        # Ajustar si aún no cumplió años este año
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    def get_award_category(self) -> Optional[str]:
        """
        Determinar categoría de premiación basada en género y edad

        Rangos de edad estándar IAAF:
        - Sub-20 (15-19)
        - Elite (20-34)
        - Master A (35-39)
        - Master B (40-44)
        - Master C (45-49)
        - Master D (50-54)
        - Master E (55+)

        Returns:
            str con categoría (ej: "F15-19", "M35-39"), None si faltan datos
        """
        if not self.gender or not self.birth_date:
            return None

        age = self.get_age()
        if age is None:
            return None

        # Normalizar género
        gender_code = self.gender.upper()[0] if self.gender else "?"

        # Determinar rango de edad
        if age < 15:
            age_range = "U15"
        elif age < 20:
            age_range = "15-19"
        elif age < 35:
            age_range = "20-34"
        elif age < 40:
            age_range = "35-39"
        elif age < 45:
            age_range = "40-44"
        elif age < 50:
            age_range = "45-49"
        elif age < 55:
            age_range = "50-54"
        else:
            age_range = "55+"

        return f"{gender_code}{age_range}"

    def __str__(self) -> str:
        """Representación legible"""
        chip_info = f"Tag: {self.tag_id}" if self.has_chip_assigned() else "Sin chip"
        return f"#{self.bib_number} {self.name} ({chip_info})"

    def __repr__(self) -> str:
        """Representación para debugging"""
        return f"<Athlete {self.bib_number}: {self.name}>"


@dataclass
class RaceDistance:
    """
    Distancia de carrera (5K, 10K, 21K, Maratón, etc.)

    Representa una distancia específica dentro de un evento deportivo.
    No confundir con AwardCategory (categorías de premiación por género/edad).

    Attributes:
        distance_id: ID único de la distancia (ej: "5k", "10k", "21k", "42k", "7k_1h")
        name: Nombre descriptivo (ej: "5K", "Media Maratón", "Ultra 100K", "7K por Hora")
        distance_meters: Distancia en metros (por vuelta si es carrera por vueltas)
        expected_checkpoints: Número de checkpoints esperados (sin contar largada/meta)
        participants: Lista de atletas inscritos en esta distancia
        status: Estado actual de la carrera
        start_time: Momento de largada oficial (opcional)
        end_time: Momento de finalización (opcional)
        notes: Notas adicionales
        race_mode: Modo de carrera (LINEAR, LAPS, TIME_BASED)
        duration_hours: Duración en horas (solo para TIME_BASED) - ej: 6 horas, 12 horas, 24 horas

    Example - Carrera lineal:
        >>> distance = RaceDistance(
        ...     distance_id="21k",
        ...     name="Media Maratón",
        ...     distance_meters=21097.0,
        ...     expected_checkpoints=2,
        ...     race_mode=RaceMode.LINEAR
        ... )

    Example - Carrera por tiempo:
        >>> distance = RaceDistance(
        ...     distance_id="7k_1h",
        ...     name="7K por Hora - 6 Horas",
        ...     distance_meters=7000.0,
        ...     expected_checkpoints=0,
        ...     race_mode=RaceMode.TIME_BASED,
        ...     duration_hours=6
        ... )
    """
    distance_id: str
    name: str
    distance_meters: float
    expected_checkpoints: int = 0
    participants: List[Athlete] = field(default_factory=list)
    status: RaceStatus = RaceStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    race_mode: RaceMode = RaceMode.LINEAR  # Nuevo campo
    duration_hours: Optional[float] = None  # Nuevo campo (solo para TIME_BASED)
    
    def __post_init__(self):
        """Validar datos al crear"""
        if not self.distance_id:
            raise ValueError("distance_id no puede estar vacío")
        if not self.name or not self.name.strip():
            raise ValueError("name no puede estar vacío")
        if self.distance_meters <= 0:
            raise ValueError("distance_meters debe ser mayor a 0")
        if self.expected_checkpoints < 0:
            raise ValueError("expected_checkpoints no puede ser negativo")
    
    def add_participant(self, athlete: Athlete):
        """
        Agregar participante a esta distancia

        Args:
            athlete: Atleta a agregar

        Raises:
            ValueError: Si el atleta ya está inscrito o si el tag_id ya existe
        """
        # Verificar que no esté duplicado por athlete_id
        if any(p.athlete_id == athlete.athlete_id for p in self.participants):
            raise ValueError(f"Atleta {athlete.name} ya está inscrito en esta distancia")

        # Verificar que no haya tag_id duplicado
        if any(p.tag_id == athlete.tag_id for p in self.participants):
            raise ValueError(f"Tag {athlete.tag_id} ya está asignado a otro atleta")

        # Verificar que no haya dorsal duplicado
        if any(p.bib_number == athlete.bib_number for p in self.participants):
            raise ValueError(f"Dorsal {athlete.bib_number} ya está asignado a otro atleta")

        # Actualizar distance_id del atleta
        athlete.distance_id = self.distance_id

        self.participants.append(athlete)
    
    def remove_participant(self, athlete_id: str) -> bool:
        """
        Eliminar participante de esta distancia

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
        Buscar participante por tag_id o alias

        Busca primero por tag_id principal, luego por aliases.
        Esto soporta chips que son detectados con IDs diferentes por
        USB (ej: "818") vs TCP/IP (ej: "E3806894").

        Args:
            tag_id: ID del chip RFID

        Returns:
            Athlete si se encuentra, None si no
        """
        for athlete in self.participants:
            if athlete.matches_tag(tag_id):
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
        return f"<RaceDistance '{self.name}': {len(self.participants)} athletes, {self.status.value}>"


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
        distance_id: ID de la distancia (se asigna después)

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
    distance_id: Optional[str] = None
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
        distance_id: ID de la distancia en la que compite
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
        ...     distance_id="21k"
        ... )
    """
    athlete: Athlete
    distance_id: str
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


@dataclass
class AwardCategory:
    """
    Categoría de premiación basada en género y edad

    Representa una categoría de premiación (ej: "Masculino 35-39", "Femenino Sub-20").
    No confundir con RaceDistance (que representa distancias como 5K, 10K, etc.).

    Attributes:
        award_category_id: ID único (ej: "F15-19", "M35-39")
        name: Nombre descriptivo (ej: "Femenino 15-19 años")
        gender: Género ('M', 'F', 'O' para Otro, None para Mixto)
        min_age: Edad mínima (incluida)
        max_age: Edad máxima (incluida, None para sin límite)
        distance_ids: Lista de IDs de distancias a las que aplica (None = todas)
        is_iaaf: Si es una categoría estándar IAAF (no modificable)
        description: Descripción adicional

    Example:
        >>> # Categoría IAAF (aplica a todas las distancias)
        >>> cat = AwardCategory(
        ...     award_category_id="F15-19",
        ...     name="Femenino Sub-20",
        ...     gender="F",
        ...     min_age=15,
        ...     max_age=19,
        ...     is_iaaf=True
        ... )
        >>> # Categoría personalizada solo para 21K
        >>> cat = AwardCategory(
        ...     award_category_id="M40-49-21K",
        ...     name="Masculino Master 40-49 (21K)",
        ...     gender="M",
        ...     min_age=40,
        ...     max_age=49,
        ...     distance_ids=["21k"],
        ...     is_iaaf=False
        ... )
    """
    award_category_id: str
    name: str
    gender: Optional[str] = None  # M, F, O (Otro), None (Mixto)
    min_age: int = 0
    max_age: Optional[int] = None  # None = sin límite superior
    distance_ids: Optional[List[str]] = None  # None = aplica a todas las distancias
    is_iaaf: bool = False
    description: Optional[str] = None

    def __post_init__(self):
        """Validar datos al crear"""
        if not self.award_category_id:
            raise ValueError("award_category_id no puede estar vacío")
        if not self.name:
            raise ValueError("name no puede estar vacío")
        if self.min_age < 0:
            raise ValueError("min_age debe ser >= 0")
        if self.max_age is not None and self.max_age < self.min_age:
            raise ValueError("max_age debe ser >= min_age")
        if self.gender and self.gender.upper() not in ['M', 'F', 'O', None]:
            # Normalizar género
            self.gender = self.gender.upper()[0] if self.gender else None

    def applies_to_athlete(self, athlete: 'Athlete') -> bool:
        """
        Verificar si esta categoría de premiación aplica a un atleta

        Args:
            athlete: Atleta a verificar

        Returns:
            bool: True si el atleta pertenece a esta categoría de premiación
        """
        # Verificar género
        if self.gender:
            athlete_gender = athlete.gender.upper()[0] if athlete.gender else None
            if athlete_gender != self.gender:
                return False

        # Verificar edad
        age = athlete.get_age()
        if age is None:
            return False  # Sin edad, no podemos categorizar

        if age < self.min_age:
            return False

        if self.max_age is not None and age > self.max_age:
            return False

        # Verificar distancia (si esta categoría aplica solo a ciertas distancias)
        if self.distance_ids is not None:
            if athlete.distance_id not in self.distance_ids:
                return False

        return True

    def applies_to_distance(self, distance_id: str) -> bool:
        """
        Verificar si esta categoría de premiación aplica a una distancia

        Args:
            distance_id: ID de la distancia (ej: "5k", "10k", "21k")

        Returns:
            bool: True si aplica a esa distancia
        """
        if self.distance_ids is None:
            return True  # Aplica a todas las distancias
        return distance_id in self.distance_ids

    def get_age_range_str(self) -> str:
        """
        Obtener string con rango de edad

        Returns:
            str: Rango formateado (ej: "15-19", "55+", "0-14")
        """
        if self.max_age is None:
            return f"{self.min_age}+"
        return f"{self.min_age}-{self.max_age}"

    def __str__(self) -> str:
        """Representación legible"""
        gender_str = {"M": "Masculino", "F": "Femenino", "O": "Otro"}.get(self.gender, "Mixto")
        age_str = self.get_age_range_str()
        return f"{gender_str} {age_str}"

    def __repr__(self) -> str:
        """Representación para debugging"""
        return f"<AwardCategory '{self.name}' ({self.award_category_id})>"


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def create_iaaf_award_categories() -> List[AwardCategory]:
    """
    Crear categorías de premiación estándar IAAF

    Categorías por género y edad según International Association of Athletics Federations:
    - Sub-15 (0-14)
    - Sub-20 (15-19)
    - Elite (20-34)
    - Master A (35-39)
    - Master B (40-44)
    - Master C (45-49)
    - Master D (50-54)
    - Master E (55+)

    Returns:
        List[AwardCategory]: Lista de categorías IAAF para M y F
    """
    categories = []

    # Definición de rangos IAAF
    age_ranges = [
        ("U15", "Sub-15", 0, 14),
        ("15-19", "Sub-20", 15, 19),
        ("20-34", "Elite", 20, 34),
        ("35-39", "Master A", 35, 39),
        ("40-44", "Master B", 40, 44),
        ("45-49", "Master C", 45, 49),
        ("50-54", "Master D", 50, 54),
        ("55+", "Master E", 55, None),
    ]

    # Crear para Masculino y Femenino
    for gender_code, gender_name in [("M", "Masculino"), ("F", "Femenino")]:
        for age_code, age_name, min_age, max_age in age_ranges:
            cat_id = f"{gender_code}{age_code}"
            cat_name = f"{gender_name} {age_name}"

            if max_age is None:
                description = f"Categoría {gender_name} {min_age} años o más (IAAF)"
            else:
                description = f"Categoría {gender_name} {min_age}-{max_age} años (IAAF)"

            category = AwardCategory(
                award_category_id=cat_id,
                name=cat_name,
                gender=gender_code,
                min_age=min_age,
                max_age=max_age,
                distance_ids=None,  # Aplica a todas las distancias
                is_iaaf=True,
                description=description
            )
            categories.append(category)

    return categories


def create_test_distance() -> RaceDistance:
    """
    Crear distancia de prueba para testing

    Returns:
        RaceDistance con datos de ejemplo
    """
    distance = RaceDistance(
        distance_id="100m-test",
        name="100 Metros (Test)",
        distance_meters=100.0,
        expected_checkpoints=0
    )

    # Agregar atletas de prueba
    test_athletes = [
        Athlete("7662", 101, "Juan Pérez", distance.distance_id),
        Athlete("8587", 102, "Pedro López", distance.distance_id, team="Club A"),
        Athlete("1923", 103, "Carlos Ruiz", distance.distance_id, team="Club B"),
    ]

    for athlete in test_athletes:
        distance.add_participant(athlete)

    return distance


if __name__ == "__main__":
    """Tests básicos de los modelos"""

    print("=" * 60)
    print("TESTS DE MODELOS")
    print("=" * 60)

    # Test 1: Crear distancia
    print("\n1. Crear distancia...")
    distance = create_test_distance()
    print(f"   ✅ {distance}")
    print(f"   Participantes: {len(distance)}")

    # Test 2: Buscar por tag
    print("\n2. Buscar atleta por tag...")
    athlete = distance.get_participant_by_tag("7662")
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
    result = AthleteResult(athlete=athlete, distance_id=distance.distance_id)

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