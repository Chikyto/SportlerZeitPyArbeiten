"""
Sistema centralizado de señales para comunicación entre componentes
src/utils/signals.py
"""

from PyQt6.QtCore import QObject, pyqtSignal


class AppSignals(QObject):
    """Sistema centralizado de señales para toda la aplicación"""
    
    # ===== SEÑALES DE CONEXIÓN =====
    connection_status_changed = pyqtSignal(bool, str)
    connection_established = pyqtSignal()
    connection_lost = pyqtSignal()
    scanner_connected = pyqtSignal(bool)
    
    # ===== SEÑALES DE LOGGING =====
    log_message = pyqtSignal(str, str)  # ⭐ mensaje, level
    
    # ===== SEÑALES DE DETECCIÓN DE TAGS =====
    tag_detected = pyqtSignal(dict)
    tags_batch_detected = pyqtSignal(list)
    
    # ===== SEÑALES DE CATEGORÍAS =====
    category_created = pyqtSignal(str)
    category_started = pyqtSignal(str)
    category_finished = pyqtSignal(str)
    category_updated = pyqtSignal(str)
    
    # ===== SEÑALES MULTI-ANTENA =====
    scanner_ready = pyqtSignal(object)
    antenna_changed = pyqtSignal(int)
    
    # Detecciones por rol de antena
    start_detected = pyqtSignal(str, str)
    finish_detected = pyqtSignal(str, str)
    checkpoint_detected = pyqtSignal(str, int, str)
    
    # Estado de scanning
    scanning_started = pyqtSignal()
    scanning_stopped = pyqtSignal()
    scan_progress = pyqtSignal(int)
    auto_start_scanning = pyqtSignal()  # 🔥 Nueva: Auto-iniciar escaneo cuando se inician distancias
    
    # Errores de scanning
    scanner_error = pyqtSignal(str)
    antenna_error = pyqtSignal(int, str)
    
    # ===== SEÑALES DE PARTICIPANTES =====
    participant_registered = pyqtSignal(dict)
    participant_updated = pyqtSignal(str)
    
    # ===== SEÑALES DE RESULTADOS =====
    result_calculated = pyqtSignal(dict)
    results_exported = pyqtSignal(str)

    # ===== SEÑALES DE DETECCIÓN CON ATLETA RESUELTO =====
    # tag_id, athlete_name, distance_name, bib_number
    athlete_tag_resolved = pyqtSignal(str, str, str, str)
    # athlete_name, distance_name, formatted_time
    athlete_finished = pyqtSignal(str, str, str)

    # Emitida cuando se carga un .szconfig: (event_name, event_id)
    backend_config_loaded = pyqtSignal(str, str)


# Singleton para uso global
_app_signals_instance = None


def get_app_signals():
    """Obtiene la instancia singleton de AppSignals"""
    global _app_signals_instance
    if _app_signals_instance is None:
        _app_signals_instance = AppSignals()
    return _app_signals_instance