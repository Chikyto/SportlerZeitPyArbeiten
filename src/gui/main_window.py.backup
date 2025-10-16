"""
Ventana principal de la aplicación RFID Athletics Timer - VERSIÓN CORREGIDA
Arquitectura modular con separación de responsabilidades
"""
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QTabWidget, QLabel, QMessageBox)
from PyQt6.QtCore import pyqtSlot, Qt

from src.utils.signals import AppSignals
from ..core.advanced_scanner import AdvancedYR8900Scanner
from ..core.integrated_race_tracker import IntegratedRaceTracker
from src.utils.signals import get_app_signals

# Importar tabs
from .tabs import DetectionTab, ConfigurationTab
from .widgets.event_config_widget import EventConfigWidget
from .widgets.race_monitoring_widget import RaceMonitoringWidget

logger = logging.getLogger(__name__)    

class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación
    
    Responsabilidades:
    - Crear y organizar los tabs
    - Coordinar la comunicación entre componentes vía signals
    - Gestionar el ciclo de vida de la aplicación
    """
    
    def __init__(self, wizard_config=None):
        super().__init__()
        
        # 🔥 IMPORTANTE: Normalizar wizard_config al recibirlo
        self.wizard_config = self._normalize_config(wizard_config)
        self.signals = AppSignals()
        self.scanner = None
        
        self.setWindowTitle("RFID Athletics Timer")
        self.setMinimumSize(1200, 800)
        
        # 🔥 ORDEN CRÍTICO:
        # 1. Crear UI (tabs)
        self.setup_ui()
        
        # 2. Configurar scanner
        self.setup_scanner()
        
        # 3. 🔥 APLICAR CONFIGURACIÓN A LOS TABS
        self.apply_config_to_tabs()
        
        # 4. Conectar señales
        self.connect_signals()
    
    def _normalize_config(self, config):
        """
        🔥 CRÍTICO: Normalizar configuración para asegurar tipos correctos
        Convierte keys de antenas de string a int si es necesario
        """
        if not config:
            return config
        
        logger.info("=" * 80)
        logger.info("🔧 NORMALIZANDO CONFIGURACIÓN")
        logger.info("=" * 80)
        
        # Normalizar keys de antennas a int
        if 'antennas' in config:
            antennas_normalized = {}
            for key, value in config['antennas'].items():
                # Convertir key a int
                port_int = int(key) if isinstance(key, str) else key
                antennas_normalized[port_int] = value
                
                logger.info(f"  Puerto {key} ({type(key).__name__}) → {port_int} (int)")
            
            config['antennas'] = antennas_normalized
            logger.info(f"✅ Antenas normalizadas: {list(antennas_normalized.keys())}")
        
        logger.info("=" * 80)
        return config
    
    def setup_ui(self):
        """Configurar interfaz principal"""
        self.setWindowTitle("RFID Athletics Timer - Sistema de Control")
        self.setGeometry(100, 100, 1000, 750)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        
        # Sistema de pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(self.tab_widget)
        
        # Crear pestañas
        self.create_tabs()
        
        # Barra de estado
        self.status_label = QLabel("Aplicación iniciada")
        layout.addWidget(self.status_label)
    
    def setup_scanner(self):
        """Configura scanner con datos del wizard"""
        if not self.wizard_config:
            logger.warning("No hay configuración del wizard disponible")
            self.signals.connection_status_changed.emit(False, "Sin configuración")
            return
        
        try:
            # Obtener parámetros de conexión
            conn = self.wizard_config.get('connection', {})
            host = conn.get('host', '192.168.0.178')
            port = conn.get('port', 4001)
            
            logger.info(f"Creando scanner: {host}:{port}")
            
            # Crear scanner con parámetros del wizard
            from src.core.advanced_scanner import AdvancedYR8900Scanner
            self.scanner = AdvancedYR8900Scanner(host, port)
            
            # Conectar al lector
            if not self.scanner.connect():
                logger.error("No se pudo conectar al scanner")
                self.signals.connection_status_changed.emit(
                    False, 
                    "Error de conexión al lector"
                )
                return
            
            # 🔥 Configurar antenas habilitadas (keys ya son int gracias a normalize)
            antennas_config = self.wizard_config.get('antennas', {})
            enabled_ports = [
                port for port, config in antennas_config.items()
                if config.get('enabled', False)
            ]
            
            logger.info(f"📡 Antenas habilitadas: {enabled_ports}")
            self.scanner.available_antennas = enabled_ports
      
            # Configurar potencia si está en config
            power = self.wizard_config.get('power_dbm')
            if power:
                logger.info(f"⚡ Configurando potencia: {power} dBm")
                self.scanner.set_output_power(power)
            
            # Emitir señal de scanner listo
            self.signals.scanner_ready.emit(self.scanner)
            self.signals.connection_status_changed.emit(
                True, 
                f"Conectado - {len(enabled_ports)} antenas activas"
            )
            
            logger.info("✓ Scanner configurado y listo")
            
        except Exception as e:
            logger.error(f"❌ Error configurando scanner: {e}")
            import traceback
            traceback.print_exc()
            self.signals.connection_status_changed.emit(False, str(e))
    
    def apply_config_to_tabs(self):
        """
        🔥 MÉTODO CRÍTICO: Aplicar configuración del wizard a todos los tabs
        Este método se llama DESPUÉS de crear los tabs y el scanner
        """
        if not self.wizard_config:
            logger.warning("⚠️  No hay configuración para aplicar a los tabs")
            return
        
        logger.info("=" * 80)
        logger.info("🔄 APLICANDO CONFIGURACIÓN A LOS TABS")
        logger.info("=" * 80)
        
        antennas_config = self.wizard_config.get('antennas', {})
        
        # Debug detallado
        logger.info(f"📦 Configuración a aplicar:")
        logger.info(f"   Keys: {list(antennas_config.keys())}")
        logger.info(f"   Tipos: {[type(k).__name__ for k in antennas_config.keys()]}")
        
        for port, config in antennas_config.items():
            logger.info(f"   Puerto {port}:")
            logger.info(f"      name: {config.get('name')}")
            logger.info(f"      enabled: {config.get('enabled')}")
            logger.info(f"      start: {config.get('start')}")
            logger.info(f"      finish: {config.get('finish')}")
            logger.info(f"      checkpoint: {config.get('checkpoint')}")
        
        # 1. 🔥 APLICAR A DETECTION TAB
        try:
            logger.info("\n📡 Actualizando DetectionTab...")
            if hasattr(self, 'detection_tab'):
                self.detection_tab.update_antenna_roles_from_config(antennas_config)
                logger.info("✅ DetectionTab actualizado")
            else:
                logger.error("❌ detection_tab no existe!")
        except Exception as e:
            logger.error(f"❌ Error actualizando DetectionTab: {e}")
            import traceback
            traceback.print_exc()
        
        # 2. 🔥 APLICAR A CONFIGURATION TAB
        try:
            logger.info("\n⚙️  Actualizando ConfigurationTab...")
            if hasattr(self, 'config_tab'):
                # Tu ConfigurationTab debe tener un método load_configuration
                if hasattr(self.config_tab, 'load_configuration'):
                    self.config_tab.load_configuration(self.wizard_config)
                    logger.info("✅ ConfigurationTab actualizado")
                else:
                    logger.warning("⚠️  ConfigurationTab no tiene load_configuration()")
            else:
                logger.error("❌ config_tab no existe!")
        except Exception as e:
            logger.error(f"❌ Error actualizando ConfigurationTab: {e}")
            import traceback
            traceback.print_exc()
        
        logger.info("=" * 80)
        logger.info("✅ CONFIGURACIÓN APLICADA A TODOS LOS TABS")
        logger.info("=" * 80)
    
    def on_connection_status_changed(self, connected, message):
        """Actualiza status bar según estado de conexión"""
        if connected:
            self.status_label.setText(f"✓ {message}")
            logger.info(f"✓ {message}")
        else:
            self.status_label.setText(f"✗ {message}")
            logger.warning(f"✗ {message}")

    def get_antenna_config(self, port: int) -> dict:
        """
        Obtiene configuración completa de una antena específica
        
        Args:
            port: Número de puerto (1-8) como INT
            
        Returns:
            Dict con configuración de la antena
        """
        if not self.wizard_config:
            return {}
        
        antennas = self.wizard_config.get('antennas', {})
        
        # 🔥 Buscar por puerto como int (ya normalizado)
        return antennas.get(port, {})
    
    def get_antenna_role(self, port: int) -> str:
        """
        Obtiene el rol PRINCIPAL de una antena
        Para compatibilidad con código existente
        """
        config = self.get_antenna_config(port)
        
        # Retornar el primer rol encontrado (por prioridad)
        if config.get('start'):
            return 'start'
        elif config.get('finish'):
            return 'finish'
        elif config.get('checkpoint'):
            return 'checkpoint'
        
        return 'unknown'

    def get_antenna_roles(self, port: int) -> list:
        """
        Obtiene TODOS los roles de una antena
        Retorna lista de roles: ['start', 'finish', 'checkpoint']
        """
        config = self.get_antenna_config(port)
        roles = []
        
        if config.get('start'):
            roles.append('start')
        if config.get('finish'):
            roles.append('finish')
        if config.get('checkpoint'):
            roles.append('checkpoint')
        
        return roles
    
    def get_antenna_name(self, port: int) -> str:
        """Obtiene el nombre de una antena"""
        config = self.get_antenna_config(port)
        return config.get('name', f'Antena {port}')
    
    def get_enabled_antennas(self) -> list:
        """Obtiene lista de puertos habilitados"""
        if not self.wizard_config:
            return []
        
        antennas = self.wizard_config.get('antennas', {})
        return [
            port for port, config in antennas.items()
            if config.get('enabled', False)
        ]

    def create_tabs(self):
        """Crea todos los tabs de la aplicación"""
        
        logger.info("=" * 80)
        logger.info("🏗️  CREANDO TABS")
        logger.info("=" * 80)
        logger.info(f"wizard_config existe: {self.wizard_config is not None}")
        if self.wizard_config:
            logger.info(f"  Antenas en config: {list(self.wizard_config.get('antennas', {}).keys())}")
        logger.info("=" * 80)
        
        # ===== TAB 1: DETECCIÓN =====
        logger.info("\n📡 Creando DetectionTab...")
        self.detection_tab = DetectionTab(signals=self.signals)
        self.tab_widget.addTab(self.detection_tab, "🔍 Detección")
        logger.info("✅ DetectionTab creado")
        
        # ===== TAB 2: GESTIÓN DE EVENTOS =====
        logger.info("\n📋 Creando EventConfigWidget...")
        self.event_config_widget = EventConfigWidget()
        self.tab_widget.addTab(self.event_config_widget, "📋 Gestión de Eventos")
        logger.info("✅ EventConfigWidget creado")
        
        # ===== TAB 3: COMPETENCIA =====
        logger.info("\n🏃 Creando RaceMonitoringWidget...")
        self.race_monitoring_widget = RaceMonitoringWidget()
        self.tab_widget.addTab(self.race_monitoring_widget, "🏃 Competencia")
        logger.info("✅ RaceMonitoringWidget creado")
        
        # ===== TAB 4: CONFIGURACIÓN =====
        logger.info("\n⚙️  Creando ConfigurationTab...")
        logger.info(f"  Pasando scanner: {self.scanner is not None}")
        logger.info(f"  Pasando signals: {self.signals is not None}")
        logger.info(f"  Pasando wizard_config: {self.wizard_config is not None}")
        
        try:
            self.config_tab = ConfigurationTab(
                scanner=self.scanner,
                signals=self.signals,
                wizard_config=self.wizard_config
            )
            logger.info("✅ ConfigurationTab creado")
            self.tab_widget.addTab(self.config_tab, "⚙️ Configuración")
        except Exception as e:
            logger.error(f"❌ Error creando ConfigurationTab: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        logger.info("=" * 80)
        logger.info("✅ TODOS LOS TABS CREADOS")
        logger.info("=" * 80)

    def connect_signals(self):
        """Conecta señales del sistema"""
        logger.info("🔌 Conectando señales...")
        
        # Señal de estado de conexión
        self.signals.connection_status_changed.connect(self.on_connection_status_changed)
        
        # Conectar señales de widgets existentes de forma segura
        if hasattr(self, 'event_config_widget') and hasattr(self.event_config_widget, 'category_started'):
            self.event_config_widget.category_started.connect(self.on_category_started)
        
        if hasattr(self, 'race_monitoring_widget'):
            pass
        
        logger.info("✅ Señales conectadas")

    @pyqtSlot(int)
    def on_tab_changed(self, index):
        """Manejar cambio de pestaña"""
        current_widget = self.tab_widget.widget(index)
        if hasattr(current_widget, 'on_tab_activated'):
            current_widget.on_tab_activated()
    
    @pyqtSlot(str)
    def on_category_started(self, category_id):
        """Manejar inicio de categoría"""
        # Inicializar race tracker si no existe
        if not hasattr(self, 'race_tracker') or not self.race_tracker:
            event_manager = self.event_config_widget.get_event_manager()
            self.race_tracker = IntegratedRaceTracker(event_manager)
            
            # Aplicar configuración de antenas si existe
            if self.wizard_config:
                antennas_config = self.wizard_config.get('antennas', {})
                enabled_antennas = {
                    port: config for port, config in antennas_config.items() 
                    if config.get('enabled', False)
                }
                self.race_tracker.set_antenna_config(enabled_antennas)
            
            # Conectar el widget de monitoreo
            self.race_monitoring_widget.set_race_tracker(self.race_tracker)
        
        self.signals.log_message.emit(f"Categoría iniciada: {category_id}", "info")
        self.status_label.setText(f"Categoría activa: {category_id}")
    
    @pyqtSlot(str)
    def on_category_finished(self, category_id):
        """Manejar finalización de categoría"""
        self.signals.log_message.emit(f"Categoría finalizada: {category_id}", "info")
    
    @pyqtSlot(dict)
    def on_tag_detected_global(self, tag):
        """Procesar detección de tag a nivel global"""
        tag_number = tag['number']
        
        # Procesar con race tracker si existe y hay categoría activa
        if hasattr(self, 'race_tracker') and self.race_tracker:
            reading = self.race_tracker.process_chip_reading(
                tag_number, 
                tag['antenna'], 
                tag['timestamp']
            )
            
            if reading:
                self.race_monitoring_widget.refresh_all_data()
                
                participant_status = self.race_tracker.get_participant_status(tag_number)
                if participant_status:
                    self.signals.log_message.emit(
                        f"Participante {tag_number}: {participant_status.status}", 
                        "info"
                    )
    
    @pyqtSlot(str, str)
    def on_log_message(self, message, level):
        """Actualizar barra de estado con mensajes importantes"""
        if level in ['warning', 'error']:
            self.status_label.setText(f"⚠️ {message}")
        else:
            self.status_label.setText(message)
    
    @pyqtSlot()
    def export_data(self):
        """Exportar datos (placeholder)"""
        self.signals.log_message.emit("Función de exportación pendiente de implementar", "info")
        QMessageBox.information(
            self, 
            "Exportar Datos", 
            "Funcionalidad de exportación será implementada en futuras versiones."
        )
    
    def closeEvent(self, event):
        """Manejar cierre de la aplicación"""
        reply = QMessageBox.question(
            self,
            'Confirmar Salida',
            '¿Está seguro que desea salir?\nSe perderán los datos no guardados.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Desconectar scanner si está conectado
            if self.scanner and hasattr(self.scanner, 'connected') and self.scanner.connected:
                self.scanner.disconnect()
            event.accept()
        else:
            event.ignore()
    
    def get_current_state(self):
        """Obtener estado actual del sistema para debugging"""
        return {
            'scanner_connected': self.scanner.connected if self.scanner else False,
            'race_tracker_active': hasattr(self, 'race_tracker') and self.race_tracker is not None,
            'active_tab': self.tab_widget.currentIndex(),
            'wizard_config_loaded': self.wizard_config is not None
        }