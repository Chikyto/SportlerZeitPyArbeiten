"""
Configuración para carreras con múltiples antenas
Define roles de antenas y lógica de cronometraje
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class AntennaRole(Enum):
    """Roles que puede cumplir una antena"""
    START = "start"          # Línea de largada
    FINISH = "finish"        # Línea de meta
    CHECKPOINT = "checkpoint" # Punto intermedio
    DISABLED = "disabled"    # Antena deshabilitada

@dataclass
class AntennaConfig:
    """Configuración de una antena individual"""
    id: int
    role: AntennaRole
    name: str
    description: str
    enabled: bool = True

class RaceConfig:
    """Configuración de carrera con múltiples antenas"""
    
    def __init__(self):
        # Configuración por defecto para 4 antenas
        self.antennas = {
            0: AntennaConfig(0, AntennaRole.START, "Largada", "Línea de largada"),
            1: AntennaConfig(1, AntennaRole.CHECKPOINT, "Checkpoint 1", "Primer control"),
            2: AntennaConfig(2, AntennaRole.CHECKPOINT, "Checkpoint 2", "Segundo control"),
            3: AntennaConfig(3, AntennaRole.FINISH, "Meta", "Línea de meta")
        }
        
        # Tiempo mínimo entre lecturas del mismo chip (evitar falsos duplicados)
        self.min_read_interval = timedelta(seconds=2)
        
        # Tiempo máximo para considerar una lectura válida después del inicio
        self.max_race_time = timedelta(hours=6)
        
    def get_antenna_by_role(self, role: AntennaRole) -> List[AntennaConfig]:
        """Obtiene antenas por rol"""
        return [ant for ant in self.antennas.values() 
                if ant.role == role and ant.enabled]
    
    def is_start_antenna(self, antenna_id: int) -> bool:
        """Verifica si una antena es de largada"""
        antenna = self.antennas.get(antenna_id)
        return antenna and antenna.role == AntennaRole.START and antenna.enabled
    
    def is_finish_antenna(self, antenna_id: int) -> bool:
        """Verifica si una antena es de meta"""
        antenna = self.antennas.get(antenna_id)
        return antenna and antenna.role == AntennaRole.FINISH and antenna.enabled
    
    def get_antenna_name(self, antenna_id: int) -> str:
        """Obtiene el nombre de una antena"""
        antenna = self.antennas.get(antenna_id)
        return antenna.name if antenna else f"Antena {antenna_id}"

@dataclass
class ChipReading:
    """Registro de una lectura de chip"""
    chip_id: str
    antenna_id: int
    timestamp: datetime
    antenna_role: AntennaRole
    race_time: Optional[float] = None  # Tiempo desde inicio de carrera
    
class RaceTracker:
    """Rastreador de estado de carrera para cada chip"""
    
    def __init__(self, race_config: RaceConfig):
        self.config = race_config
        self.chip_states: Dict[str, List[ChipReading]] = {}
        self.race_start_time: Optional[datetime] = None
        self.race_active = False
        
    def start_race(self):
        """Iniciar carrera"""
        self.race_start_time = datetime.now()
        self.race_active = True
        self.chip_states.clear()
        
    def stop_race(self):
        """Finalizar carrera"""
        self.race_active = False
        
    def process_chip_reading(self, chip_id: str, antenna_id: int, timestamp: datetime) -> Optional[ChipReading]:
        """
        Procesa una lectura de chip y determina si es válida
        Retorna ChipReading si es válida, None si debe ignorarse
        """
        if not self.race_active or not self.race_start_time:
            return None
            
        antenna = self.config.antennas.get(antenna_id)
        if not antenna or not antenna.enabled:
            return None
            
        # Verificar si ya tenemos lecturas de este chip
        chip_history = self.chip_states.get(chip_id, [])
        
        # Verificar intervalo mínimo entre lecturas en la misma antena
        last_reading_same_antenna = None
        for reading in reversed(chip_history):
            if reading.antenna_id == antenna_id:
                last_reading_same_antenna = reading
                break
                
        if last_reading_same_antenna:
            time_diff = timestamp - last_reading_same_antenna.timestamp
            if time_diff < self.config.min_read_interval:
                return None  # Muy pronto, probablemente duplicado
        
        # Calcular tiempo de carrera
        race_time = (timestamp - self.race_start_time).total_seconds()
        
        # Crear registro de lectura
        reading = ChipReading(
            chip_id=chip_id,
            antenna_id=antenna_id, 
            timestamp=timestamp,
            antenna_role=antenna.role,
            race_time=race_time
        )
        
        # Agregar a historial
        if chip_id not in self.chip_states:
            self.chip_states[chip_id] = []
        self.chip_states[chip_id].append(reading)
        
        return reading
        
    def get_chip_status(self, chip_id: str) -> Dict:
        """Obtiene el estado actual de un chip"""
        if chip_id not in self.chip_states:
            return {"status": "not_started", "readings": []}
            
        readings = self.chip_states[chip_id]
        start_readings = [r for r in readings if r.antenna_role == AntennaRole.START]
        finish_readings = [r for r in readings if r.antenna_role == AntennaRole.FINISH]
        checkpoint_readings = [r for r in readings if r.antenna_role == AntennaRole.CHECKPOINT]
        
        status = "not_started"
        total_time = None
        
        if start_readings and finish_readings:
            status = "finished"
            # Calcular tiempo total (primera largada a primera meta)
            start_time = min(start_readings, key=lambda x: x.timestamp)
            finish_time = min(finish_readings, key=lambda x: x.timestamp)
            total_time = (finish_time.timestamp - start_time.timestamp).total_seconds()
        elif start_readings:
            status = "in_progress"
        
        return {
            "status": status,
            "total_time": total_time,
            "start_time": start_readings[0].timestamp if start_readings else None,
            "finish_time": finish_readings[0].timestamp if finish_readings else None,
            "checkpoints": len(checkpoint_readings),
            "readings": readings
        }
        
    def get_race_results(self) -> List[Dict]:
        """Obtiene resultados de carrera ordenados por tiempo"""
        results = []
        
        for chip_id in self.chip_states.keys():
            status = self.get_chip_status(chip_id)
            if status["status"] == "finished" and status["total_time"]:
                results.append({
                    "chip_id": chip_id,
                    "total_time": status["total_time"],
                    "start_time": status["start_time"],
                    "finish_time": status["finish_time"],
                    "checkpoints": status["checkpoints"]
                })
        
        # Ordenar por tiempo total
        results.sort(key=lambda x: x["total_time"])
        
        # Agregar posiciones
        for i, result in enumerate(results):
            result["position"] = i + 1
            
        return results