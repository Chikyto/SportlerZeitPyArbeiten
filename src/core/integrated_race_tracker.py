"""
Sistema integrado de cronometraje que combina:
- Gestión de eventos multi-distancia
- Configuración de antenas
- Scanner RFID con filtrado inteligente
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from .event_manager import EventManager, RaceStatus
from dataclasses import dataclass

@dataclass
class ChipReading:
    """Lectura de chip con información de contexto"""
    chip_id: str
    distance_id: str
    antenna_id: int
    timestamp: datetime
    reading_type: str  # 'start', 'finish', 'checkpoint', 'start_finish'
    race_time: float   # Segundos desde inicio de la distancia
    category_start_time: datetime

@dataclass
class ParticipantStatus:
    """Estado de un participante"""
    chip_id: str
    distance_id: str
    status: str  # 'not_started', 'in_progress', 'finished'
    start_time: Optional[datetime] = None
    finish_time: Optional[datetime] = None
    total_time: Optional[float] = None
    checkpoints_passed: int = 0
    last_reading: Optional[ChipReading] = None

class IntegratedRaceTracker:
    """Tracker de carreras integrado con gestión de eventos"""
    
    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self.antenna_config: Dict[int, Dict] = {}  # antenna_id -> config
        self.chip_readings: Dict[str, List[ChipReading]] = {}
        self.participant_statuses: Dict[str, ParticipantStatus] = {}
        self.min_read_interval = 2.0  # segundos entre lecturas del mismo chip
        
    def set_antenna_config(self, antenna_config: Dict[int, Dict]):
        """Configurar roles de antenas"""
        self.antenna_config = antenna_config
        print(f"Configuración de antenas actualizada: {len(antenna_config)} antenas activas")
        
    def process_chip_reading(self, chip_id: str, antenna_id: int, timestamp: datetime) -> Optional[ChipReading]:
        """
        Procesar lectura de chip con filtrado inteligente
        Solo procesa chips de distancias activas
        """
        # 1. Verificar si el chip está registrado
        distance_id = self.event_manager.get_participant_category(chip_id)
        if not distance_id:
            print(f"Chip {chip_id} no está registrado en ninguna distancia")
            return None

        # 2. Verificar si la distancia está activa
        if distance_id not in self.event_manager.get_active_categories():
            print(f"Chip {chip_id} pertenece a distancia {distance_id} que no está activa")
            return None
            
        # 3. Verificar configuración de antena
        if antenna_id not in self.antenna_config:
            print(f"Antena {antenna_id} no está configurada")
            return None
            
        antenna_roles = self.antenna_config[antenna_id]
        if not antenna_roles.get('enabled', False):
            print(f"Antena {antenna_id} está deshabilitada")
            return None
            
        # 4. Verificar intervalo mínimo entre lecturas
        if not self._is_valid_reading_interval(chip_id, antenna_id, timestamp):
            print(f"Lectura de chip {chip_id} muy reciente, ignorando")
            return None
            
        # 5. Obtener tiempo de inicio de la distancia
        category_start_time = self.event_manager.distance_start_times.get(distance_id)
        if not category_start_time:
            print(f"Distancia {distance_id} no tiene tiempo de inicio")
            return None
            
        # 6. Calcular tiempo de carrera
        race_time = (timestamp - category_start_time).total_seconds()
        
        # 7. Determinar tipo de lectura
        reading_type = self._determine_reading_type(antenna_roles)
        
        # 8. Crear lectura
        reading = ChipReading(
            chip_id=chip_id,
            distance_id=distance_id,
            antenna_id=antenna_id,
            timestamp=timestamp,
            reading_type=reading_type,
            race_time=race_time,
            category_start_time=category_start_time
        )
        
        # 9. Almacenar lectura
        if chip_id not in self.chip_readings:
            self.chip_readings[chip_id] = []
        self.chip_readings[chip_id].append(reading)
        
        # 10. Actualizar estado del participante
        self._update_participant_status(reading)
        
        print(f"Lectura procesada: Chip {chip_id} en antena {antenna_id} ({reading_type}) - Tiempo: {race_time:.2f}s")
        return reading
        
    def _is_valid_reading_interval(self, chip_id: str, antenna_id: int, timestamp: datetime) -> bool:
        """Verificar si la lectura cumple con el intervalo mínimo"""
        if chip_id not in self.chip_readings:
            return True
            
        # Buscar última lectura en la misma antena
        last_reading_same_antenna = None
        for reading in reversed(self.chip_readings[chip_id]):
            if reading.antenna_id == antenna_id:
                last_reading_same_antenna = reading
                break
                
        if last_reading_same_antenna:
            time_diff = (timestamp - last_reading_same_antenna.timestamp).total_seconds()
            return time_diff >= self.min_read_interval
            
        return True
        
    def _determine_reading_type(self, antenna_roles: Dict) -> str:
        """Determinar tipo de lectura según configuración de antena"""
        if antenna_roles.get('start') and antenna_roles.get('finish'):
            return 'start_finish'
        elif antenna_roles.get('start'):
            return 'start'
        elif antenna_roles.get('finish'):
            return 'finish'
        elif antenna_roles.get('checkpoint'):
            return 'checkpoint'
        else:
            return 'unknown'
            
    def _update_participant_status(self, reading: ChipReading):
        """Actualizar estado del participante basado en la lectura"""
        chip_id = reading.chip_id
        
        # Obtener o crear estado del participante
        if chip_id not in self.participant_statuses:
            self.participant_statuses[chip_id] = ParticipantStatus(
                chip_id=chip_id,
                distance_id=reading.distance_id,
                status='not_started'
            )
            
        participant = self.participant_statuses[chip_id]
        participant.last_reading = reading
        
        # Analizar todas las lecturas para determinar estado
        all_readings = self.chip_readings.get(chip_id, [])
        start_readings = [r for r in all_readings if r.reading_type in ['start', 'start_finish']]
        finish_readings = [r for r in all_readings if r.reading_type in ['finish', 'start_finish']]
        checkpoint_readings = [r for r in all_readings if r.reading_type == 'checkpoint']
        
        # Actualizar checkpoints
        participant.checkpoints_passed = len(checkpoint_readings)
        
        # Determinar estado principal
        if start_readings:
            # Ha iniciado
            first_start = min(start_readings, key=lambda x: x.timestamp)
            participant.start_time = first_start.timestamp
            participant.status = 'in_progress'
            
            # Verificar si ha terminado
            if finish_readings:
                # Para antenas start_finish, el finish debe ser después del start
                valid_finish_readings = []
                for finish_reading in finish_readings:
                    if finish_reading.reading_type == 'start_finish':
                        # Para start_finish, debe ser después del primer start
                        if finish_reading.timestamp > first_start.timestamp:
                            valid_finish_readings.append(finish_reading)
                    else:
                        # Para antenas finish dedicadas, cualquier lectura es válida
                        valid_finish_readings.append(finish_reading)
                        
                if valid_finish_readings:
                    first_finish = min(valid_finish_readings, key=lambda x: x.timestamp)
                    participant.finish_time = first_finish.timestamp
                    participant.total_time = (first_finish.timestamp - first_start.timestamp).total_seconds()
                    participant.status = 'finished'
                    
    def get_participant_status(self, chip_id: str) -> Optional[ParticipantStatus]:
        """Obtener estado de un participante"""
        return self.participant_statuses.get(chip_id)
        
    def get_category_results(self, distance_id: str) -> List[ParticipantStatus]:
        """Obtener resultados de una distancia ordenados por tiempo"""
        category_participants = [
            status for status in self.participant_statuses.values()
            if status.distance_id == distance_id
        ]
        
        # Separar por estado
        finished = [p for p in category_participants if p.status == 'finished' and p.total_time]
        in_progress = [p for p in category_participants if p.status == 'in_progress']
        not_started = [p for p in category_participants if p.status == 'not_started']
        
        # Ordenar finalizados por tiempo
        finished.sort(key=lambda x: x.total_time)
        
        # Ordenar en progreso por tiempo de inicio
        in_progress.sort(key=lambda x: x.start_time or datetime.min)
        
        return finished + in_progress + not_started
        
    def get_active_participants_count(self) -> Dict[str, int]:
        """Obtener conteo de participantes activos por distancia"""
        counts = {}
        for distance_id in self.event_manager.get_active_categories():
            active_count = sum(1 for status in self.participant_statuses.values()
                             if status.distance_id == distance_id and status.status == 'in_progress')
            counts[distance_id] = active_count
        return counts
        
    def get_system_status(self) -> Dict:
        """Obtener estado completo del sistema"""
        active_categories = self.event_manager.get_active_categories()
        active_participants = self.get_active_participants_count()
        
        return {
            'active_categories': active_categories,
            'active_participants': active_participants,
            'total_readings': sum(len(readings) for readings in self.chip_readings.values()),
            'configured_antennas': len([ant for ant in self.antenna_config.values() if ant.get('enabled')]),
            'registered_participants': len(self.event_manager.participants)
        }