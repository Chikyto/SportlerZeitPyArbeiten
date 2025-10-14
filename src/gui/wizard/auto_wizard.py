"""
Wizard automático con detección inteligente - VERSIÓN CORREGIDA
"""
import logging
from PyQt6.QtWidgets import QWizard, QMessageBox, QWizardPage, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import QTimer, Qt, pyqtSignal

from config import SystemConfig
from hardware import ReaderManager
from .antenna_config_page import AntennaConfigurationPage
from .summary_page import SummaryPage

logger = logging.getLogger(__name__)


class AutoConnectPage(QWizardPage):
    """Página de auto-conexión invisible"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard_ref = wizard
        self.connection_attempted = False
        
        self.setTitle("Conectando al sistema...")
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Estableciendo conexión con el lector RFID...")
        layout.addWidget(self.status_label)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Modo indeterminado
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
    
    def initializePage(self):
        """Intentar conexión automática al entrar"""
        if not self.connection_attempted:
            self.connection_attempted = True
            QTimer.singleShot(500, self.attempt_connection)
    
    def attempt_connection(self):
        """Intentar conectar automáticamente"""
        wizard = self.wizard()
        
        try:
            self.status_label.setText("Conectando a 192.168.0.178:4001...")
            
            if wizard.reader_manager.test_connection():
                self.status_label.setText("✓ Conexión exitosa")
                self.progress.setRange(0, 100)
                self.progress.setValue(100)
                
                if hasattr(wizard.reader_manager, 'firmware_version'):
                    self.status_label.setText(
                        f"✓ Conexión exitosa - Firmware v{wizard.reader_manager.firmware_version}"
                    )
                
                QTimer.singleShot(500, wizard.next)
            else:
                self.connection_failed()
                
        except Exception as e:
            logger.error(f"Error en auto-conexión: {e}")
            self.connection_failed()
    
    def connection_failed(self):
        """Manejar fallo de conexión"""
        self.status_label.setText("✗ No se pudo conectar automáticamente")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        
        reply = QMessageBox.question(
            self,
            "Conexión Fallida",
            "No se pudo conectar al lector RFID en la dirección por defecto.\n\n"
            "¿Desea configurar manualmente la conexión?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show_manual_config()
        else:
            self.wizard().reject()
    
    def show_manual_config(self):
        """Mostrar configuración manual"""
        from PyQt6.QtWidgets import QDialog, QLineEdit, QSpinBox, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuración Manual")
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("Host:"))
        host_input = QLineEdit("192.168.0.178")
        layout.addWidget(host_input)
        
        layout.addWidget(QLabel("Puerto:"))
        port_input = QSpinBox()
        port_input.setRange(1, 65535)
        port_input.setValue(4001)
        layout.addWidget(port_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            wizard = self.wizard()
            wizard.config.reader.host = host_input.text()
            wizard.config.reader.port = port_input.value()
            
            self.connection_attempted = False
            self.attempt_connection()


class AutoDetectionPage(QWizardPage):
    """Página de auto-detección de antenas"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard_ref = wizard
        self.detection_results = {}
        self.detection_completed = False
        
        self.setTitle("Detectando antenas...")
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Escaneando puertos de antenas...")
        layout.addWidget(self.status_label)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        self.details_label = QLabel("")
        layout.addWidget(self.details_label)
        
        self.setLayout(layout)
    
    def initializePage(self):
        """Iniciar detección automática"""
        if not self.detection_completed:
            QTimer.singleShot(300, self.start_detection)
    
    def start_detection(self):
        """Escanear antenas automáticamente"""
        wizard = self.wizard()
        
        self.progress.setRange(0, 8)
        
        for port in range(1, 9):
            self.status_label.setText(f"Escaneando puerto {port}/8...")
            self.progress.setValue(port)
            
            try:
                is_connected, return_loss = \
                    wizard.reader_manager.antenna_detector.detect_physical_antenna(port)
                self.detection_results[port] = (is_connected, return_loss)
                
                if is_connected:
                    self.details_label.setText(
                        self.details_label.text() + 
                        f"\n✓ Puerto {port}: Conectada ({return_loss} dB)"
                    )
            except Exception as e:
                logger.error(f"Error detectando puerto {port}: {e}")
                self.detection_results[port] = (False, 0)
        
        self.detection_completed = True
        connected_count = sum(1 for conn, _ in self.detection_results.values() if conn)
        
        self.status_label.setText(f"✓ Detección completada: {connected_count} antenas encontradas")
        
        if connected_count > 0:
            QTimer.singleShot(1000, wizard.next)
        else:
            QMessageBox.warning(
                self,
                "Sin antenas",
                "No se detectaron antenas conectadas.\n"
                "Verifique las conexiones físicas."
            )
    
    def isComplete(self):
        """Página completa si hay antenas detectadas"""
        if not self.detection_completed:
            return False
        connected_count = sum(1 for conn, _ in self.detection_results.values() if conn)
        return connected_count > 0


