"""
Clase base para todos los tabs
src/gui/tabs/base_tab.py
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
import logging

logger = logging.getLogger(__name__)


class BaseTab(QWidget):
    """Clase base para todos los tabs de la aplicación"""
    
    def __init__(self, signals=None, parent=None):
        super().__init__(parent)
        self.signals = signals
        self.layout = QVBoxLayout(self)
        
        # Setup UI siempre
        self.setup_ui()
        
        # Conectar señales solo si existen
        if self.signals:
            try:
                self.connect_signals()
            except Exception as e:
                logger.error(f"Error conectando señales en {self.__class__.__name__}: {e}")
    
    def setup_ui(self):
        """Sobrescribir en subclases para crear UI"""
        pass
    
    def connect_signals(self):
        """Sobrescribir en subclases para conectar señales"""
        pass
    
    def log(self, message):
        """Helper para logging"""
        logger.info(f"[{self.__class__.__name__}] {message}")
        print(f"[{self.__class__.__name__}] {message}")
    
    def safe_connect(self, signal_name, slot):
        """Helper para conectar señales de forma segura"""
        if not self.signals:
            return False
        
        if hasattr(self.signals, signal_name):
            signal = getattr(self.signals, signal_name)
            try:
                signal.connect(slot)
                return True
            except Exception as e:
                logger.error(f"Error conectando {signal_name}: {e}")
                return False
        else:
            logger.warning(f"Señal {signal_name} no existe en AppSignals")
            return False