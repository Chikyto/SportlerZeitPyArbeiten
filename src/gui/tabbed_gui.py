import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                            QTabWidget, QGroupBox, QLineEdit, QSpinBox,
                            QTableWidget, QTableWidgetItem, QHeaderView,
                            QCheckBox, QComboBox)
from PyQt6.QtCore import pyqtSignal, QTime, Qt
from PyQt6.QtGui import QFont
from datetime import datetime
from ..core.simple_scanner import SimpleScanner
from .widgets.antenna_config_widget import AntennaConfigWidget
from .widgets.event_config_widget import EventConfigWidget
from ..core.integrated_race_tracker import IntegratedRaceTracker

class TabbedGUI(QMainWindow):
    """GUI con sistema de pestañas organizado"""
    
    def __init__(self):
        super().__init__()
        self.scanner = SimpleScanner()
        self.detected_tags = {}
        self.race_active = False
        self.race_start_time = None
        self.race_results = {}
        self.race_tracker = None  # Se inicializa cuando se conecta el event manager
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interfaz con pestañas"""
        self.setWindowTitle("RFID Athletics Timer - Sistema de Control")
        self.setGeometry(100, 100, 900, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Sistema de pestañas
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Crear pestañas
        self.setup_event_config_tab()
        self.setup_connection_tab()
        self.setup_antenna_config_tab()
        self.setup_detection_tab()
        self.setup_competition_tab()
        self.setup_database_tab()
        
        # Barra de estado simple
        self.status_label = QLabel("Aplicación iniciada")
        layout.addWidget(self.status_label)
        
    def setup_connection_tab(self):
        """Pestaña: Conexión con Interface RFID"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "Conexión RFID")
        
        layout = QVBoxLayout(tab)
        
        # Configuración de conexión
        config_group = QGroupBox("Configuración del Lector YR8900")
        config_layout = QVBoxLayout(config_group)
        
        # Host y puerto
        conn_layout = QHBoxLayout()
        conn_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit("192.168.0.178")
        conn_layout.addWidget(self.host_input)
        
        conn_layout.addWidget(QLabel("Puerto:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(4001)
        conn_layout.addWidget(self.port_input)
        
        config_layout.addLayout(conn_layout)
        layout.addWidget(config_group)
        
        # Estado de conexión
        status_group = QGroupBox("Estado de Conexión")
        status_layout = QVBoxLayout(status_group)
        
        self.connection_status = QLabel("Desconectado")
        self.connection_status.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        status_layout.addWidget(self.connection_status)
        
        # Botones de control
        buttons_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.clicked.connect(self.connect_scanner)
        buttons_layout.addWidget(self.connect_btn)
        
        self.test_btn = QPushButton("Test Básico")
        self.test_btn.clicked.connect(self.test_scanner)
        self.test_btn.setEnabled(False)
        buttons_layout.addWidget(self.test_btn)
        
        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.clicked.connect(self.disconnect_scanner)
        self.disconnect_btn.setEnabled(False)
        buttons_layout.addWidget(self.disconnect_btn)
        
        status_layout.addLayout(buttons_layout)
        layout.addWidget(status_group)
        
        # Log de conexión
        log_group = QGroupBox("Log de Conexión")
        log_layout = QVBoxLayout(log_group)
        
        self.connection_log = QTextEdit()
        self.connection_log.setMaximumHeight(200)
        self.connection_log.setReadOnly(True)
        log_layout.addWidget(self.connection_log)
        
        layout.addWidget(log_group)
        
    def setup_detection_tab(self):
        """Pestaña: Detección de Chips"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "Detección de Chips")
        
        layout = QVBoxLayout(tab)
        
        # Controles de scanning
        scan_group = QGroupBox("Control de Scanning")
        scan_layout = QHBoxLayout(scan_group)
        
        self.scan_single_btn = QPushButton("Scan Simple")
        self.scan_single_btn.clicked.connect(self.scan_single)
        self.scan_single_btn.setEnabled(False)
        scan_layout.addWidget(self.scan_single_btn)
        
        self.scan_continuous_btn = QPushButton("Scan Continuo (5s)")
        self.scan_continuous_btn.clicked.connect(self.scan_continuous)
        self.scan_continuous_btn.setEnabled(False)
        scan_layout.addWidget(self.scan_continuous_btn)
        
        self.clear_tags_btn = QPushButton("Limpiar Lista")
        self.clear_tags_btn.clicked.connect(self.clear_tags)
        scan_layout.addWidget(self.clear_tags_btn)
        
        scan_layout.addStretch()
        
        # Contador
        self.tag_counter = QLabel("Chips detectados: 0")
        self.tag_counter.setStyleSheet("font-weight: bold;")
        scan_layout.addWidget(self.tag_counter)
        
        layout.addWidget(scan_group)
        
        # Tabla de chips detectados
        table_group = QGroupBox("Chips Detectados")
        table_layout = QVBoxLayout(table_group)
        
        self.tags_table = QTableWidget()
        self.tags_table.setColumnCount(4)
        self.tags_table.setHorizontalHeaderLabels(["Chip", "Antena", "Hora", "EPC"])
        
        # Configurar tabla
        header = self.tags_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tags_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.tags_table)
        
        layout.addWidget(table_group)
        
    def setup_competition_tab(self):
        """Pestaña: Manejo de Competencia"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "Competencia")
        
        layout = QVBoxLayout(tab)
        
        # Configuración de evento
        event_group = QGroupBox("Configuración del Evento")
        event_layout = QVBoxLayout(event_group)
        
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Nombre del evento:"))
        self.event_name = QLineEdit("Competencia RFID")
        info_layout.addWidget(self.event_name)
        
        info_layout.addWidget(QLabel("Fecha:"))
        self.event_date = QLineEdit("2025-09-21")
        info_layout.addWidget(self.event_date)
        
        event_layout.addLayout(info_layout)
        layout.addWidget(event_group)
        
        # Control de cronometraje
        timing_group = QGroupBox("Control de Cronometraje")
        timing_layout = QVBoxLayout(timing_group)
        
        timing_buttons = QHBoxLayout()
        
        self.start_race_btn = QPushButton("Iniciar Carrera")
        self.start_race_btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        self.start_race_btn.clicked.connect(self.start_race)
        timing_buttons.addWidget(self.start_race_btn)
        
        self.stop_race_btn = QPushButton("Finalizar Carrera")
        self.stop_race_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.stop_race_btn.setEnabled(False)
        self.stop_race_btn.clicked.connect(self.stop_race)
        timing_buttons.addWidget(self.stop_race_btn)
        
        timing_layout.addLayout(timing_buttons)
        
        # Estado de la carrera
        self.race_status = QLabel("Carrera no iniciada")
        self.race_status.setStyleSheet("font-size: 16px; font-weight: bold;")
        timing_layout.addWidget(self.race_status)
        
        layout.addWidget(timing_group)
        
        # Resultados
        results_group = QGroupBox("Resultados de la Carrera")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Posición", "Chip", "Tiempo", "Estado"])
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group)
        
    def setup_database_tab(self):
        """Pestaña: Base de Datos (preparada para Firebase)"""
        tab = QWidget()
        self.tab_widget.addTab(tab, "Base de Datos")
        
        layout = QVBoxLayout(tab)
        
        # Estado de conexión a DB
        db_status_group = QGroupBox("Estado de Base de Datos")
        db_status_layout = QVBoxLayout(db_status_group)
        
        self.db_status = QLabel("Sin conexión a base de datos")
        self.db_status.setStyleSheet("font-weight: bold; color: orange;")
        db_status_layout.addWidget(self.db_status)
        
        # Botones de DB (preparados para Firebase)
        db_buttons = QHBoxLayout()
        
        self.connect_firebase_btn = QPushButton("Conectar Firebase")
        self.connect_firebase_btn.setEnabled(False)  # Disabled hasta implementar
        self.connect_firebase_btn.setToolTip("Funcionalidad pendiente de implementar")
        db_buttons.addWidget(self.connect_firebase_btn)
        
        self.export_data_btn = QPushButton("Exportar Datos")
        self.export_data_btn.clicked.connect(self.export_data)
        db_buttons.addWidget(self.export_data_btn)
        
        db_status_layout.addLayout(db_buttons)
        layout.addWidget(db_status_group)
        
        # Configuración local
        local_group = QGroupBox("Almacenamiento Local (Temporal)")
        local_layout = QVBoxLayout(local_group)
        
        self.local_storage_info = QTextEdit()
        self.local_storage_info.setMaximumHeight(150)
        self.local_storage_info.setReadOnly(True)
        self.local_storage_info.setPlainText("Datos se almacenan localmente mientras se implementa Firebase.\nTodos los chips detectados se mantienen en memoria.")
        local_layout.addWidget(self.local_storage_info)
        
        layout.addWidget(local_group)
        
        # Placeholder para futuras funcionalidades
        future_group = QGroupBox("Funcionalidades Futuras")
        future_layout = QVBoxLayout(future_group)
        
        future_info = QLabel("• Sincronización automática con Firebase\n• Backup en tiempo real\n• Análisis de datos históricos\n• Reportes automáticos")
        future_layout.addWidget(future_info)
        
        layout.addWidget(future_group)
        
    # Métodos de funcionalidad
    
    def log_connection(self, message):
        """Agregar mensaje al log de conexión"""
        self.connection_log.append(f"[{self.get_timestamp()}] {message}")
        self.status_label.setText(message)
        
    def get_timestamp(self):
        """Obtener timestamp actual"""
        return datetime.now().strftime('%H:%M:%S')
        
    def connect_scanner(self):
        """Conectar al scanner"""
        host = self.host_input.text().strip()
        port = self.port_input.value()
        
        self.scanner.host = host
        self.scanner.port = port
        
        self.log_connection("Intentando conectar...")
        if self.scanner.connect():
            self.connection_status.setText("Conectado")
            self.connection_status.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
            
            # Habilitar botones
            self.connect_btn.setEnabled(False)
            self.test_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(True)
            self.scan_single_btn.setEnabled(True)
            self.scan_continuous_btn.setEnabled(True)
            
            self.log_connection("Conectado exitosamente")
        else:
            self.log_connection("Error de conexión")
            
    def disconnect_scanner(self):
        """Desconectar del scanner"""
        self.scanner.disconnect()
        self.connection_status.setText("Desconectado")
        self.connection_status.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        
        # Deshabilitar botones
        self.connect_btn.setEnabled(True)
        self.test_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(False)
        self.scan_single_btn.setEnabled(False)
        self.scan_continuous_btn.setEnabled(False)
        
        self.log_connection("Desconectado")
        
    def test_scanner(self):
        """Test básico del scanner"""
        self.log_connection("Ejecutando test básico...")
        if self.scanner.test_basic_command():
            self.log_connection("Test básico exitoso")
        else:
            self.log_connection("Test básico falló")
            
    def scan_single(self):
        """Scan simple"""
        tags = self.scanner.scan_with_parsing()
        if tags:
            for tag in tags:
                self.add_tag_to_table(tag)
            self.log_connection(f"Scan simple: {len(tags)} chip(s) detectado(s)")
        else:
            self.log_connection("Scan simple: sin chips detectados")
            
    def scan_continuous(self):
        """Scan continuo"""
        self.log_connection("Iniciando scan continuo...")
        tags = self.scanner.continuous_scan_simple(5)
        
        for tag in tags:
            self.add_tag_to_table(tag)
            
        self.update_tag_counter()
        self.log_connection(f"Scan continuo completado: {len(tags)} chips únicos")
        
    def start_race(self):
        """Iniciar carrera"""
        self.race_start_time = datetime.now()
        self.race_active = True
        self.race_results.clear()
        
        self.race_status.setText(f"Carrera EN CURSO - Iniciada: {self.race_start_time.strftime('%H:%M:%S')}")
        self.race_status.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
        
        self.start_race_btn.setEnabled(False)
        self.stop_race_btn.setEnabled(True)
        
        self.results_table.setRowCount(0)
        self.log_connection("Carrera iniciada")

    def stop_race(self):
        """Finalizar carrera"""
        self.race_active = False
        
        self.race_status.setText("Carrera FINALIZADA")
        self.race_status.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")
        
        self.start_race_btn.setEnabled(True)
        self.stop_race_btn.setEnabled(False)
        
        self.log_connection("Carrera finalizada")
        
    def add_tag_to_table(self, tag):
        """Agregar tag a la tabla usando el sistema integrado"""
        tag_number = tag['number']
        
        # Procesar con race tracker si existe
        if hasattr(self, 'race_tracker') and self.race_tracker:
            reading = self.race_tracker.process_chip_reading(
                tag_number, 
                tag['antenna'], 
                tag['timestamp']
            )
            
            # Solo procesar si la lectura es válida (categoría activa, etc.)
            if not reading:
                return  # Chip ignorado (no registrado o categoría inactiva)
            
            # Obtener estado del participante
            participant_status = self.race_tracker.get_participant_status(tag_number)
            if participant_status:
                self.log_connection(f"Participante {tag_number}: {participant_status.status}")
        
        # Continuar con lógica original de tabla
        if tag_number in self.detected_tags:
            return
            
        self.detected_tags[tag_number] = tag
        
        row = self.tags_table.rowCount()
        self.tags_table.insertRow(row)
        
        self.tags_table.setItem(row, 0, QTableWidgetItem(tag_number))
        self.tags_table.setItem(row, 1, QTableWidgetItem(str(tag['antenna'])))
        self.tags_table.setItem(row, 2, QTableWidgetItem(tag['timestamp'].strftime('%H:%M:%S')))
        self.tags_table.setItem(row, 3, QTableWidgetItem(tag['epc_hex'][:16] + "..."))
        
        self.update_tag_counter()

    def update_results_table(self):
        """Actualizar tabla de resultados de carrera"""
        self.results_table.setRowCount(0)
        
        # Ordenar por tiempo
        sorted_results = sorted(self.race_results.items(), key=lambda x: x[1]['time'])
        
        for i, (chip, result) in enumerate(sorted_results):
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            self.results_table.setItem(row, 0, QTableWidgetItem(str(i + 1)))
            self.results_table.setItem(row, 1, QTableWidgetItem(chip))
            self.results_table.setItem(row, 2, QTableWidgetItem(f"{result['time']:.3f}s"))
            self.results_table.setItem(row, 3, QTableWidgetItem("Completado"))
        
    def clear_tags(self):
        """Limpiar lista de tags"""
        self.detected_tags.clear()
        self.tags_table.setRowCount(0)
        self.update_tag_counter()
        self.log_connection("Lista de chips limpiada")
        
    def update_tag_counter(self):
        """Actualizar contador de tags"""
        count = len(self.detected_tags)
        self.tag_counter.setText(f"Chips detectados: {count}")
        
    def export_data(self):
        """Exportar datos (placeholder)"""
        self.log_connection("Función de exportación pendiente de implementar")


    def setup_antenna_config_tab(self):
        """Pestaña: Configuración de Antenas - usando widget separado"""
        # Crear widget de configuración de antenas
        self.antenna_config_widget = AntennaConfigWidget()
        
        # Conectar señal para recibir configuración aplicada
        self.antenna_config_widget.config_applied.connect(self.on_antenna_config_applied)
        
        # Agregar widget como pestaña
        self.tab_widget.addTab(self.antenna_config_widget, "Config. Antenas")

    def on_antenna_config_applied(self, config_data):
        """Manejar configuración de antenas aplicada"""
        # Crear resumen de configuración
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
        
        self.log_connection("Configuración de antenas aplicada:")
        for line in config_summary:
            self.log_connection(f"  • {line}")
        
        # Actualizar tracker integrado si existe
        if hasattr(self, 'race_tracker') and self.race_tracker:
            self.race_tracker.set_antenna_config(config_data)
        
        enabled_count = len(config_summary)
        self.log_connection(f"Sistema configurado con {enabled_count} antenas activas")

    def setup_event_config_tab(self):
        """Pestaña: Configuración de Eventos Multi-Categoría"""
        self.event_config_widget = EventConfigWidget()
        
        # Conectar señales
        self.event_config_widget.category_started.connect(self.on_category_started)
        self.event_config_widget.category_finished.connect(self.on_category_finished)
        
        self.tab_widget.addTab(self.event_config_widget, "Gestión de Eventos")

    def on_category_started(self, category_id):
        """Manejar inicio de categoría"""
        self.log_connection(f"Categoría iniciada: {category_id}")

    def on_category_finished(self, category_id):
        """Manejar finalización de categoría"""
        self.log_connection(f"Categoría finalizada: {category_id}")

    def on_category_started(self, category_id):
        """Manejar inicio de categoría"""
        # Inicializar race tracker si no existe
        if not hasattr(self, 'race_tracker') or not self.race_tracker:
            if hasattr(self, 'event_config_widget'):
                event_manager = self.event_config_widget.get_event_manager()
                self.race_tracker = IntegratedRaceTracker(event_manager)
                
                # Aplicar configuración de antenas si existe
                if hasattr(self, 'antenna_config_widget'):
                    antenna_config = self.antenna_config_widget.get_current_config()
                    enabled_antennas = {ant_id: config for ant_id, config in antenna_config.items() 
                                    if config['enabled']}
                    self.race_tracker.set_antenna_config(enabled_antennas)
        
        self.log_connection(f"Categoría iniciada: {category_id}")
        
    def on_category_finished(self, category_id):
        """Manejar finalización de categoría"""
        self.log_connection(f"Categoría finalizada: {category_id}")