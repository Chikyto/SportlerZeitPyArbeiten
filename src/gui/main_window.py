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
from ..core.race_tracking.models import EventType
from .managers.antenna_manager import AntennaManager
from .managers.tab_manager import TabManager
from .widgets.finish_ticket_dialog import FinishTicketDialog
from .widgets.chip_alias_dialog import ChipAliasDialog

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
        # Set para evitar mostrar el diálogo de alias más de una vez por chip
        self._shown_alias_dialogs: set = set()

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

        # 🎟️ Señal de atleta llegando a meta → mostrar ticket
        self.signals.athlete_finished.connect(self.on_athlete_finished_show_ticket)

        # 🔗 Chip desconocido → mostrar diálogo para registrar alias
        self.signals.unknown_chip_detected.connect(self.on_unknown_chip_detected)

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
            logger.info("=" * 80)
            logger.info("🏁 MainWindow: SEÑAL tag_detected RECIBIDA")
            logger.info(f"   Tag data: {tag_data}")
            logger.info("=" * 80)

            # Extraer datos necesarios
            tag_id = tag_data.get('tag_id')
            antenna_port = tag_data.get('antenna')  # o 'antenna_port'
            if not antenna_port:
                antenna_port = tag_data.get('antenna_port')
            if not antenna_port:
                antenna_port = tag_data.get('port')  # Nuevo: también intentar 'port'
            # Priorizar timestamp_obj (datetime) sobre timestamp (string)
            timestamp = tag_data.get('timestamp_obj')
            if not timestamp:
                timestamp = tag_data.get('timestamp')  # Fallback a timestamp string
            roles = tag_data.get('roles', [])

            logger.info(f"📊 Datos extraídos:")
            logger.info(f"   tag_id: {tag_id}")
            logger.info(f"   antenna_port: {antenna_port}")
            logger.info(f"   timestamp: {timestamp}")
            logger.info(f"   roles: {roles}")

            # Validar datos mínimos
            if not tag_id or not antenna_port or not timestamp:
                logger.warning(f"⚠️  Detección incompleta: {tag_data}")
                logger.warning(f"   tag_id={tag_id}, antenna_port={antenna_port}, timestamp={timestamp}")
                return

            logger.info("📤 Enviando a RaceManager.process_detection()...")

            # Procesar con RaceManager
            event = self.race_manager.process_detection(
                tag_id=tag_id,
                timestamp=timestamp,
                antenna_port=antenna_port,
                roles=roles
            )

            if event:
                logger.info(f"✅ Evento procesado exitosamente: {event}")
            else:
                logger.warning(f"⚠️  Tag {tag_id} detectado pero sin evento de carrera asociado")
                logger.warning("   Posibles causas:")
                logger.warning("   - Chip no asociado a ningún atleta")
                logger.warning("   - Distancia no está en estado RUNNING")
                logger.warning("   - Rol de antena no coincide con estado del atleta")

            # Resolver nombre y distancia del atleta para mostrar en tabla de detección
            athlete, distance = self.race_manager._find_athlete_by_tag(tag_id)
            if athlete and distance and self.signals:
                self.signals.athlete_tag_resolved.emit(tag_id, athlete.name, distance.name)

                # Si fue un evento de llegada a meta, emitir notificación
                if event and event.event_type == EventType.FINISH:
                    result = self.race_manager.results.get(distance.distance_id, {}).get(athlete.athlete_id)
                    formatted_time = result.get_formatted_time() if result else "N/A"
                    self.signals.athlete_finished.emit(athlete.name, distance.name, formatted_time)
            elif not athlete and self.signals:
                # Chip desconocido: emitir señal para que el usuario pueda registrar alias
                logger.warning(f"⚠️  Chip desconocido '{tag_id}' - emitiendo señal para registro de alias")
                self.signals.unknown_chip_detected.emit(tag_id)

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

    @pyqtSlot(str, str, str)
    def on_athlete_finished_show_ticket(self, athlete_name: str, distance_name: str, formatted_time: str):
        """
        Mostrar ticket imprimible cuando un atleta cruza la meta

        Args:
            athlete_name: Nombre del atleta
            distance_name: Nombre de la distancia
            formatted_time: Tiempo formateado (HH:MM:SS)
        """
        try:
            logger.info(f"🎟️  Generando ticket para: {athlete_name}")

            # Buscar el atleta en el race_manager para obtener toda su info
            athlete = None
            distance = None
            result = None

            for dist in self.race_manager.get_all_distances():
                for participant in dist.participants:
                    if participant.name == athlete_name:
                        athlete = participant
                        distance = dist
                        # Obtener el resultado
                        results_dict = self.race_manager.results.get(dist.distance_id, {})
                        result = results_dict.get(participant.athlete_id)
                        break
                if athlete:
                    break

            if not athlete or not distance or not result:
                logger.warning(f"⚠️  No se pudo encontrar info completa para {athlete_name}")
                return

            # Obtener clasificaciones
            position_overall = result.position or 0

            # Posición por género
            results_by_gender = self.race_manager.get_results_by_gender(distance.distance_id)
            gender_key = athlete.gender.upper()[0] if athlete.gender else "Otro"
            if gender_key not in ["M", "F"]:
                gender_key = "Otro"
            gender_results = results_by_gender.get(gender_key, [])
            position_gender = next((i+1 for i, r in enumerate(gender_results) if r.athlete.athlete_id == athlete.athlete_id), 0)

            # Posición por categoría
            category = athlete.get_category() or "Sin categoría"
            results_by_award = self.race_manager.get_results_by_award_category(distance.distance_id)
            category_results = results_by_award.get(category, [])
            position_category = next((i+1 for i, r in enumerate(category_results) if r.athlete.athlete_id == athlete.athlete_id), 0)

            # Obtener nombre del evento
            event_config = self.tab_manager.get_tab('event_config')
            event_name = "Carrera"
            if event_config and hasattr(event_config, 'event_name_input'):
                event_name = event_config.event_name_input.text() or "Carrera"

            # Crear y mostrar el ticket
            ticket_dialog = FinishTicketDialog(
                athlete_name=athlete.name,
                distance_name=distance.name,
                bib_number=athlete.bib_number,
                finish_time=formatted_time,
                position_overall=position_overall,
                position_gender=position_gender,
                position_category=position_category,
                gender=athlete.gender or "Otro",
                category=category,
                event_name=event_name,
                parent=self
            )

            ticket_dialog.exec()
            logger.info(f"✅ Ticket mostrado para {athlete_name}")

        except Exception as e:
            logger.error(f"❌ Error mostrando ticket: {e}")
            import traceback
            traceback.print_exc()
            import traceback
            traceback.print_exc()

    @pyqtSlot(str)
    def on_unknown_chip_detected(self, tag_id: str):
        """
        Manejar detección de chip desconocido.

        Muestra un diálogo (una sola vez por chip) para que el usuario
        lo asocie como alias de un atleta ya registrado. Útil cuando USB
        y TCP/IP reportan IDs distintos del mismo chip físico.

        Args:
            tag_id: ID del chip detectado que no está en la base de datos
        """
        try:
            # Mostrar el diálogo solo una vez por chip desconocido
            if tag_id in self._shown_alias_dialogs:
                return
            self._shown_alias_dialogs.add(tag_id)

            athletes_with_chips = self.race_manager.get_all_athletes_with_chips()

            if not athletes_with_chips:
                logger.warning(f"⚠️  Chip '{tag_id}' desconocido, pero no hay atletas con chip asignado para comparar")
                return

            dialog = ChipAliasDialog(
                unknown_tag_id=tag_id,
                athletes_with_chips=athletes_with_chips,
                parent=self
            )
            dialog.alias_registered.connect(self._on_alias_confirmed)

            if dialog.exec():
                # Si aceptó, el alias quedó registrado → limpiar del set para no bloquear futuras re-detecciones
                self._shown_alias_dialogs.discard(tag_id)

        except Exception as e:
            logger.error(f"❌ Error mostrando diálogo de alias: {e}")
            import traceback
            traceback.print_exc()

    def _on_alias_confirmed(self, alias_tag_id: str, athlete_id: str):
        """
        Procesar confirmación de registro de alias.

        Args:
            alias_tag_id: ID alternativo a registrar
            athlete_id: UUID del atleta al que pertenece
        """
        try:
            success = self.race_manager.register_chip_alias(alias_tag_id, athlete_id)
            if success:
                # Guardar los cambios en disco
                chip_assignment_widget = self.tab_manager.get_tab('chip_assignment')
                if chip_assignment_widget and hasattr(chip_assignment_widget, 'auto_save_data'):
                    chip_assignment_widget.auto_save_data()
                    logger.info(f"💾 Alias guardado en disco")
                else:
                    # Fallback: guardar directamente con persistence
                    from src.core.race_data_persistence import RaceDataPersistence
                    persistence = RaceDataPersistence()
                    persistence.save_race_data(self.race_manager)
                    logger.info(f"💾 Alias guardado (fallback)")
        except Exception as e:
            logger.error(f"❌ Error guardando alias: {e}")
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