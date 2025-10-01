from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QGroupBox, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QComboBox, QTabWidget, QTextEdit)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont
from datetime import datetime

class RaceMonitoringWidget(QWidget):
    """Widget para monitoreo de carreras en tiempo real"""
    
    # Señales
    refresh_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.race_tracker = None
        self.event_manager = None
        self.setup_ui()
        
        # Timer para actualización automática
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_data)
        self.refresh_timer.start(2000)  # Actualizar cada 2 segundos
        
    def setup_ui(self):
        """Configurar interfaz del widget"""
        layout = QVBoxLayout(self)
        
        # Controles superiores
        controls_group = QGroupBox("Control de Monitoreo")
        controls_layout = QHBoxLayout(controls_group)
        
        # Selector de categoría
        controls_layout.addWidget(QLabel("Categoría:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas las categorías")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        controls_layout.addWidget(self.category_combo)
        
        # Botones de control
        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_all_data)
        controls_layout.addWidget(self.refresh_btn)
        
        self.auto_refresh_btn = QPushButton("Auto: ON")
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        self.auto_refresh_btn.setStyleSheet("background-color: green; color: white;")
        controls_layout.addWidget(self.auto_refresh_btn)
        
        controls_layout.addStretch()
        
        # Estado del sistema
        self.system_status_label = QLabel("Sistema: Desconectado")
        self.system_status_label.setStyleSheet("font-weight: bold;")
        controls_layout.addWidget(self.system_status_label)
        
        layout.addWidget(controls_group)
        
        # Pestañas para diferentes vistas
        self.monitoring_tabs = QTabWidget()
        
        # Tab 1: Resumen de categorías
        self.setup_categories_overview_tab()
        
        # Tab 2: Participantes en tiempo real
        self.setup_participants_tab()
        
        # Tab 3: Estadísticas detalladas
        self.setup_statistics_tab()
        
        layout.addWidget(self.monitoring_tabs)
        
    def setup_categories_overview_tab(self):
        """Tab con resumen de todas las categorías"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "Resumen de Categorías")
        
        layout = QVBoxLayout(tab)
        
        # Tabla de categorías con estado
        self.categories_overview_table = QTableWidget()
        self.categories_overview_table.setColumnCount(8)
        self.categories_overview_table.setHorizontalHeaderLabels([
            "Categoría", "Estado", "Hora Inicio", "Participantes", 
            "No Iniciados", "En Carrera", "Finalizados", "Último Checkpoint"
        ])
        
        # Configurar tabla
        header = self.categories_overview_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        self.categories_overview_table.setAlternatingRowColors(True)
        layout.addWidget(self.categories_overview_table)
        
    def setup_participants_tab(self):
        """Tab con participantes en tiempo real"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "Participantes")
        
        layout = QVBoxLayout(tab)
        
        # Filtros
        filters_layout = QHBoxLayout()
        
        filters_layout.addWidget(QLabel("Mostrar:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems([
            "Todos", "No iniciados", "En carrera", "Finalizados"
        ])
        self.status_filter_combo.currentTextChanged.connect(self.refresh_participants_table)
        filters_layout.addWidget(self.status_filter_combo)
        
        filters_layout.addStretch()
        
        # Contadores
        self.participants_count_label = QLabel("Total: 0 participantes")
        self.participants_count_label.setStyleSheet("font-weight: bold;")
        filters_layout.addWidget(self.participants_count_label)
        
        layout.addLayout(filters_layout)
        
        # Tabla de participantes
        self.participants_table = QTableWidget()
        self.participants_table.setColumnCount(8)
        self.participants_table.setHorizontalHeaderLabels([
            "Chip", "Categoría", "Estado", "Tiempo Inicio", 
            "Tiempo Actual", "Checkpoints", "Última Lectura", "Antena"
        ])
        
        # Configurar tabla
        header = self.participants_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        self.participants_table.setAlternatingRowColors(True)
        layout.addWidget(self.participants_table)
        
    def setup_statistics_tab(self):
        """Tab con estadísticas detalladas"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "Estadísticas")
        
        layout = QVBoxLayout(tab)
        
        # Estadísticas generales
        stats_group = QGroupBox("Estadísticas en Tiempo Real")
        stats_layout = QVBoxLayout(stats_group)
        
        self.statistics_text = QTextEdit()
        self.statistics_text.setReadOnly(True)
        self.statistics_text.setMaximumHeight(200)
        stats_layout.addWidget(self.statistics_text)
        
        layout.addWidget(stats_group)
        
        # Log de eventos recientes
        events_group = QGroupBox("Eventos Recientes")
        events_layout = QVBoxLayout(events_group)
        
        self.events_log = QTextEdit()
        self.events_log.setReadOnly(True)
        self.events_log.setStyleSheet("font-family: 'Courier New'; font-size: 9pt;")
        events_layout.addWidget(self.events_log)
        
        layout.addWidget(events_group)
        
    def set_race_tracker(self, race_tracker):
        """Establecer el tracker de carreras"""
        self.race_tracker = race_tracker
        if race_tracker:
            self.event_manager = race_tracker.event_manager
            self.refresh_category_combo()
            self.system_status_label.setText("Sistema: Conectado")
            self.system_status_label.setStyleSheet("font-weight: bold; color: green;")
        
    def refresh_category_combo(self):
        """Actualizar combo de categorías"""
        if not self.event_manager:
            return
            
        current_text = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("Todas las categorías")
        
        for cat_id in self.event_manager.get_categories_by_time():
            category = self.event_manager.categories[cat_id]
            self.category_combo.addItem(f"{cat_id} - {category.name}")
            
        # Restaurar selección si es posible
        index = self.category_combo.findText(current_text)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        
    def on_category_changed(self):
        """Manejar cambio de categoría seleccionada"""
        self.refresh_participants_table()
        
    def toggle_auto_refresh(self):
        """Alternar actualización automática"""
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
            self.auto_refresh_btn.setText("Auto: OFF")
            self.auto_refresh_btn.setStyleSheet("background-color: red; color: white;")
        else:
            self.refresh_timer.start(2000)
            self.auto_refresh_btn.setText("Auto: ON")
            self.auto_refresh_btn.setStyleSheet("background-color: green; color: white;")
            
    def refresh_all_data(self):
        """Actualizar todos los datos"""
        if not self.race_tracker or not self.event_manager:
            return
            
        self.refresh_categories_overview()
        self.refresh_participants_table()
        self.refresh_statistics()
        
    def refresh_categories_overview(self):
        """Actualizar resumen de categorías"""
        if not self.event_manager:
            return
            
        self.categories_overview_table.setRowCount(0)
        
        for cat_id in self.event_manager.get_categories_by_time():
            category_info = self.event_manager.get_category_info(cat_id)
            category = category_info['category']
            status = category_info['status']
            
            # Obtener estadísticas de participantes
            if self.race_tracker:
                results = self.race_tracker.get_category_results(cat_id)
                not_started = len([p for p in results if p.status == 'not_started'])
                in_progress = len([p for p in results if p.status == 'in_progress'])
                finished = len([p for p in results if p.status == 'finished'])
                total_participants = len(results)
                
                # Última actividad
                last_checkpoint = "N/A"
                if results:
                    last_active = max((p for p in results if p.last_reading), 
                                    key=lambda x: x.last_reading.timestamp, default=None)
                    if last_active and last_active.last_reading:
                        last_checkpoint = last_active.last_reading.timestamp.strftime('%H:%M:%S')
            else:
                not_started = in_progress = finished = total_participants = 0
                last_checkpoint = "N/A"
            
            # Agregar fila
            row = self.categories_overview_table.rowCount()
            self.categories_overview_table.insertRow(row)
            
            self.categories_overview_table.setItem(row, 0, QTableWidgetItem(f"{cat_id} - {category.name}"))
            
            # Estado con color
            status_item = QTableWidgetItem(status.value.title())
            if status.value == "active":
                status_item.setBackground(Qt.GlobalColor.green)
            elif status.value == "finished":
                status_item.setBackground(Qt.GlobalColor.gray)
            self.categories_overview_table.setItem(row, 1, status_item)
            
            # Hora de inicio
            start_time = category_info.get('actual_start_time')
            start_time_str = start_time.strftime('%H:%M:%S') if start_time else "No iniciada"
            self.categories_overview_table.setItem(row, 2, QTableWidgetItem(start_time_str))
            
            self.categories_overview_table.setItem(row, 3, QTableWidgetItem(str(total_participants)))
            self.categories_overview_table.setItem(row, 4, QTableWidgetItem(str(not_started)))
            self.categories_overview_table.setItem(row, 5, QTableWidgetItem(str(in_progress)))
            self.categories_overview_table.setItem(row, 6, QTableWidgetItem(str(finished)))
            self.categories_overview_table.setItem(row, 7, QTableWidgetItem(last_checkpoint))
            
    def refresh_participants_table(self):
        """Actualizar tabla de participantes"""
        if not self.race_tracker:
            return
            
        self.participants_table.setRowCount(0)
        
        # Determinar categoría seleccionada
        selected_category = None
        current_text = self.category_combo.currentText()
        if current_text != "Todas las categorías" and " - " in current_text:
            selected_category = current_text.split(" - ")[0]
            
        # Filtrar por estado
        status_filter = self.status_filter_combo.currentText().lower()
        
        # Obtener participantes
        all_participants = []
        if selected_category:
            all_participants = self.race_tracker.get_category_results(selected_category)
        else:
            # Todas las categorías
            for cat_id in self.event_manager.categories.keys():
                all_participants.extend(self.race_tracker.get_category_results(cat_id))
        
        # Filtrar por estado
        if status_filter != "todos":
            status_map = {
                "no iniciados": "not_started",
                "en carrera": "in_progress", 
                "finalizados": "finished"
            }
            filter_status = status_map.get(status_filter)
            if filter_status:
                all_participants = [p for p in all_participants if p.status == filter_status]
        
        # Actualizar contador
        self.participants_count_label.setText(f"Total: {len(all_participants)} participantes")
        
        # Llenar tabla
        for participant in all_participants:
            row = self.participants_table.rowCount()
            self.participants_table.insertRow(row)
            
            self.participants_table.setItem(row, 0, QTableWidgetItem(participant.chip_id))
            self.participants_table.setItem(row, 1, QTableWidgetItem(participant.category_id))
            
            # Estado con color
            status_item = QTableWidgetItem(participant.status.replace('_', ' ').title())
            if participant.status == "in_progress":
                status_item.setBackground(Qt.GlobalColor.yellow)
            elif participant.status == "finished":
                status_item.setBackground(Qt.GlobalColor.green)
            self.participants_table.setItem(row, 2, status_item)
            
            # Tiempos
            start_time_str = participant.start_time.strftime('%H:%M:%S') if participant.start_time else "N/A"
            self.participants_table.setItem(row, 3, QTableWidgetItem(start_time_str))
            
            # Tiempo actual/total
            if participant.status == "finished" and participant.total_time:
                time_str = f"{participant.total_time:.1f}s"
            elif participant.status == "in_progress" and participant.start_time:
                current_time = (datetime.now() - participant.start_time).total_seconds()
                time_str = f"{current_time:.1f}s (en curso)"
            else:
                time_str = "N/A"
            self.participants_table.setItem(row, 4, QTableWidgetItem(time_str))
            
            self.participants_table.setItem(row, 5, QTableWidgetItem(str(participant.checkpoints_passed)))
            
            # Última lectura
            if participant.last_reading:
                last_reading_str = participant.last_reading.timestamp.strftime('%H:%M:%S')
                antenna_str = str(participant.last_reading.antenna_id)
            else:
                last_reading_str = "N/A"
                antenna_str = "N/A"
                
            self.participants_table.setItem(row, 6, QTableWidgetItem(last_reading_str))
            self.participants_table.setItem(row, 7, QTableWidgetItem(antenna_str))
            
    def refresh_statistics(self):
        """Actualizar estadísticas"""
        if not self.race_tracker:
            return
            
        system_status = self.race_tracker.get_system_status()
        
        stats_text = f"""ESTADÍSTICAS DEL SISTEMA
{'='*30}
Categorías activas: {len(system_status['active_categories'])}
Participantes registrados: {system_status['registered_participants']}
Antenas configuradas: {system_status['configured_antennas']}
Total de lecturas: {system_status['total_readings']}

PARTICIPANTES ACTIVOS POR CATEGORÍA:
"""
        
        for cat_id, count in system_status['active_participants'].items():
            category_name = self.event_manager.categories[cat_id].name
            stats_text += f"• {cat_id} ({category_name}): {count} en carrera\n"
            
        stats_text += f"\nÚltima actualización: {datetime.now().strftime('%H:%M:%S')}"
        
        self.statistics_text.setPlainText(stats_text)
        
    def log_event(self, message):
        """Agregar evento al log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        self.events_log.append(log_message)
        
        # Mantener máximo 50 líneas en el log
        text = self.events_log.toPlainText()
        lines = text.split('\n')
        if len(lines) > 50:
            self.events_log.setPlainText('\n'.join(lines[-50:]))