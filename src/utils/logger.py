"""
Sistema de logging centralizado para el sistema de cronometraje
"""

import logging
import sys
from typing import Optional

# Cache de loggers
_loggers = {}

def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado
    
    Args:
        name: Nombre del logger (generalmente __name__)
        
    Returns:
        Logger configurado
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    
    return _loggers[name]

class ColoredFormatter(logging.Formatter):
    """Formatter con colores para consola"""
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        """Formatea el registro con colores"""
        if sys.stdout.isatty():  # Solo colorear si es terminal
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            
            # Colorear solo el nivel
            record.levelname = f"{color}{record.levelname}{reset}"
        
        return super().format(record)

class TimingSystemLogger:
    """Logger especializado para el sistema de cronometraje"""
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
        self.name = name
    
    def detection(self, chip_id: str, athlete_name: str, time_str: str, detection_type: str = "DETECTION"):
        """Log específico para detecciones RFID"""
        self.logger.info(f"[{detection_type}] Chip: {chip_id} | Atleta: {athlete_name} | Tiempo: {time_str}")
    
    def scanner_status(self, status: str, details: str = ""):
        """Log para estados del scanner"""
        self.logger.info(f"[SCANNER] {status} {details}".strip())
    
    def firebase_status(self, status: str, details: str = ""):
        """Log para estados de Firebase"""
        self.logger.info(f"[FIREBASE] {status} {details}".strip())
    
    def race_event(self, event: str, details: str = ""):
        """Log para eventos de carrera"""
        self.logger.info(f"[RACE] {event} {details}".strip())
    
    def system_error(self, component: str, error: str, exception: Exception = None):
        """Log para errores del sistema"""
        if exception:
            self.logger.error(f"[ERROR] {component}: {error}", exc_info=True)
        else:
            self.logger.error(f"[ERROR] {component}: {error}")
    
    def performance(self, operation: str, duration_ms: float, details: str = ""):
        """Log para métricas de rendimiento"""
        self.logger.debug(f"[PERF] {operation}: {duration_ms:.1f}ms {details}".strip())

def get_timing_logger(name: str) -> TimingSystemLogger:
    """
    Obtiene un logger especializado para cronometraje
    
    Args:
        name: Nombre del logger
        
    Returns:
        TimingSystemLogger configurado
    """
    return TimingSystemLogger(name)

# Funciones de conveniencia
def log_detection(chip_id: str, athlete_name: str, time_str: str, detection_type: str = "DETECTION"):
    """Log de detección usando logger por defecto"""
    logger = get_timing_logger("detection")
    logger.detection(chip_id, athlete_name, time_str, detection_type)

def log_system_start():
    """Log de inicio del sistema"""
    logger = get_logger("system")
    logger.info("="*60)
    logger.info("Sistema de Cronometraje YR8900 INICIADO")
    logger.info("="*60)

def log_system_stop():
    """Log de parada del sistema"""
    logger = get_logger("system")
    logger.info("="*60)
    logger.info("Sistema de Cronometraje YR8900 DETENIDO")
    logger.info("="*60)

def log_race_start(race_name: str, total_athletes: int):
    """Log de inicio de carrera"""
    logger = get_timing_logger("race")
    logger.race_event("INICIO", f"Carrera: {race_name} | Atletas: {total_athletes}")

def log_race_finish(race_name: str, finished_athletes: int, total_time: str):
    """Log de finalización de carrera"""
    logger = get_timing_logger("race")
    logger.race_event("FIN", f"Carrera: {race_name} | Finalizados: {finished_athletes} | Duración: {total_time}")