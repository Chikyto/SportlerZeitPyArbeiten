"""
Sistema de gestión de eventos - Versión simplificada
"""

from dataclasses import dataclass
from datetime import datetime, time
from typing import Dict, List, Optional
from enum import Enum

class RaceStatus(Enum):
    """Estados de una carrera"""
    PENDING = "pending"
    ACTIVE = "active"
    FINISHED = "finished"
    CANCELLED = "cancelled"

@dataclass
class RaceCategory:
    """Definición de una distancia de carrera"""
    id: str
    name: str
    distance: str
    start_time: time
    max_duration_hours: int
    description: str
    chip_prefix: str = ""
    
    def __post_init__(self):
        if not self.chip_prefix:
            self.chip_prefix = self.id.upper()

class EventManager:
    """Gestor de eventos simplificado"""
    
    def __init__(self):
        self.event_name = "Evento RFID"
        self.event_date = datetime.now().date()
        self.categories: Dict[str, RaceCategory] = {}
        self.participants: Dict[str, str] = {}  # chip_id -> category_id
        self.race_states: Dict[str, RaceStatus] = {}
        self.category_start_times: Dict[str, Optional[datetime]] = {}
        
    def add_category(self, category: RaceCategory):
        """Agregar distancia al evento"""
        self.categories[category.id] = category
        self.race_states[category.id] = RaceStatus.PENDING
        self.category_start_times[category.id] = None
        
    def remove_category(self, category_id: str):
        """Eliminar distancia del evento"""
        if category_id in self.categories:
            del self.categories[category_id]
            del self.race_states[category_id]
            del self.category_start_times[category_id]
            
            # Eliminar participantes de esta distancia
            to_remove = [chip_id for chip_id, cat_id in self.participants.items() 
                        if cat_id == category_id]
            for chip_id in to_remove:
                del self.participants[chip_id]
    
    def register_participant(self, chip_id: str, category_id: str, participant_name: str = ""):
        """Registrar participante en una distancia"""
        if category_id not in self.categories:
            raise ValueError(f"Distancia {category_id} no existe")
        self.participants[chip_id] = category_id
    
    def get_participant_category(self, chip_id: str) -> Optional[str]:
        """Obtener distancia de un chip"""
        return self.participants.get(chip_id)
    
    def start_category(self, category_id: str) -> bool:
        """Iniciar una distancia específica"""
        if category_id not in self.categories:
            return False
        self.race_states[category_id] = RaceStatus.ACTIVE
        self.category_start_times[category_id] = datetime.now()
        return True
    
    def finish_category(self, category_id: str) -> bool:
        """Finalizar una distancia específica"""
        if category_id not in self.categories:
            return False
        self.race_states[category_id] = RaceStatus.FINISHED
        return True
    
    def get_active_categories(self) -> List[str]:
        """Obtener distancias actualmente activas"""
        return [cat_id for cat_id, status in self.race_states.items() 
                if status == RaceStatus.ACTIVE]
    
    def get_category_info(self, category_id: str) -> Dict:
        """Obtener información completa de una distancia"""
        if category_id not in self.categories:
            return {}
            
        category = self.categories[category_id]
        status = self.race_states[category_id]
        start_time = self.category_start_times[category_id]
        
        # Contar participantes
        participant_count = sum(1 for cat_id in self.participants.values() 
                              if cat_id == category_id)
        
        return {
            'category': category,
            'status': status,
            'actual_start_time': start_time,
            'participant_count': participant_count,
            'scheduled_start': category.start_time,
            'is_active': status == RaceStatus.ACTIVE,
            'is_finished': status == RaceStatus.FINISHED
        }
    
    def get_categories_by_time(self) -> List[str]:
        """Obtener distancias ordenadas por hora de largada"""
        return sorted(self.categories.keys(), 
                     key=lambda cat_id: self.categories[cat_id].start_time)