class AutoConfigurationWizard(QWizard):
    """Wizard automático optimizado"""
    
    # 🔥 SEÑAL CRÍTICA: emite configuración al finalizar
    configuration_completed = pyqtSignal(dict)
    
    def __init__(self, config: SystemConfig = None, parent=None):
        super().__init__(parent)
        
        self.config = config or SystemConfig()
        self.reader_manager = ReaderManager(self.config.reader)
        
        self.setWindowTitle("Configuración Rápida - Sistema RFID")
        self.resize(700, 500)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        
        # Páginas del wizard optimizado
        self.auto_connect_page = AutoConnectPage(self)
        self.auto_detection_page = AutoDetectionPage(self)
        self.antenna_config_page = AntennaConfigurationPage(self)
        self.summary_page = SummaryPage(self)
        
        self.addPage(self.auto_connect_page)
        self.addPage(self.auto_detection_page)
        self.addPage(self.antenna_config_page)
        self.addPage(self.summary_page)
        
        logger.info("Wizard automático inicializado")
    
    def accept(self):
        """Guardar configuración al completar"""
        try:
            # 1. Obtener configuración de las páginas
            config_page = self.page(2)
            if config_page and hasattr(config_page, 'get_configuration'):
                antenna_config = config_page.get_configuration()
                self.config.antennas = antenna_config
                
                # 2. Guardar a archivo
                filename = "timing_system_config.json"
                if self.config.save_to_file(filename):
                    logger.info(f"✅ Configuración guardada en {filename}")
                
                # 3. 🔥 EMITIR SEÑAL con configuración completa
                full_config = self.get_configuration()
                logger.info(f"🔔 Emitiendo configuración: {full_config}")
                self.configuration_completed.emit(full_config)
                
                logger.info("✅ Configuración del wizard completada")
            
            super().accept()
            
        except Exception as e:
            logger.error(f"❌ Error finalizando wizard: {e}")
            QMessageBox.critical(self, "Error", f"Error al finalizar:\n{str(e)}")
    
    def reject(self):
        """Cancelar wizard"""
        reply = QMessageBox.question(
            self,
            "Cancelar",
            "¿Está seguro que desea cancelar?\n"
            "La aplicación se cerrará.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            super().reject()
    
    def get_configuration(self):
        """
        🔥 CRÍTICO: Obtener configuración en formato estandarizado
        Usar SIEMPRE puertos 1-8 como keys (no índices 0-7)
        """
        config = {
            'connection': {
                'host': getattr(self.config.reader, 'host', '192.168.0.178'),
                'port': getattr(self.config.reader, 'port', 4001),
                'verified': True
            },
            'power_dbm': 30,  # Potencia por defecto
            'antennas': {}
        }
        
        # Obtener configuración de antenas
        if hasattr(self.antenna_config_page, 'get_configuration'):
            antenna_configs = self.antenna_config_page.get_configuration()
            
            for port, antenna_config in antenna_configs.items():
                # port ya viene como 1-8, NO convertir a índice
                functions = getattr(antenna_config, 'multiple_functions', [])
                description = getattr(antenna_config, 'description', f'Antena puerto {port}')
                
                # Extraer nombre limpio
                if ':' in description:
                    name = description.split(':', 1)[1].strip()
                else:
                    name = f'Antena {port}'
                
                # 🔥 KEY = puerto (1-8), NO índice (0-7)
                config['antennas'][port] = {
                    'enabled': True,
                    'name': name,
                    'description': description,
                    'start': 'largada' in functions,
                    'finish': 'llegada' in functions,
                    'checkpoint': 'checkpoint' in functions,
                    'power_level': getattr(antenna_config, 'power_level', 25),
                    'functions': functions
                }
        
        logger.info(f"📡 Configuración generada: {config['antennas'].keys()}")
        return config