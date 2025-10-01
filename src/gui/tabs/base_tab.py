"""
Clase base para todas las pestañas de la aplicación
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSlot
from datetime import datetime
from ...utils.signals import get_app_signals


class BaseTab(QWidget):
    """Clase base para pestañas con funcionalidad común"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.signals = get_app_signals()
        self.layout = QVBoxLayout(self)
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Configurar UI - debe ser implementado por subclases"""
        raise NotImplementedError("Subclasses must implement setup_ui()")
    
    def connect_signals(self):
        """Conectar señales - puede ser sobrescrito por subclases"""
        pass
    
    def get_timestamp(self):
        """Obtener timestamp formateado"""
        return datetime.now().strftime('%H:%M:%S')
    
    def log(self, message, level='info'):
        """Emitir mensaje de log"""
        self.signals.log_message.emit(message, level)
    
    @pyqtSlot()
    def on_tab_activated(self):
        """Llamado cuando el tab es activado - puede ser sobrescrito"""
        pass
    
    @pyqtSlot()
    def on_tab_deactivated(self):
        """Llamado cuando el tab es desactivado - puede ser sobrescrito"""
        pass