#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ventana principal de la aplicación RFID Athletics Timer - REFACTORIZADO
src/gui/main_window.py

Responsabilidad única: Coordinación de alto nivel y UI principal
Delegación: AntennaManager para antenas, TabManager para tabs
"""

import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                            QTabWidget, QLabel, QMessageBox)
from PyQt6.QtCore import pyqtSlot

from src.utils.signals import AppSignals
from ..core.advanced_scanner import AdvancedYR8900Scanner
from ..core.race_tracking.race_manager import RaceManager
from .managers.antenna_manager import AntennaManager
from .managers.tab_manager import TabManager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación
    
    Responsabilidades:
    - Setup UI principal (título, tabs, status bar)
    - Coordinar managers (AntennaManager, TabManager)
    - Configurar scanner
    - Conectar señales globales
    """
    
    def __init__(self, wizard_config=None):
        super().__init__()

        # Configuración y managers
        self.wizard_config = self._normalize_config(wizard_config)
        self.antenna_manager = AntennaManager(self.wizard_config)
        self.race_manager = RaceManager()  # Sistema de timing de carreras
        self.signals = AppSignals()
        self.scanner = None

        # Setup
        self.setWindowTitle("RFID Athletics Timer")
        self.setMinimumSize(1200, 800)

        # Orden crítico de inicialización
        self.setup_ui()           # 1. Crear UI básica
        self.setup_scanner()      # 2. Configurar scanner
        self.apply_config()       # 3. Aplicar config a tabs
        self.connect_signals()    # 4. Conectar señales

        logger.info("✅ MainWindow inicializado correctamente")
    
    def _normalize_config(self, config):
        """
        Normalizar configuración para asegurar tipos correctos
        
        Args:
            config: Configuración del wizard
        
        Returns:
            dict: Configuración normalizada
        """
        if not config:
            return config
        
        logger.info("🔧 Normalizando configuración")
        
        # Normalizar keys de antennas a int
        if 'antennas' in config:
            antennas_normalized = {}
            for key, value in config['antennas'].items():
                port_int = int(key) if isinstance(key, str) else key
                antennas_normalized[port_int] = value
            
            config['antennas'] = antennas_normalized
            logger.info(f"✅ Antenas normalizadas: {list(antennas_normalized.keys())}")
        
        return config
    
    def setup_ui(self):
        """Configurar interfaz principal"""
        logger.info("🎨 Configurando UI principal")
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        
        # Sistema de pestañas
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Barra de estado
        self.status_label = QLabel("Aplicación iniciada")
        layout.addWidget(self.status_label)
        
        # Crear tabs usando TabManager
        self.tab_manager = TabManager(
            self.tab_widget,
            self.signals,
            self.scanner,
            self.antenna_manager,
            self.race_manager
        )
        self.tab_manager.create_all_tabs()
        
        logger.info("✅ UI principal configurada")
    
    def setup_scanner(self):
        """Configurar scanner con datos del wizard"""
        if not self.wizard_config:
            logger.warning("⚠️  No hay configuración del wizard")
            self.signals.connection_status_changed.emit(False, "Sin configuración")
            return
        
        try:
            logger.info("🔌 Configurando scanner...")
            
            # Obtener parámetros de conexión
            conn = self.wizard_config.get('connection', {})
            host = conn.get('host', '192.168.0.178')
            port = conn.get('port', 4001)
            
            # Crear scanner
            self.scanner = AdvancedYR8900Scanner(host, port)
            
            # Conectar al lector
            if not self.scanner.connect():
                logger.error("❌ No se pudo conectar al scanner")
                self.signals.connection_status_changed.emit(
                    False, 
                    "Error de conexión al lector"
                )
                return
            
            # Configurar antenas habilitadas
            enabled_ports = self.antenna_manager.get_enabled_antennas()
            logger.info(f"📡 Antenas habilitadas: {enabled_ports}")
            self.scanner.available_antennas = enabled_ports
      
            # Configurar potencia si está en config
            power = self.wizard_config.get('power_dbm')
            if power:
                logger.info(f"⚡ Configurando potencia: {power} dBm")
                self.scanner.set_output_power(power)
            
            # Actualizar TabManager con scanner
            self.tab_manager.set_scanner(self.scanner)
            
            # Emitir señal de scanner listo
            self.signals.scanner_ready.emit(self.scanner)
            self.signals.connection_status_changed.emit(
                True, 
                f"Conectado - {len(enabled_ports)} antenas activas"
            )
            
            logger.info("✅ Scanner configurado y listo")
            
        except Exception as e:
            logger.error(f"❌ Error configurando scanner: {e}")
            import traceback
            traceback.print_exc()
            self.signals.connection_status_changed.emit(False, str(e))
    
    def apply_config(self):
        """
        Aplicar configuración del wizard a todos los componentes
        """
        if not self.wizard_config:
            logger.warning("⚠️  No hay configuración para aplicar")
            return
        
        logger.info("🔄 Aplicando configuración a componentes")
        
        # Delegar a TabManager
        self.tab_manager.apply_config_to_all_tabs(self.wizard_config)
        
        logger.info("✅ Configuración aplicada")
    
    def connect_signals(self):
        """Conectar señales del sistema"""
        logger.info("🔌 Conectando señales...")

        # Señal de estado de conexión
        self.signals.connection_status_changed.connect(self.on_connection_status_changed)

        # Señal de detección de tags → RaceManager
        self.signals.tag_detected.connect(self.on_tag_detected_for_race)

        # 🔥 Señal de auto-inicio de escaneo cuando se inician distancias
        self.signals.auto_start_scanning.connect(self.on_auto_start_scanning)

        logger.info("✅ Señales conectadas")
    
    @pyqtSlot(bool, str)
    def on_connection_status_changed(self, connected, message):
        """Actualizar status bar según estado de conexión"""
        if connected:
            self.status_label.setText(f"✓ {message}")
            logger.info(f"✓ {message}")
        else:
            self.status_label.setText(f"✗ {message}")
            logger.warning(f"✗ {message}")

    @pyqtSlot(dict)
    def on_tag_detected_for_race(self, tag_data):
        """
        Procesar detección de tag para sistema de carreras

        Args:
            tag_data: Dict con información del tag procesado
                {
                    'tag_id': str,
                    'antenna_port': int,
                    'roles': List[str],
                    'antenna_name': str,
                    'timestamp': datetime
                }
        """
        try:
            # Extraer datos necesarios
            tag_id = tag_data.get('tag_id')
            antenna_port = tag_data.get('antenna')  # o 'antenna_port'
            if not antenna_port:
                antenna_port = tag_data.get('antenna_port')
            timestamp = tag_data.get('timestamp')
            roles = tag_data.get('roles', [])

            # Validar datos mínimos
            if not tag_id or not antenna_port or not timestamp:
                logger.warning(f"⚠️  Detección incompleta: {tag_data}")
                return

            # Procesar con RaceManager
            event = self.race_manager.process_detection(
                tag_id=tag_id,
                timestamp=timestamp,
                antenna_port=antenna_port,
                roles=roles
            )

            if event:
                logger.info(f"🏁 Evento procesado: {event}")
            else:
                logger.debug(f"Tag {tag_id} detectado pero sin evento de carrera asociado")

        except Exception as e:
            logger.error(f"❌ Error procesando detección para carrera: {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot()
    def on_auto_start_scanning(self):
        """
        🔥 Callback para auto-iniciar escaneo cuando se inician distancias

        Este método es llamado cuando EventConfigWidget emite la señal auto_start_scanning
        después de iniciar una o más distancias.
        """
        try:
            logger.info("=" * 80)
            logger.info("🚀 AUTO-INICIO DE ESCANEO SOLICITADO")
            logger.info("=" * 80)

            # Obtener referencia al DetectionTab
            detection_tab = self.tab_manager.get_tab('detection')

            if not detection_tab:
                logger.error("❌ DetectionTab no encontrado")
                return

            # Llamar al método de auto-inicio
            success = detection_tab.auto_start_scanning()

            if success:
                logger.info("✅ Escaneo automático iniciado exitosamente")
                logger.info("📡 Las antenas están escaneando chips para la carrera")
            else:
                logger.warning("⚠️  No se pudo iniciar escaneo automático")
                logger.warning("   Verifica configuración de scanner y antenas")

            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"❌ Error en auto-inicio de escaneo: {e}")
            import traceback
            traceback.print_exc()

    # ========================================================================
    # Métodos de acceso (delegan a AntennaManager)
    # ========================================================================
    
    def get_antenna_config(self, port: int) -> dict:
        """Obtener configuración completa de una antena"""
        return self.antenna_manager.get_antenna_config(port)
    
    def get_antenna_roles(self, port: int) -> list:
        """Obtener todos los roles de una antena"""
        return self.antenna_manager.get_antenna_roles(port)
    
    def get_antenna_role(self, port: int) -> str:
        """Obtener rol principal de una antena (compatibilidad)"""
        return self.antenna_manager.get_antenna_role(port)
    
    def get_antenna_name(self, port: int) -> str:
        """Obtener nombre de una antena"""
        return self.antenna_manager.get_antenna_name(port)
    
    def get_enabled_antennas(self) -> list:
        """Obtener lista de puertos habilitados"""
        return self.antenna_manager.get_enabled_antennas()
    
    # ========================================================================
    # Cleanup
    # ========================================================================
    
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
                logger.info("Desconectando scanner...")
                self.scanner.disconnect()
            event.accept()
        else:
            event.ignore()
    
    # ========================================================================
    # Debug y utilidades
    # ========================================================================
    
    def get_current_state(self):
        """Obtener estado actual del sistema para debugging"""
        return {
            'scanner_connected': self.scanner.connected if self.scanner else False,
            'active_tab': self.tab_widget.currentIndex(),
            'wizard_config_loaded': self.wizard_config is not None,
            'antenna_summary': self.antenna_manager.get_summary(),
            'tab_count': self.tab_manager.get_tab_count()
        }