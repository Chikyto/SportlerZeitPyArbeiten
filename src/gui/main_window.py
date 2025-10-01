"""
Ventana principal de la aplicación RFID Athletics Timer
Arquitectura modular con separación de responsabilidades
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                            QTabWidget, QLabel, QMessageBox)
from PyQt6.QtCore import pyqtSlot, Qt

from ..core.advanced_scanner import AdvancedYR8900Scanner
from ..core.integrated_race_tracker import IntegratedRaceTracker
from ..utils.signals import get_app_signals

# Importar tabs
from .tabs.connection_tab import ConnectionTab
from .tabs.detection_tab import DetectionTab

# Importar widgets existentes
from .widgets.antenna_config_widget import AntennaConfigWidget
from .widgets.event_config_widget import EventConfigWidget
from .widgets.race_monitoring_widget import RaceMonitoringWidget


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
        
        # Configuración del wizard (si viene del wizard)
        self.wizard_config = wizard_config
        
        # Señales centralizadas
        self.signals = get_app_signals()
        
        # Core components
        self.scanner = AdvancedYR8900Scanner()
        self.race_tracker = None
        
        # Setup
        self.setup_ui()
        self.connect_signals()
        self.apply_wizard_config()
        
    def setup_ui(self):
        """Configurar interfaz principal"""
        self.setWindowTitle("RFID Athletics Timer - Sistema de Control")
        self.setGeometry(100, 100, 1000, 750)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
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
    
    def create_tabs(self):
        """Crear todas las pestañas de la aplicación"""
        # 1. Gestión de Eventos (primero - lo más importante)
        self.event_config_widget = EventConfigWidget()
        self.tab_widget.addTab(self.event_config_widget, "⚙️ Gestión de Eventos")
        
        # 2. Competencia (segundo - monitoreo activo)
        self.race_monitoring_widget = RaceMonitoringWidget()
        self.tab_widget.addTab(self.race_monitoring_widget, "🏁 Competencia")
        
        # 3. Conexión RFID
        self.connection_tab = ConnectionTab(self.scanner)
        self.tab_widget.addTab(self.connection_tab, "🔌 Conexión RFID")
        
        # 4. Configuración de Antenas
        self.antenna_config_widget = AntennaConfigWidget()
        self.tab_widget.addTab(self.antenna_config_widget, "📡 Config. Antenas")
        
        # 5. Detección de Chips
        self.detection_tab = DetectionTab(self.scanner)
        self.tab_widget.addTab(self.detection_tab, "🔍 Detección de Chips")
        
        # 6. Base de Datos (futuro)
        self.create_database_tab()
    
    def create_database_tab(self):
        """Crear tab de base de datos (placeholder)"""
        from PyQt6.QtWidgets import QGroupBox, QPushButton, QTextEdit
        
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Estado de conexión a DB
        db_status_group = QGroupBox("Estado de Base de Datos")
        db_status_layout = QVBoxLayout(db_status_group)
        
        db_status = QLabel("Sin conexión a base de datos")
        db_status.setStyleSheet("font-weight: bold; color: orange;")
        db_status_layout.addWidget(db_status)
        
        # Botones de DB
        from PyQt6.QtWidgets import QHBoxLayout
        db_buttons = QHBoxLayout()
        
        connect_firebase_btn = QPushButton("Conectar Firebase")
        connect_firebase_btn.setEnabled(False)
        connect_firebase_btn.setToolTip("Funcionalidad pendiente de implementar")
        db_buttons.addWidget(connect_firebase_btn)
        
        export_data_btn = QPushButton("Exportar Datos")
        export_data_btn.clicked.connect(self.export_data)
        db_buttons.addWidget(export_data_btn)
        
        db_status_layout.addLayout(db_buttons)
        layout.addWidget(db_status_group)
        
        # Información local
        local_group = QGroupBox("Almacenamiento Local (Temporal)")
        local_layout = QVBoxLayout(local_group)
        
        local_storage_info = QTextEdit()
        local_storage_info.setMaximumHeight(150)
        local_storage_info.setReadOnly(True)
        local_storage_info.setPlainText(
            "Datos se almacenan localmente mientras se implementa Firebase.\n"
            "Todos los chips detectados se mantienen en memoria."
        )
        local_layout.addWidget(local_storage_info)
        layout.addWidget(local_group)
        
        # Futuras funcionalidades
        future_group = QGroupBox("Funcionalidades Futuras")
        future_layout = QVBoxLayout(future_group)
        
        future_info = QLabel(
            "• Sincronización automática con Firebase\n"
            "• Backup en tiempo real\n"
            "• Análisis de datos históricos\n"
            "• Reportes automáticos"
        )
        future_layout.addWidget(future_info)
        layout.addWidget(future_group)
        
        self.tab_widget.addTab(tab, "💾 Base de Datos")
    
    def connect_signals(self):
        """Conectar todas las señales del sistema"""
        # Señales de eventos
        self.event_config_widget.category_started.connect(self.on_category_started)
        self.event_config_widget.category_finished.connect(self.on_category_finished)
        
        # Señales de antenas
        self.antenna_config_widget.config_applied.connect(self.on_antenna_config_applied)
        
        # Señales de logging
        self.signals.log_message.connect(self.on_log_message)
        
        # Señales de tags
        self.signals.tag_detected.connect(self.on_tag_detected_global)
    
    def apply_wizard_config(self):
        """Aplicar configuración del wizard si existe"""
        if not self.wizard_config:
            print("DEBUG: No hay wizard_config")
            return
        
        print("\n" + "="*60)
        print("DEBUG: CONFIGURACIÓN COMPLETA DEL WIZARD")
        print("="*60)
        import json
        print(json.dumps(self.wizard_config, indent=2, default=str))
        print("="*60 + "\n")
        
        # Aplicar configuración de conexión
        if 'connection' in self.wizard_config:
            conn = self.wizard_config['connection']
            try:
                self.connection_tab.host_input.setText(conn.get('host', '192.168.0.178'))
                self.connection_tab.port_input.setValue(conn.get('port', 4001))
                self.connection_tab.host_input.setReadOnly(True)
                self.connection_tab.port_input.setReadOnly(True)
                
                if conn.get('verified', False):
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(500, self.connection_tab.connect_scanner)
            except Exception as e:
                print(f"ERROR aplicando config de conexión: {e}")
        
        # Aplicar configuración de antenas
        if 'antennas' in self.wizard_config:
            wizard_antennas = self.wizard_config['antennas']
            
            print(f"DEBUG: Wizard antennas keys: {list(wizard_antennas.keys())}")
            print(f"DEBUG: Wizard antennas types: {[type(k) for k in wizard_antennas.keys()]}")
            
            # Crear configuración completa para todas las antenas (0-7)
            full_config = {}
            
            for antenna_index in range(8):
                # Probar ambos: int y string (por si JSON convirtió a string)
                found = False
                
                # Intentar como int
                if antenna_index in wizard_antennas:
                    wizard_ant = wizard_antennas[antenna_index]
                    found = True
                # Intentar como string
                elif str(antenna_index) in wizard_antennas:
                    wizard_ant = wizard_antennas[str(antenna_index)]
                    found = True
                
                if found:
                    # Antena configurada en el wizard
                    full_config[antenna_index] = {
                        'enabled': wizard_ant.get('enabled', True),
                        'name': wizard_ant.get('name', f'Antena {antenna_index + 1}'),
                        'start': wizard_ant.get('start', False),
                        'finish': wizard_ant.get('finish', False),
                        'checkpoint': wizard_ant.get('checkpoint', False),
                        'description': wizard_ant.get('description', 'Sin configurar')
                    }
                    print(f"DEBUG: ✓ Antena {antenna_index} configurada: {full_config[antenna_index]}")
                else:
                    # Antena no configurada
                    full_config[antenna_index] = {
                        'enabled': False,
                        'name': f'Antena {antenna_index + 1}',
                        'start': False,
                        'finish': False,
                        'checkpoint': False,
                        'description': 'Sin configurar'
                    }
            
            print(f"\nDEBUG: Config completa a enviar al widget:")
            for idx, cfg in full_config.items():
                if cfg['enabled']:
                    print(f"  Antena {idx}: {cfg}")
            
            try:
                print("\nDEBUG: Llamando a load_from_wizard_config...")
                self.antenna_config_widget.load_from_wizard_config(full_config)
                self.signals.antenna_config_applied.emit(full_config)
                print("DEBUG: ✓ Configuración aplicada al widget")
                    
            except Exception as e:
                print(f"ERROR aplicando config de antenas: {e}")
                import traceback
                traceback.print_exc()

    @pyqtSlot(int)
    def on_tab_changed(self, index):
        """Manejar cambio de pestaña"""
        # Notificar al tab actual que fue activado
        current_widget = self.tab_widget.widget(index)
        if hasattr(current_widget, 'on_tab_activated'):
            current_widget.on_tab_activated()
    
    @pyqtSlot(str)
    def on_category_started(self, category_id):
        """Manejar inicio de categoría"""
        # Inicializar race tracker si no existe
        if not self.race_tracker:
            event_manager = self.event_config_widget.get_event_manager()
            self.race_tracker = IntegratedRaceTracker(event_manager)
            
            # Aplicar configuración de antenas si existe
            antenna_config = self.antenna_config_widget.get_current_config()
            enabled_antennas = {
                ant_id: config for ant_id, config in antenna_config.items() 
                if config['enabled']
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
    def on_antenna_config_applied(self, config_data):
        """Manejar configuración de antenas aplicada"""
        config_summary = []
        
        for antenna_id, config in config_data.items():
            roles = []
            if config['start']:
                roles.append("Largada")
            if config['finish']:
                roles.append("Meta")
            if config['checkpoint']:
                roles.append("Checkpoint")
            
            name = config['name']
            roles_str = "+".join(roles)
            config_summary.append(f"Antena {antenna_id + 1} ({name}): {roles_str}")
        
        self.signals.log_message.emit("Configuración de antenas aplicada:", "info")
        for line in config_summary:
            self.signals.log_message.emit(f"  • {line}", "info")
        
        # Actualizar tracker integrado si existe
        if self.race_tracker:
            self.race_tracker.set_antenna_config(config_data)
        
        enabled_count = len(config_summary)
        self.status_label.setText(f"Sistema configurado con {enabled_count} antenas activas")
    
    @pyqtSlot(dict)
    def on_tag_detected_global(self, tag):
        """Procesar detección de tag a nivel global"""
        tag_number = tag['number']
        
        # Procesar con race tracker si existe y hay categoría activa
        if self.race_tracker:
            reading = self.race_tracker.process_chip_reading(
                tag_number, 
                tag['antenna'], 
                tag['timestamp']
            )
            
            if reading:
                # Forzar actualización del widget de monitoreo
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
            if self.scanner.connected:
                self.scanner.disconnect()
            event.accept()
        else:
            event.ignore()
    
    def get_current_state(self):
        """Obtener estado actual del sistema para debugging"""
        return {
            'scanner_connected': self.scanner.connected if self.scanner else False,
            'race_tracker_active': self.race_tracker is not None,
            'active_tab': self.tab_widget.currentIndex(),
            'antenna_config': self.antenna_config_widget.get_current_config() if hasattr(self, 'antenna_config_widget') else None
        }