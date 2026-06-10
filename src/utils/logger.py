"""
Sistema de logging centralizado para el sistema de cronometraje
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

# Cache de loggers
_loggers = {}


def setup_logging(console_level: int = logging.WARNING,
                  file_level: int = logging.INFO,
                  log_file: str = "timing_system.log",
                  max_bytes: int = 5 * 1024 * 1024,
                  backup_count: int = 5) -> None:
    """
    Configurar el logging de toda la aplicación.

    Filosofía:
    - Consola: solo WARNING y ERROR → los problemas se ven de inmediato,
      sin perderse entre miles de líneas de detalle.
    - Archivo con rotación: todo el detalle (INFO/DEBUG) queda en
      timing_system.log, acotado a max_bytes × (backup_count + 1)
      para que nunca crezca infinito.

    Args:
        console_level: Nivel mínimo para la consola (WARNING por defecto;
                       usar logging.INFO/DEBUG con --verbose)
        file_level: Nivel mínimo para el archivo
        log_file: Ruta del archivo de log
        max_bytes: Tamaño máximo de cada archivo antes de rotar
        backup_count: Cantidad de archivos rotados a conservar
    """
    root = logging.getLogger()
    root.setLevel(min(console_level, file_level))
    root.handlers.clear()

    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(ColoredFormatter(fmt))
    root.addHandler(console_handler)

    root.info(
        f"Logging configurado: consola={logging.getLevelName(console_level)}, "
        f"archivo={log_file} ({logging.getLevelName(file_level)}, "
        f"rotación {max_bytes // (1024 * 1024)}MB × {backup_count})"
    )

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