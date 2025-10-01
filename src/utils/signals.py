"""
Sistema de señales centralizado para comunicación entre componentes
"""
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime


class AppSignals(QObject):
    """Señales globales de la aplicación"""
    
    # Señales de conexión
    scanner_connected = pyqtSignal(bool)  # True si conectado
    scanner_status_changed = pyqtSignal(str)  # Mensaje de estado
    
    # Señales de detección de chips
    tag_detected = pyqtSignal(dict)  # {number, antenna, timestamp, epc_hex}
    tags_cleared = pyqtSignal()
    
    # Señales de configuración de antenas
    antenna_config_applied = pyqtSignal(dict)  # {antenna_id: config}
    
    # Señales de eventos/categorías
    category_created = pyqtSignal(str)  # category_id
    category_started = pyqtSignal(str)  # category_id
    category_finished = pyqtSignal(str)  # category_id
    participant_registered = pyqtSignal(str, str)  # chip_number, category_id
    
    # Señales de carrera
    race_status_changed = pyqtSignal(dict)  # {status, timestamp, data}
    participant_status_updated = pyqtSignal(str, dict)  # chip_number, status_data
    
    # Señales de logging
    log_message = pyqtSignal(str, str)  # message, level (info/warning/error)
    
    # Señales de base de datos
    data_exported = pyqtSignal(str)  # filepath
    firebase_status_changed = pyqtSignal(bool)  # connected


# Instancia global singleton
_app_signals = None


def get_app_signals() -> AppSignals:
    """Obtener instancia singleton de señales de aplicación"""
    global _app_signals
    if _app_signals is None:
        _app_signals = AppSignals()
    return _app_signals