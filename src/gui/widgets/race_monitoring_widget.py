import csv
import io
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QComboBox, QTabWidget, QTextEdit,
                            QFileDialog, QMessageBox, QSpinBox, QSizePolicy)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QColor
from datetime import datetime


def _fmt_time(total_seconds):
    """Formato MM:SS.mmm para tiempo en segundos (float)"""
    if total_seconds is None:
        return "N/A"
    total_ms = int(total_seconds * 1000)
    minutes = total_ms // 60000
    seconds = (total_ms % 60000) // 1000
    ms = total_ms % 1000
    return f"{minutes}:{seconds:02d}.{ms:03d}"


class RaceMonitoringWidget(QWidget):
    """Widget para monitoreo de carreras en tiempo real"""

    refresh_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.race_tracker = None
        self.event_manager = None
        self.setup_ui()

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all_data)
        self.refresh_timer.start(2000)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Controles superiores
        controls_group = QGroupBox("Control de Monitoreo")
        controls_layout = QHBoxLayout(controls_group)

        controls_layout.addWidget(QLabel("Distancia:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("Todas las categorías")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        controls_layout.addWidget(self.category_combo)

        self.refresh_btn = QPushButton("Actualizar")
        self.refresh_btn.clicked.connect(self.refresh_all_data)
        controls_layout.addWidget(self.refresh_btn)

        self.auto_refresh_btn = QPushButton("Auto: ON")
        self.auto_refresh_btn.clicked.connect(self.toggle_auto_refresh)
        self.auto_refresh_btn.setStyleSheet("background-color: green; color: white;")
        controls_layout.addWidget(self.auto_refresh_btn)

        self.export_btn = QPushButton("🗂 Exportar Resultados")
        self.export_btn.clicked.connect(self.export_all_results)
        self.export_btn.setStyleSheet("background-color: #1565C0; color: white; font-weight: bold;")
        controls_layout.addWidget(self.export_btn)

        controls_layout.addStretch()

        self.system_status_label = QLabel("Sistema: Desconectado")
        self.system_status_label.setStyleSheet("font-weight: bold;")
        controls_layout.addWidget(self.system_status_label)

        layout.addWidget(controls_group)

        self.monitoring_tabs = QTabWidget()
        self.setup_distances_overview_tab()
        self.setup_participants_tab()
        self.setup_statistics_tab()
        self.setup_podios_tab()
        self.setup_tiempos_parciales_tab()
        layout.addWidget(self.monitoring_tabs)

    # -------------------------------------------------------------------------
    # Tab 1: Resumen de Distancias
    # -------------------------------------------------------------------------

    def setup_distances_overview_tab(self):
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "Resumen de Distancias")

        layout = QVBoxLayout(tab)

        self.categories_overview_table = QTableWidget()
        self.categories_overview_table.setColumnCount(8)
        self.categories_overview_table.setHorizontalHeaderLabels([
            "Distancia", "Estado", "Hora Inicio", "Participantes",
            "No Iniciados", "En Carrera", "Finalizados", "Última Actividad"
        ])
        header = self.categories_overview_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.categories_overview_table.setAlternatingRowColors(True)
        layout.addWidget(self.categories_overview_table)

    # -------------------------------------------------------------------------
    # Tab 2: Participantes
    # -------------------------------------------------------------------------

    def setup_participants_tab(self):
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "Participantes")

        layout = QVBoxLayout(tab)

        filters_layout = QHBoxLayout()
        filters_layout.addWidget(QLabel("Mostrar:"))
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["Todos", "No iniciados", "En carrera", "Finalizados"])
        self.status_filter_combo.currentTextChanged.connect(self.refresh_participants_table)
        filters_layout.addWidget(self.status_filter_combo)
        filters_layout.addStretch()

        self.participants_count_label = QLabel("Total: 0 participantes")
        self.participants_count_label.setStyleSheet("font-weight: bold;")
        filters_layout.addWidget(self.participants_count_label)
        layout.addLayout(filters_layout)

        self.participants_table = QTableWidget()
        self.participants_table.setColumnCount(8)
        self.participants_table.setHorizontalHeaderLabels([
            "Chip", "Distancia", "Estado", "Tiempo Inicio",
            "Tiempo Actual", "Checkpoints", "Última Lectura", "Tipo"
        ])
        header = self.participants_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(7):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.participants_table.setAlternatingRowColors(True)
        layout.addWidget(self.participants_table)

    # -------------------------------------------------------------------------
    # Tab 3: Estadísticas
    # -------------------------------------------------------------------------

    def setup_statistics_tab(self):
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "Estadísticas")

        layout = QVBoxLayout(tab)

        stats_group = QGroupBox("Estadísticas en Tiempo Real")
        stats_layout = QVBoxLayout(stats_group)
        self.statistics_text = QTextEdit()
        self.statistics_text.setReadOnly(True)
        self.statistics_text.setMaximumHeight(200)
        stats_layout.addWidget(self.statistics_text)
        layout.addWidget(stats_group)

        events_group = QGroupBox("Eventos Recientes")
        events_layout = QVBoxLayout(events_group)
        self.events_log = QTextEdit()
        self.events_log.setReadOnly(True)
        self.events_log.setStyleSheet("font-family: 'Courier New'; font-size: 9pt;")
        events_layout.addWidget(self.events_log)
        layout.addWidget(events_group)

    # -------------------------------------------------------------------------
    # Tab 4: Podios por Distancia
    # -------------------------------------------------------------------------

    def setup_podios_tab(self):
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "🏆 Podios por Distancia")

        layout = QVBoxLayout(tab)

        # Controles del tab
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Distancia:"))

        self.podios_dist_combo = QComboBox()
        self.podios_dist_combo.addItem("Selecciona una distancia")
        self.podios_dist_combo.setMinimumWidth(200)
        self.podios_dist_combo.currentTextChanged.connect(self.refresh_podios)
        controls.addWidget(self.podios_dist_combo)

        controls.addWidget(QLabel("Top:"))
        self.podios_top_spin = QSpinBox()
        self.podios_top_spin.setRange(1, 20)
        self.podios_top_spin.setValue(3)
        self.podios_top_spin.valueChanged.connect(self.refresh_podios)
        controls.addWidget(self.podios_top_spin)

        update_btn = QPushButton("🔄 Actualizar Podios")
        update_btn.clicked.connect(self.refresh_podios)
        controls.addWidget(update_btn)

        controls.addSpacing(16)

        csv_btn = QPushButton("📊 CSV")
        csv_btn.setStyleSheet("background-color: #2E7D32; color: white;")
        csv_btn.clicked.connect(self.export_podios_csv)
        controls.addWidget(csv_btn)

        pdf_gen_btn = QPushButton("📄 PDF General")
        pdf_gen_btn.setStyleSheet("background-color: #C62828; color: white;")
        pdf_gen_btn.clicked.connect(lambda: self._pdf_not_available("General"))
        controls.addWidget(pdf_gen_btn)

        pdf_gen_btn2 = QPushButton("📄 PDF Género")
        pdf_gen_btn2.setStyleSheet("background-color: #1A237E; color: white;")
        pdf_gen_btn2.clicked.connect(lambda: self._pdf_not_available("Género"))
        controls.addWidget(pdf_gen_btn2)

        pdf_cat_btn = QPushButton("📄 PDF Categorías")
        pdf_cat_btn.setStyleSheet("background-color: #004D40; color: white;")
        pdf_cat_btn.clicked.connect(lambda: self._pdf_not_available("Categorías"))
        controls.addWidget(pdf_cat_btn)

        pdf_rel_btn = QPushButton("📄 PDF Relator")
        pdf_rel_btn.setStyleSheet("background-color: #E65100; color: white;")
        pdf_rel_btn.clicked.connect(lambda: self._pdf_not_available("Relator"))
        controls.addWidget(pdf_rel_btn)

        controls.addStretch()
        layout.addLayout(controls)

        # Tabla de podios
        self.podios_table = QTableWidget()
        self.podios_table.setColumnCount(6)
        self.podios_table.setHorizontalHeaderLabels([
            "Pos", "Chip", "Distancia", "Tiempo Total", "Hora Llegada", "Estado"
        ])
        header = self.podios_table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.podios_table.setAlternatingRowColors(True)

        # Placeholder
        self.podios_placeholder = QLabel(
            "Selecciona una distancia para ver los podios clasificados por "
            "categoría de premiación (género/edad)."
        )
        self.podios_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.podios_placeholder.setStyleSheet("color: gray; font-style: italic;")
        self.podios_placeholder.setWordWrap(True)

        layout.addWidget(self.podios_placeholder)
        layout.addWidget(self.podios_table)
        self.podios_table.hide()

    # -------------------------------------------------------------------------
    # Tab 5: Tiempos Parciales
    # -------------------------------------------------------------------------

    def setup_tiempos_parciales_tab(self):
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "⏱ Tiempos Parciales")

        layout = QVBoxLayout(tab)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Distancia:"))

        self.parciales_dist_combo = QComboBox()
        self.parciales_dist_combo.addItem("Todas las distancias")
        self.parciales_dist_combo.setMinimumWidth(200)
        self.parciales_dist_combo.currentTextChanged.connect(self.refresh_tiempos_parciales)
        controls.addWidget(self.parciales_dist_combo)

        update_btn = QPushButton("🔄 Actualizar")
        update_btn.clicked.connect(self.refresh_tiempos_parciales)
        controls.addWidget(update_btn)

        csv_btn = QPushButton("📊 Exportar CSV")
        csv_btn.setStyleSheet("background-color: #2E7D32; color: white;")
        csv_btn.clicked.connect(self.export_parciales_csv)
        controls.addWidget(csv_btn)

        controls.addStretch()
        layout.addLayout(controls)

        self.parciales_table = QTableWidget()
        self.parciales_table.setAlternatingRowColors(True)
        layout.addWidget(self.parciales_table)

        self.parciales_placeholder = QLabel(
            "No hay tiempos parciales disponibles. Los tiempos parciales se registran "
            "cuando los chips pasan por antenas de tipo 'checkpoint'."
        )
        self.parciales_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parciales_placeholder.setStyleSheet("color: gray; font-style: italic;")
        self.parciales_placeholder.setWordWrap(True)
        layout.addWidget(self.parciales_placeholder)

    # -------------------------------------------------------------------------
    # Conexión con el tracker
    # -------------------------------------------------------------------------

    def set_race_tracker(self, race_tracker):
        self.race_tracker = race_tracker
        if race_tracker:
            self.event_manager = race_tracker.event_manager
            self.refresh_category_combo()
            self.refresh_podios_dist_combo()
            self.refresh_parciales_dist_combo()
            self.system_status_label.setText("Sistema: Conectado")
            self.system_status_label.setStyleSheet("font-weight: bold; color: green;")

    def refresh_category_combo(self):
        if not self.event_manager:
            return
        current_text = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("Todas las categorías")
        for cat_id in self.event_manager.get_categories_by_time():
            category = self.event_manager.categories[cat_id]
            self.category_combo.addItem(f"{cat_id} - {category.name}")
        index = self.category_combo.findText(current_text)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

    def refresh_podios_dist_combo(self):
        """Poblar el dropdown de distancias del tab Podios"""
        if not self.event_manager:
            return
        current_text = self.podios_dist_combo.currentText()
        self.podios_dist_combo.blockSignals(True)
        self.podios_dist_combo.clear()
        self.podios_dist_combo.addItem("Selecciona una distancia")
        for cat_id in self.event_manager.get_categories_by_time():
            category = self.event_manager.categories[cat_id]
            label = f"{cat_id}" if not category.name or category.name == cat_id else f"{cat_id} — {category.name}"
            self.podios_dist_combo.addItem(label, userData=cat_id)
        self.podios_dist_combo.blockSignals(False)
        # Restaurar selección previa si es posible
        index = self.podios_dist_combo.findText(current_text)
        if index >= 0:
            self.podios_dist_combo.setCurrentIndex(index)

    def refresh_parciales_dist_combo(self):
        """Poblar el dropdown de distancias del tab Tiempos Parciales"""
        if not self.event_manager:
            return
        current_text = self.parciales_dist_combo.currentText()
        self.parciales_dist_combo.blockSignals(True)
        self.parciales_dist_combo.clear()
        self.parciales_dist_combo.addItem("Todas las distancias", userData=None)
        for cat_id in self.event_manager.get_categories_by_time():
            category = self.event_manager.categories[cat_id]
            label = f"{cat_id}" if not category.name or category.name == cat_id else f"{cat_id} — {category.name}"
            self.parciales_dist_combo.addItem(label, userData=cat_id)
        self.parciales_dist_combo.blockSignals(False)
        index = self.parciales_dist_combo.findText(current_text)
        if index >= 0:
            self.parciales_dist_combo.setCurrentIndex(index)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def on_category_changed(self):
        self.refresh_participants_table()

    def toggle_auto_refresh(self):
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
            self.auto_refresh_btn.setText("Auto: OFF")
            self.auto_refresh_btn.setStyleSheet("background-color: red; color: white;")
        else:
            self.refresh_timer.start(2000)
            self.auto_refresh_btn.setText("Auto: ON")
            self.auto_refresh_btn.setStyleSheet("background-color: green; color: white;")

    def refresh_all_data(self):
        if not self.race_tracker or not self.event_manager:
            return
        self.refresh_podios_dist_combo()
        self.refresh_parciales_dist_combo()
        self.refresh_category_combo()
        self.refresh_categories_overview()
        self.refresh_participants_table()
        self.refresh_statistics()
        active_tab = self.monitoring_tabs.currentIndex()
        if active_tab == 3:
            self.refresh_podios()
        elif active_tab == 4:
            self.refresh_tiempos_parciales()

    # -------------------------------------------------------------------------
    # Refresh: Resumen de Distancias
    # -------------------------------------------------------------------------

    def refresh_categories_overview(self):
        if not self.event_manager:
            return
        self.categories_overview_table.setRowCount(0)

        for cat_id in self.event_manager.get_categories_by_time():
            category_info = self.event_manager.get_category_info(cat_id)
            category = category_info['category']
            status = category_info['status']

            results = self.race_tracker.get_category_results(cat_id) if self.race_tracker else []
            not_started = len([p for p in results if p.status == 'not_started'])
            in_progress = len([p for p in results if p.status == 'in_progress'])
            finished = len([p for p in results if p.status == 'finished'])
            total_participants = len(results)

            last_checkpoint = "N/A"
            active_results = [p for p in results if p.last_reading]
            if active_results:
                last_active = max(active_results, key=lambda x: x.last_reading.timestamp)
                last_checkpoint = last_active.last_reading.timestamp.strftime('%H:%M:%S')

            row = self.categories_overview_table.rowCount()
            self.categories_overview_table.insertRow(row)

            self.categories_overview_table.setItem(row, 0, QTableWidgetItem(f"{cat_id} - {category.name}"))

            status_item = QTableWidgetItem(status.value.title())
            if status.value == "active":
                status_item.setBackground(Qt.GlobalColor.green)
            elif status.value == "finished":
                status_item.setBackground(Qt.GlobalColor.gray)
            self.categories_overview_table.setItem(row, 1, status_item)

            start_time = category_info.get('actual_start_time')
            start_time_str = start_time.strftime('%H:%M:%S') if start_time else "No iniciada"
            self.categories_overview_table.setItem(row, 2, QTableWidgetItem(start_time_str))
            self.categories_overview_table.setItem(row, 3, QTableWidgetItem(str(total_participants)))
            self.categories_overview_table.setItem(row, 4, QTableWidgetItem(str(not_started)))
            self.categories_overview_table.setItem(row, 5, QTableWidgetItem(str(in_progress)))
            self.categories_overview_table.setItem(row, 6, QTableWidgetItem(str(finished)))
            self.categories_overview_table.setItem(row, 7, QTableWidgetItem(last_checkpoint))

    # -------------------------------------------------------------------------
    # Refresh: Participantes
    # -------------------------------------------------------------------------

    def refresh_participants_table(self):
        if not self.race_tracker:
            return
        self.participants_table.setRowCount(0)

        selected_category = None
        current_text = self.category_combo.currentText()
        if current_text != "Todas las categorías" and " - " in current_text:
            selected_category = current_text.split(" - ")[0]

        status_filter = self.status_filter_combo.currentText().lower()

        all_participants = []
        if selected_category:
            all_participants = self.race_tracker.get_category_results(selected_category)
        else:
            for cat_id in self.event_manager.categories.keys():
                all_participants.extend(self.race_tracker.get_category_results(cat_id))

        if status_filter != "todos":
            status_map = {"no iniciados": "not_started", "en carrera": "in_progress", "finalizados": "finished"}
            filter_status = status_map.get(status_filter)
            if filter_status:
                all_participants = [p for p in all_participants if p.status == filter_status]

        self.participants_count_label.setText(f"Total: {len(all_participants)} participantes")

        for participant in all_participants:
            row = self.participants_table.rowCount()
            self.participants_table.insertRow(row)

            self.participants_table.setItem(row, 0, QTableWidgetItem(participant.chip_id))
            self.participants_table.setItem(row, 1, QTableWidgetItem(participant.category_id))

            status_item = QTableWidgetItem(participant.status.replace('_', ' ').title())
            if participant.status == "in_progress":
                status_item.setBackground(Qt.GlobalColor.yellow)
            elif participant.status == "finished":
                status_item.setBackground(Qt.GlobalColor.green)
            self.participants_table.setItem(row, 2, status_item)

            start_time_str = participant.start_time.strftime('%H:%M:%S') if participant.start_time else "N/A"
            self.participants_table.setItem(row, 3, QTableWidgetItem(start_time_str))

            if participant.status == "finished" and participant.total_time is not None:
                time_str = _fmt_time(participant.total_time)
            elif participant.status == "in_progress" and participant.start_time:
                elapsed = (datetime.now() - participant.start_time).total_seconds()
                time_str = _fmt_time(elapsed) + " (en curso)"
            else:
                time_str = "N/A"
            self.participants_table.setItem(row, 4, QTableWidgetItem(time_str))
            self.participants_table.setItem(row, 5, QTableWidgetItem(str(participant.checkpoints_passed)))

            if participant.last_reading:
                last_reading_str = participant.last_reading.timestamp.strftime('%H:%M:%S')
                reading_type = participant.last_reading.reading_type.replace('_', ' ').title()
            else:
                last_reading_str = "-"
                reading_type = "-"

            self.participants_table.setItem(row, 6, QTableWidgetItem(last_reading_str))
            self.participants_table.setItem(row, 7, QTableWidgetItem(reading_type))

    # -------------------------------------------------------------------------
    # Refresh: Estadísticas
    # -------------------------------------------------------------------------

    def refresh_statistics(self):
        if not self.race_tracker:
            return
        system_status = self.race_tracker.get_system_status()

        stats_text = (
            f"ESTADÍSTICAS DEL SISTEMA\n{'='*30}\n"
            f"Categorías activas: {len(system_status['active_categories'])}\n"
            f"Participantes registrados: {system_status['registered_participants']}\n"
            f"Antenas configuradas: {system_status['configured_antennas']}\n"
            f"Total de lecturas: {system_status['total_readings']}\n\n"
            f"PARTICIPANTES ACTIVOS POR CATEGORÍA:\n"
        )
        for cat_id, count in system_status['active_participants'].items():
            category_name = self.event_manager.categories[cat_id].name
            stats_text += f"• {cat_id} ({category_name}): {count} en carrera\n"
        stats_text += f"\nÚltima actualización: {datetime.now().strftime('%H:%M:%S')}"
        self.statistics_text.setPlainText(stats_text)

    # -------------------------------------------------------------------------
    # Refresh: Podios por Distancia
    # -------------------------------------------------------------------------

    def refresh_podios(self):
        if not self.race_tracker or not self.event_manager:
            return

        cat_id = self.podios_dist_combo.currentData()
        if not cat_id:
            self.podios_table.hide()
            self.podios_placeholder.show()
            return

        top_n = self.podios_top_spin.value()
        results = self.race_tracker.get_category_results(cat_id)
        finished = [p for p in results if p.status == 'finished' and p.total_time is not None]
        finished.sort(key=lambda x: x.total_time)
        top = finished[:top_n]

        self.podios_table.setRowCount(0)
        if not top:
            self.podios_table.hide()
            self.podios_placeholder.setText(
                f"No hay finalizados registrados para '{cat_id}'."
            )
            self.podios_placeholder.show()
            return

        self.podios_placeholder.hide()
        self.podios_table.show()

        medal_colors = {1: QColor(255, 215, 0), 2: QColor(192, 192, 192), 3: QColor(205, 127, 50)}

        for pos, participant in enumerate(top, start=1):
            row = self.podios_table.rowCount()
            self.podios_table.insertRow(row)

            pos_item = QTableWidgetItem(str(pos))
            pos_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if pos in medal_colors:
                pos_item.setBackground(medal_colors[pos])
            self.podios_table.setItem(row, 0, pos_item)

            self.podios_table.setItem(row, 1, QTableWidgetItem(participant.chip_id))
            self.podios_table.setItem(row, 2, QTableWidgetItem(participant.category_id))
            self.podios_table.setItem(row, 3, QTableWidgetItem(_fmt_time(participant.total_time)))

            finish_str = participant.finish_time.strftime('%H:%M:%S') if participant.finish_time else "N/A"
            self.podios_table.setItem(row, 4, QTableWidgetItem(finish_str))

            status_item = QTableWidgetItem("Finished")
            status_item.setBackground(Qt.GlobalColor.green)
            self.podios_table.setItem(row, 5, status_item)

    # -------------------------------------------------------------------------
    # Refresh: Tiempos Parciales
    # -------------------------------------------------------------------------

    def refresh_tiempos_parciales(self):
        if not self.race_tracker or not self.event_manager:
            return

        filter_cat = self.parciales_dist_combo.currentData()

        # Recopilar todas las lecturas checkpoint
        chip_readings = getattr(self.race_tracker, 'chip_readings', {})
        rows_data = []

        for chip_id, readings in chip_readings.items():
            checkpoints = [r for r in readings if r.reading_type == 'checkpoint']
            if not checkpoints:
                continue
            if filter_cat and readings[0].category_id != filter_cat:
                continue
            for r in checkpoints:
                rows_data.append({
                    'chip': chip_id,
                    'distancia': r.category_id,
                    'checkpoint': f"CP{r.antenna_id}",
                    'hora': r.timestamp.strftime('%H:%M:%S'),
                    'tiempo': _fmt_time(r.race_time),
                })

        self.parciales_table.setRowCount(0)

        if not rows_data:
            self.parciales_table.hide()
            self.parciales_placeholder.show()
            return

        # Calcular columnas dinámicas (una por cada CP detectado)
        checkpoints_found = sorted(set(r['checkpoint'] for r in rows_data))
        cols = ["Chip", "Distancia"] + checkpoints_found + ["Hora Llegada", "Tiempo Total"]
        self.parciales_table.setColumnCount(len(cols))
        self.parciales_table.setHorizontalHeaderLabels(cols)

        # Agrupar por chip
        by_chip = {}
        for rd in rows_data:
            chip = rd['chip']
            if chip not in by_chip:
                by_chip[chip] = {'distancia': rd['distancia'], 'checkpoints': {}}
            by_chip[chip]['checkpoints'][rd['checkpoint']] = rd['tiempo']

        self.parciales_placeholder.hide()
        self.parciales_table.show()

        for chip_id, data in by_chip.items():
            # Get participant status for finish info
            p_status = None
            if hasattr(self.race_tracker, 'participant_statuses'):
                p_status = self.race_tracker.participant_statuses.get(chip_id)

            row = self.parciales_table.rowCount()
            self.parciales_table.insertRow(row)
            self.parciales_table.setItem(row, 0, QTableWidgetItem(chip_id))
            self.parciales_table.setItem(row, 1, QTableWidgetItem(data['distancia']))

            for i, cp in enumerate(checkpoints_found):
                val = data['checkpoints'].get(cp, "-")
                self.parciales_table.setItem(row, 2 + i, QTableWidgetItem(val))

            offset = 2 + len(checkpoints_found)
            if p_status and p_status.finish_time:
                self.parciales_table.setItem(row, offset, QTableWidgetItem(
                    p_status.finish_time.strftime('%H:%M:%S')))
            else:
                self.parciales_table.setItem(row, offset, QTableWidgetItem("-"))

            if p_status and p_status.total_time is not None:
                self.parciales_table.setItem(row, offset + 1, QTableWidgetItem(
                    _fmt_time(p_status.total_time)))
            else:
                self.parciales_table.setItem(row, offset + 1, QTableWidgetItem("-"))

        header = self.parciales_table.horizontalHeader()
        for i in range(len(cols)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    # -------------------------------------------------------------------------
    # Exportación
    # -------------------------------------------------------------------------

    def _get_all_results(self):
        """Devuelve lista de filas [chip, distancia, tiempo_fmt, finish_hora, posicion]"""
        if not self.race_tracker or not self.event_manager:
            return []
        rows = []
        for cat_id in self.event_manager.get_categories_by_time():
            results = self.race_tracker.get_category_results(cat_id)
            finished = [p for p in results if p.status == 'finished' and p.total_time is not None]
            finished.sort(key=lambda x: x.total_time)
            for pos, p in enumerate(finished, start=1):
                rows.append({
                    'pos': pos,
                    'chip': p.chip_id,
                    'distancia': p.category_id,
                    'tiempo': _fmt_time(p.total_time),
                    'tiempo_seg': round(p.total_time, 3) if p.total_time else '',
                    'finish': p.finish_time.strftime('%H:%M:%S') if p.finish_time else '',
                    'checkpoints': p.checkpoints_passed,
                })
        return rows

    def export_all_results(self):
        """Exportar todos los resultados a CSV"""
        rows = self._get_all_results()
        if not rows:
            QMessageBox.information(self, "Sin datos", "No hay resultados finalizados para exportar.")
            return
        self._save_csv(
            ["Pos", "Chip", "Distancia", "Tiempo", "Tiempo (seg)", "Hora Llegada", "Checkpoints"],
            [[r['pos'], r['chip'], r['distancia'], r['tiempo'], r['tiempo_seg'], r['finish'], r['checkpoints']] for r in rows],
            "resultados_completos"
        )

    def export_podios_csv(self):
        """Exportar el podio actual a CSV"""
        cat_id = self.podios_dist_combo.currentData()
        if not cat_id or not self.race_tracker:
            QMessageBox.information(self, "Sin selección", "Selecciona primero una distancia.")
            return
        top_n = self.podios_top_spin.value()
        results = self.race_tracker.get_category_results(cat_id)
        finished = sorted([p for p in results if p.status == 'finished' and p.total_time is not None],
                          key=lambda x: x.total_time)[:top_n]
        if not finished:
            QMessageBox.information(self, "Sin datos", f"No hay finalizados en '{cat_id}'.")
            return
        self._save_csv(
            ["Pos", "Chip", "Distancia", "Tiempo", "Hora Llegada"],
            [[i+1, p.chip_id, p.category_id, _fmt_time(p.total_time),
              p.finish_time.strftime('%H:%M:%S') if p.finish_time else '']
             for i, p in enumerate(finished)],
            f"podio_{cat_id}"
        )

    def export_parciales_csv(self):
        """Exportar tiempos parciales a CSV"""
        if self.parciales_table.rowCount() == 0:
            QMessageBox.information(self, "Sin datos", "No hay tiempos parciales para exportar.")
            return
        cols = [self.parciales_table.horizontalHeaderItem(c).text()
                for c in range(self.parciales_table.columnCount())]
        data = []
        for r in range(self.parciales_table.rowCount()):
            row = []
            for c in range(self.parciales_table.columnCount()):
                item = self.parciales_table.item(r, c)
                row.append(item.text() if item else "")
            data.append(row)
        self._save_csv(cols, data, "tiempos_parciales")

    def _save_csv(self, headers, rows, default_name):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar CSV", f"{default_name}.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            QMessageBox.information(self, "Exportado", f"Archivo guardado en:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{e}")

    def _pdf_not_available(self, kind):
        QMessageBox.information(
            self, "PDF no disponible",
            f"La exportación PDF ({kind}) requiere la librería 'reportlab'.\n"
            "Por favor instálala con: pip install reportlab"
        )

    # -------------------------------------------------------------------------
    # Log de eventos
    # -------------------------------------------------------------------------

    def log_event(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.events_log.append(f"[{timestamp}] {message}")
        text = self.events_log.toPlainText()
        lines = text.split('\n')
        if len(lines) > 50:
            self.events_log.setPlainText('\n'.join(lines[-50:]))
