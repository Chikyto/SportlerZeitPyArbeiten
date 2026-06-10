from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QGroupBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QComboBox, QTabWidget, QTextEdit)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RaceMonitoringWidget(QWidget):
    """Widget para monitoreo de carreras en tiempo real"""

    # Señales
    refresh_requested = pyqtSignal()

    def __init__(self, race_manager=None):
        super().__init__()
        self.race_manager = race_manager
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
        controls_layout.addWidget(QLabel("Distancia:"))
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

        # Botón de exportación
        self.export_btn = QPushButton("📊 Exportar Resultados")
        self.export_btn.clicked.connect(self.show_export_dialog)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                padding: 8px 15px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        controls_layout.addWidget(self.export_btn)

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

        # Tab 4: Podios por categoría de premiación
        self.setup_podiums_tab()

        # Tab 5: Tiempos parciales (Splits)
        self.setup_splits_tab()

        layout.addWidget(self.monitoring_tabs)
        
    def setup_categories_overview_tab(self):
        """Tab con resumen de todas las categorías"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "Resumen de Distancias")
        
        layout = QVBoxLayout(tab)
        
        # Tabla de categorías con estado
        self.categories_overview_table = QTableWidget()
        self.categories_overview_table.setColumnCount(8)
        self.categories_overview_table.setHorizontalHeaderLabels([
            "Distancia", "Estado", "Hora Inicio", "Participantes",
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
            "Chip", "Distancia", "Estado", "Tiempo Inicio",
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

    def setup_podiums_tab(self):
        """Tab con podios por categoría de premiación"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "🏆 Podios por Distancia")

        layout = QVBoxLayout(tab)

        # Controles
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Distancia:"))
        self.podiums_category_combo = QComboBox()
        self.podiums_category_combo.addItem("Selecciona una distancia")
        self.podiums_category_combo.currentTextChanged.connect(self.refresh_podiums)
        controls_layout.addWidget(self.podiums_category_combo)

        controls_layout.addWidget(QLabel("Top:"))
        self.podium_top_n_combo = QComboBox()
        self.podium_top_n_combo.addItems(["3", "5", "10"])
        self.podium_top_n_combo.currentTextChanged.connect(self.refresh_podiums)
        controls_layout.addWidget(self.podium_top_n_combo)

        refresh_podiums_btn = QPushButton("🔄 Actualizar Podios")
        refresh_podiums_btn.clicked.connect(self.refresh_podiums)
        controls_layout.addWidget(refresh_podiums_btn)

        export_podiums_btn = QPushButton("📄 CSV")
        export_podiums_btn.clicked.connect(self.export_podiums_to_csv)
        export_podiums_btn.setStyleSheet("background-color: #10b981; color: white; font-weight: bold;")
        export_podiums_btn.setToolTip("Exportar podios a CSV")
        controls_layout.addWidget(export_podiums_btn)

        # Botones de exportación a PDF
        export_pdf_general_btn = QPushButton("📕 PDF General")
        export_pdf_general_btn.clicked.connect(self.export_pdf_general)
        export_pdf_general_btn.setStyleSheet("background-color: #e94560; color: white; font-weight: bold;")
        export_pdf_general_btn.setToolTip("Exportar clasificación general a PDF")
        controls_layout.addWidget(export_pdf_general_btn)

        export_pdf_gender_btn = QPushButton("📗 PDF Género")
        export_pdf_gender_btn.clicked.connect(self.export_pdf_by_gender)
        export_pdf_gender_btn.setStyleSheet("background-color: #0f3460; color: white; font-weight: bold;")
        export_pdf_gender_btn.setToolTip("Exportar clasificación por género a PDF")
        controls_layout.addWidget(export_pdf_gender_btn)

        export_pdf_category_btn = QPushButton("📘 PDF Categorías")
        export_pdf_category_btn.clicked.connect(self.export_pdf_by_category)
        export_pdf_category_btn.setStyleSheet("background-color: #16213e; color: white; font-weight: bold;")
        export_pdf_category_btn.setToolTip("Exportar clasificación por categorías a PDF")
        controls_layout.addWidget(export_pdf_category_btn)

        export_pdf_announcer_btn = QPushButton("🎤 PDF Relator")
        export_pdf_announcer_btn.clicked.connect(self.export_pdf_announcer)
        export_pdf_announcer_btn.setStyleSheet("background-color: #f0a500; color: white; font-weight: bold;")
        export_pdf_announcer_btn.setToolTip("Exportar formato para relator (letra grande)")
        controls_layout.addWidget(export_pdf_announcer_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Área de podios (scroll area con contenido dinámico)
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.podiums_container = QWidget()
        self.podiums_layout = QVBoxLayout(self.podiums_container)
        self.podiums_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.podiums_container)
        layout.addWidget(scroll_area)

        # Información inicial
        info_label = QLabel("Selecciona una distancia para ver los podios clasificados por categoría de premiación (género/edad).")
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.podiums_layout.addWidget(info_label)

    def setup_splits_tab(self):
        """Tab con tiempos parciales (splits) detallados"""
        tab = QWidget()
        self.monitoring_tabs.addTab(tab, "⏱️ Tiempos Parciales")

        layout = QVBoxLayout(tab)

        # Controles
        controls_layout = QHBoxLayout()

        controls_layout.addWidget(QLabel("Distancia:"))
        self.splits_category_combo = QComboBox()
        self.splits_category_combo.addItem("Selecciona una distancia")
        self.splits_category_combo.currentTextChanged.connect(self.refresh_splits)
        controls_layout.addWidget(self.splits_category_combo)

        refresh_splits_btn = QPushButton("🔄 Actualizar")
        refresh_splits_btn.clicked.connect(self.refresh_splits)
        controls_layout.addWidget(refresh_splits_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Tabla de splits
        self.splits_table = QTableWidget()
        self.splits_table.setAlternatingRowColors(True)
        self.splits_table.setSortingEnabled(True)

        # Configurar tabla
        header = self.splits_table.horizontalHeader()
        header.setStretchLastSection(True)

        layout.addWidget(self.splits_table)

        # Información inicial
        info_label = QLabel(
            "Selecciona una distancia para ver los tiempos parciales (splits) de cada checkpoint.\n\n"
            "Los splits muestran el tiempo transcurrido en cada segmento de la carrera."
        )
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

    def refresh_splits(self):
        """Actualizar visualización de splits"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info("🔄 Actualizando splits...")

        if not self.race_manager:
            logger.warning("  ⚠️  No hay race_manager")
            return

        # Obtener distancia seleccionada
        selected_text = self.splits_category_combo.currentText()

        if selected_text == "Selecciona una distancia":
            return

        # Extraer distance_id
        distance_id = selected_text.split(" - ")[0]

        # Obtener distancia
        distance = self.race_manager.get_distance(distance_id)
        if not distance:
            logger.warning(f"  ⚠️  Distancia {distance_id} no encontrada")
            return

        # Verificar si hay checkpoints
        if distance.expected_checkpoints == 0:
            self.splits_table.setRowCount(1)
            self.splits_table.setColumnCount(1)
            self.splits_table.setHorizontalHeaderLabels(["⚠️ Información"])

            info_item = QTableWidgetItem(
                "Esta distancia no tiene checkpoints configurados.\n\n"
                "Para ver splits, ve a 'Gestión de Eventos' y configura\n"
                "el número de checkpoints para esta distancia."
            )
            info_item.setForeground(QColor(200, 100, 0))  # Naranja
            from PyQt6.QtGui import QFont
            info_item.setFont(QFont("Arial", 10))
            self.splits_table.setItem(0, 0, info_item)

            # Ajustar altura de fila para mostrar mensaje completo
            self.splits_table.setRowHeight(0, 100)

            logger.info(f"  ⚠️  Distancia '{distance.name}' no tiene checkpoints configurados")
            return

        # Obtener resultados
        results = self.race_manager.get_results(distance_id)

        if not results:
            self.splits_table.setRowCount(0)
            return

        # Configurar columnas dinámicamente según número de checkpoints
        num_checkpoints = distance.expected_checkpoints
        columns = ["Pos", "Dorsal", "Nombre"]

        # Agregar columnas de splits
        for i in range(1, num_checkpoints + 1):
            columns.append(f"Split CP{i}")

        columns.append("Tiempo Final")

        self.splits_table.setColumnCount(len(columns))
        self.splits_table.setHorizontalHeaderLabels(columns)

        # Llenar tabla
        self.splits_table.setRowCount(len(results))

        for row_idx, result in enumerate(results):
            athlete = result.athlete

            # Posición
            pos_item = QTableWidgetItem(str(result.position or "-"))
            pos_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.splits_table.setItem(row_idx, 0, pos_item)

            # Dorsal
            bib_item = QTableWidgetItem(str(athlete.bib_number or "-"))
            bib_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.splits_table.setItem(row_idx, 1, bib_item)

            # Nombre
            self.splits_table.setItem(row_idx, 2, QTableWidgetItem(athlete.name))

            # Splits
            col = 3
            for i in range(1, num_checkpoints + 1):
                if i in result.splits:
                    split = result.splits[i]
                    hours = int(split.total_seconds() // 3600)
                    minutes = int((split.total_seconds() % 3600) // 60)
                    seconds = int(split.total_seconds() % 60)
                    split_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

                    split_item = QTableWidgetItem(split_text)
                    split_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Colorear según velocidad (opcional)
                    # Verde para splits rápidos, amarillo normal, rojo lentos
                    split_item.setForeground(QColor(0, 100, 0))  # Verde por defecto

                    self.splits_table.setItem(row_idx, col, split_item)
                else:
                    not_passed_item = QTableWidgetItem("-")
                    not_passed_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    not_passed_item.setForeground(QColor(150, 150, 150))  # Gris
                    self.splits_table.setItem(row_idx, col, not_passed_item)

                col += 1

            # Tiempo final
            final_time_item = QTableWidgetItem(
                result.get_formatted_time() if result.finish_time else "-"
            )
            final_time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if result.finish_time:
                final_time_item.setForeground(QColor(0, 0, 200))  # Azul
                final_time_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))

            self.splits_table.setItem(row_idx, col, final_time_item)

        # Ajustar tamaño de columnas
        header = self.splits_table.horizontalHeader()
        for i in range(len(columns)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        logger.info(f"✅ Splits actualizados: {len(results)} atletas, {num_checkpoints} checkpoints")

    def refresh_podiums(self):
        """Actualizar visualización de podios"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info("🔄 Actualizando podios...")

        if not self.race_manager:
            logger.warning("  ⚠️  No hay race_manager")
            return

        # Limpiar layout actual
        while self.podiums_layout.count():
            item = self.podiums_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Obtener categoría seleccionada
        selected_text = self.podiums_category_combo.currentText()
        logger.info(f"  Distancia seleccionada: {selected_text}")

        if selected_text == "Selecciona una distancia":
            info_label = QLabel("Selecciona una distancia para ver los podios clasificados por categoría de premiación.")
            info_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.podiums_layout.addWidget(info_label)
            return

        race_category_id = selected_text.split(" - ")[0]

        # Obtener top_n
        top_n = int(self.podium_top_n_combo.currentText())
        logger.info(f"  Top N: {top_n}")

        # Obtener podios
        try:
            logger.info(f"  Obteniendo podios para {race_category_id}...")

            # ========== 1. GENERALES POR GÉNERO (SIN CATEGORÍA DE EDAD) ==========
            results_by_gender = self.race_manager.get_results_by_gender(race_category_id, only_finished=True)

            gender_label_map = {"M": "General Masculino", "F": "General Femenino", "X": "General No Binario", "O": "General Otro"}
            present_genders = [g for g in ["M", "F", "X", "O"] if results_by_gender.get(g)]
            for gender_key in present_genders:
                gender_results = results_by_gender.get(gender_key, [])
                if not gender_results:
                    continue

                gender_name = gender_label_map.get(gender_key, f"General {gender_key}")

                # Crear grupo para general
                group = QGroupBox(f"🏆 {gender_name}")
                group.setStyleSheet("""
                    QGroupBox {
                        font-weight: bold;
                        border: 3px solid #3b82f6;
                        border-radius: 5px;
                        margin-top: 10px;
                        padding-top: 10px;
                        background-color: #eff6ff;
                    }
                    QGroupBox::title {
                        color: #1e40af;
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px;
                        font-size: 14px;
                    }
                """)

                group_layout = QVBoxLayout(group)

                # Crear tabla
                podium_table = QTableWidget()
                podium_table.setColumnCount(5)
                podium_table.setHorizontalHeaderLabels([
                    "Pos", "Dorsal", "Nombre", "Tiempo", "Edad"
                ])

                display_results = gender_results[:top_n]
                podium_table.setRowCount(len(display_results))

                for idx, result in enumerate(display_results):
                    position = idx + 1

                    # Posición con medalla
                    pos_item = QTableWidgetItem()
                    if position == 1:
                        pos_item.setText("🥇 1°")
                        pos_item.setBackground(QColor("#ffd700"))
                    elif position == 2:
                        pos_item.setText("🥈 2°")
                        pos_item.setBackground(QColor("#c0c0c0"))
                    elif position == 3:
                        pos_item.setText("🥉 3°")
                        pos_item.setBackground(QColor("#cd7f32"))
                    else:
                        pos_item.setText(f"{position}°")

                    pos_item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                    podium_table.setItem(idx, 0, pos_item)

                    # Dorsal
                    podium_table.setItem(idx, 1, QTableWidgetItem(str(result.athlete.bib_number)))

                    # Nombre
                    name_item = QTableWidgetItem(result.athlete.name)
                    name_item.setFont(QFont("Arial", 10, QFont.Weight.Bold if position <= 3 else QFont.Weight.Normal))
                    podium_table.setItem(idx, 2, name_item)

                    # Tiempo
                    time_item = QTableWidgetItem(result.get_formatted_time())
                    time_item.setFont(QFont("Arial", 10, QFont.Weight.Bold if position <= 3 else QFont.Weight.Normal))
                    podium_table.setItem(idx, 3, time_item)

                    # Edad
                    age = result.athlete.get_age()
                    age_str = f"{age} años" if age is not None else "N/D"
                    podium_table.setItem(idx, 4, QTableWidgetItem(age_str))

                # Configurar tabla
                header = podium_table.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

                podium_table.setMaximumHeight(100 + (len(display_results) * 30))
                podium_table.setAlternatingRowColors(True)

                group_layout.addWidget(podium_table)
                self.podiums_layout.addWidget(group)

            # ========== 2. CATEGORÍAS DE EDAD (IAAF, etc) ==========
            podiums = self.race_manager.get_podium_by_award_category(race_category_id, top_n=top_n)
            logger.info(f"  Podios obtenidos: {len(podiums)} categorías")

            if not podiums and not results_by_gender.get("M") and not results_by_gender.get("F"):
                no_data_label = QLabel("No hay resultados finalizados aún.")
                no_data_label.setStyleSheet("color: #f59e0b; font-style: italic; padding: 20px;")
                no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.podiums_layout.addWidget(no_data_label)
                return

            # Crear grupos de podios por categoría
            for award_cat_id, podium in podiums.items():
                award_cat = self.race_manager.get_award_category(award_cat_id)
                if not award_cat or len(podium) == 0:
                    continue

                # Crear grupo para esta categoría
                group = QGroupBox(f"🏆 {award_cat.name}")
                group.setStyleSheet("""
                    QGroupBox {
                        font-weight: bold;
                        border: 2px solid #10b981;
                        border-radius: 5px;
                        margin-top: 10px;
                        padding-top: 10px;
                    }
                    QGroupBox::title {
                        color: #10b981;
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 5px;
                    }
                """)

                group_layout = QVBoxLayout(group)

                # Crear tabla de podio para esta categoría
                podium_table = QTableWidget()
                podium_table.setColumnCount(5)
                podium_table.setHorizontalHeaderLabels([
                    "Pos", "Dorsal", "Nombre", "Tiempo", "Género/Edad"
                ])

                podium_table.setRowCount(len(podium))

                for idx, (position, result) in enumerate(podium):
                    # Posición con medalla
                    pos_item = QTableWidgetItem()
                    if position == 1:
                        pos_item.setText("🥇 1°")
                        pos_item.setBackground(QColor("#ffd700"))  # Oro
                    elif position == 2:
                        pos_item.setText("🥈 2°")
                        pos_item.setBackground(QColor("#c0c0c0"))  # Plata
                    elif position == 3:
                        pos_item.setText("🥉 3°")
                        pos_item.setBackground(QColor("#cd7f32"))  # Bronce
                    else:
                        pos_item.setText(f"{position}°")

                    pos_item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                    podium_table.setItem(idx, 0, pos_item)

                    # Dorsal
                    podium_table.setItem(idx, 1, QTableWidgetItem(str(result.athlete.bib_number)))

                    # Nombre
                    name_item = QTableWidgetItem(result.athlete.name)
                    name_item.setFont(QFont("Arial", 10, QFont.Weight.Bold if position <= 3 else QFont.Weight.Normal))
                    podium_table.setItem(idx, 2, name_item)

                    # Tiempo
                    time_item = QTableWidgetItem(result.get_formatted_time())
                    time_item.setFont(QFont("Arial", 10, QFont.Weight.Bold if position <= 3 else QFont.Weight.Normal))
                    podium_table.setItem(idx, 3, time_item)

                    # Género/Edad
                    gender_map = {"M": "Masculino", "F": "Femenino", "O": "Otro"}
                    gender_str = gender_map.get(result.athlete.gender, "N/D")
                    age = result.athlete.get_age()
                    age_str = f"{age} años" if age is not None else "N/D"
                    podium_table.setItem(idx, 4, QTableWidgetItem(f"{gender_str}, {age_str}"))

                # Configurar tabla
                header = podium_table.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

                podium_table.setMaximumHeight(100 + (len(podium) * 30))
                podium_table.setAlternatingRowColors(True)

                group_layout.addWidget(podium_table)
                self.podiums_layout.addWidget(group)

        except Exception as e:
            error_label = QLabel(f"Error generando podios: {str(e)}")
            error_label.setStyleSheet("color: #ef4444; font-style: italic; padding: 20px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.podiums_layout.addWidget(error_label)
            import logging
            logging.error(f"Error en refresh_podiums: {e}", exc_info=True)

    def refresh_podiums_category_combo(self):
        """Actualizar combo de categorías para podios"""
        if not self.race_manager:
            return

        current_text = self.podiums_category_combo.currentText()
        self.podiums_category_combo.clear()
        self.podiums_category_combo.addItem("Selecciona una distancia")

        for category in self.race_manager.get_all_categories():
            # Solo mostrar categorías finalizadas o en curso
            from src.core.race_tracking.models import RaceStatus
            if category.status in [RaceStatus.RUNNING, RaceStatus.FINISHED]:
                self.podiums_category_combo.addItem(f"{category.distance_id} - {category.name}")

        # Restaurar selección si es posible
        index = self.podiums_category_combo.findText(current_text)
        if index >= 0:
            self.podiums_category_combo.setCurrentIndex(index)

    def refresh_splits_category_combo(self):
        """Actualizar combo de categorías para splits"""
        if not self.race_manager:
            return

        current_text = self.splits_category_combo.currentText()
        self.splits_category_combo.clear()
        self.splits_category_combo.addItem("Selecciona una distancia")

        count_added = 0
        for category in self.race_manager.get_all_categories():
            # Mostrar todas las categorías RUNNING o FINISHED
            from src.core.race_tracking.models import RaceStatus
            if category.status in [RaceStatus.RUNNING, RaceStatus.FINISHED]:
                # Agregar indicador si tiene checkpoints o no
                if category.expected_checkpoints > 0:
                    self.splits_category_combo.addItem(
                        f"{category.distance_id} - {category.name} ({category.expected_checkpoints} CPs)"
                    )
                else:
                    self.splits_category_combo.addItem(
                        f"{category.distance_id} - {category.name} (sin CPs)"
                    )
                count_added += 1

        # Restaurar selección si es posible
        index = self.splits_category_combo.findText(current_text)
        if index >= 0:
            self.splits_category_combo.setCurrentIndex(index)

    def export_podiums_to_csv(self):
        """Exportar podios por categoría de premiación a CSV"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import csv

        if not self.race_manager:
            QMessageBox.warning(self, "Error", "No hay race_manager disponible")
            return

        # Verificar que hay una categoría seleccionada
        selected_text = self.podiums_category_combo.currentText()
        if selected_text == "Selecciona una distancia":
            QMessageBox.warning(self, "Error", "Selecciona una distancia primero")
            return

        race_category_id = selected_text.split(" - ")[0]
        race_category = self.race_manager.get_category(race_category_id)

        # Diálogo para seleccionar archivo
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Podios a CSV",
            f"podios_{race_category_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )

        if not file_path:
            return  # Usuario canceló

        try:
            # Obtener podios
            top_n = int(self.podium_top_n_combo.currentText())
            podiums = self.race_manager.get_podium_by_award_category(race_category_id, top_n=top_n)

            if not podiums:
                QMessageBox.warning(self, "Sin datos", "No hay resultados finalizados para exportar")
                return

            # Escribir CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Encabezado principal
                writer.writerow([f"PODIOS POR CATEGORÍA DE PREMIACIÓN - {race_category.name}"])
                writer.writerow([f"Fecha de exportación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([])  # Línea vacía

                # Para cada categoría de premiación
                for award_cat_id, podium in sorted(podiums.items()):
                    award_cat = self.race_manager.get_award_category(award_cat_id)
                    if not award_cat or len(podium) == 0:
                        continue

                    # Encabezado de categoría
                    writer.writerow([f"CATEGORÍA: {award_cat.name}"])
                    writer.writerow([
                        "Posición",
                        "Dorsal",
                        "Nombre",
                        "Tiempo",
                        "Género",
                        "Edad",
                        "Equipo"
                    ])

                    # Resultados de esta categoría
                    for position, result in podium:
                        gender_map = {"M": "Masculino", "F": "Femenino", "O": "Otro"}
                        gender_str = gender_map.get(result.athlete.gender, "N/D")
                        age = result.athlete.get_age()
                        age_str = str(age) if age is not None else "N/D"

                        writer.writerow([
                            position,
                            result.athlete.bib_number,
                            result.athlete.name,
                            result.get_formatted_time(),
                            gender_str,
                            age_str,
                            result.athlete.team or ""
                        ])

                    writer.writerow([])  # Línea vacía entre categorías

                # Clasificación General por Género
                writer.writerow([])
                writer.writerow(["=" * 80])
                writer.writerow(["CLASIFICACIÓN GENERAL POR GÉNERO"])
                writer.writerow(["=" * 80])
                writer.writerow([])

                results_by_gender = self.race_manager.get_results_by_gender(race_category_id, only_finished=True)

                for gender_key, gender_name in [("M", "GENERAL MASCULINO"), ("F", "GENERAL FEMENINO")]:
                    gender_results = results_by_gender.get(gender_key, [])
                    if not gender_results:
                        continue

                    writer.writerow([gender_name])
                    writer.writerow([
                        "Pos",
                        "Dorsal",
                        "Nombre",
                        "Tiempo",
                        "Categoría",
                        "Edad",
                        "Equipo"
                    ])

                    for position, result in enumerate(gender_results[:top_n], 1):
                        age = result.athlete.get_age()
                        age_str = str(age) if age is not None else "N/D"

                        writer.writerow([
                            position,
                            result.athlete.bib_number,
                            result.athlete.name,
                            result.get_formatted_time(),
                            result.athlete.get_category() or "N/D",
                            age_str,
                            result.athlete.team or ""
                        ])

                    writer.writerow([])  # Línea vacía

                # Estadísticas generales al final
                writer.writerow([])
                writer.writerow(["ESTADÍSTICAS GENERALES"])
                writer.writerow(["Total de categorías de premiación:", len(podiums)])
                total_podium_positions = sum(len(p) for p in podiums.values())
                writer.writerow(["Total de posiciones en podios:", total_podium_positions])
                writer.writerow(["Finalizadores masculinos:", len(results_by_gender.get('M', []))])
                writer.writerow(["Finalizadores femeninos:", len(results_by_gender.get('F', []))])

            QMessageBox.information(
                self,
                "Éxito",
                f"Podios exportados exitosamente a:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error exportando podios:\n{str(e)}"
            )
            import logging
            logging.error(f"Error en export_podiums_to_csv: {e}", exc_info=True)

    def export_pdf_general(self):
        """Exportar clasificación general a PDF"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.pdf_exporter import PDFExporter
        import logging
        logger = logging.getLogger(__name__)

        logger.info("📕 Exportación a PDF General iniciada")

        if not self.race_manager:
            QMessageBox.warning(self, "Sin Race Manager", "No hay race manager configurado")
            return

        # Obtener distancia seleccionada del combo de podios
        selected_text = self.podiums_category_combo.currentText()
        logger.info(f"  Distancia seleccionada: {selected_text}")

        if selected_text == "Selecciona una distancia" or not selected_text:
            QMessageBox.warning(self, "Sin selección", "Selecciona una distancia primero en el tab de Podios")
            return

        # Extraer distance_id del formato "distance_id - nombre"
        race_category_id = selected_text.split(" - ")[0]
        logger.info(f"  Distance ID extraído: {race_category_id}")

        distance = self.race_manager.get_distance(race_category_id)
        if not distance:
            logger.error(f"  ❌ Distancia {race_category_id} no encontrada")
            return

        logger.info(f"  Distancia: {distance.name} ({len(distance.participants)} participantes)")

        try:
            # Diálogo para seleccionar archivo
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Clasificación General a PDF",
                f"clasificacion_general_{race_category_id}.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                logger.info("  Usuario canceló selección de archivo")
                return

            logger.info(f"  Archivo de salida: {file_path}")

            # Obtener resultados
            results = self.race_manager.get_results(race_category_id)
            logger.info(f"  Resultados obtenidos: {len(results)}")

            if not results:
                QMessageBox.warning(self, "Sin resultados", "No hay resultados para exportar")
                return

            # Obtener nombre del evento desde el tab de configuración
            event_name = "Carrera"
            try:
                # Buscar el tab de event_config en la ventana principal
                main_window = self.window()
                if hasattr(main_window, 'tab_manager'):
                    event_config_tab = main_window.tab_manager.get_tab('event_config')
                    if event_config_tab and hasattr(event_config_tab, 'event_name_input'):
                        event_name = event_config_tab.event_name_input.text() or "Carrera"
                        logger.info(f"  Nombre del evento: {event_name}")
            except Exception as e:
                logger.warning(f"  No se pudo obtener nombre del evento: {e}, usando 'Carrera'")

            # Crear exporter
            logger.info("  Creando PDFExporter...")
            exporter = PDFExporter(event_name=event_name)

            logger.info("  Generando PDF...")
            exporter.export_general_classification(
                distance_name=distance.name,
                results=results,
                output_path=file_path
            )

            logger.info(f"✅ PDF generado exitosamente: {file_path}")

            QMessageBox.information(
                self,
                "Éxito",
                f"PDF de clasificación general exportado:\n{file_path}"
            )

        except Exception as e:
            logger.error(f"❌ Error en export_pdf_general: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error exportando PDF:\n{str(e)}\n\nRevisa la consola para más detalles")

    def export_pdf_by_gender(self):
        """Exportar clasificación por género a PDF"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.pdf_exporter import PDFExporter
        import logging
        logger = logging.getLogger(__name__)

        logger.info("📗 Exportación a PDF por Género iniciada")

        if not self.race_manager:
            QMessageBox.warning(self, "Sin Race Manager", "No hay race manager configurado")
            return

        # Obtener distancia del combo de podios
        selected_text = self.podiums_category_combo.currentText()
        if selected_text == "Selecciona una distancia" or not selected_text:
            QMessageBox.warning(self, "Sin selección", "Selecciona una distancia primero en el tab de Podios")
            return

        race_category_id = selected_text.split(" - ")[0]
        logger.info(f"  Distance ID: {race_category_id}")

        distance = self.race_manager.get_distance(race_category_id)
        if not distance:
            logger.error(f"  ❌ Distancia {race_category_id} no encontrada")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Clasificación por Género a PDF",
                f"clasificacion_genero_{race_category_id}.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                logger.info("  Usuario canceló selección de archivo")
                return

            # Obtener clasificación por género
            results_by_gender = self.race_manager.get_results_by_gender(race_category_id)
            logger.info(f"  Masculino: {len(results_by_gender.get('M', []))}")
            logger.info(f"  Femenino: {len(results_by_gender.get('F', []))}")

            # Obtener nombre del evento
            event_name = "Carrera"
            try:
                main_window = self.window()
                if hasattr(main_window, 'tab_manager'):
                    event_config_tab = main_window.tab_manager.get_tab('event_config')
                    if event_config_tab and hasattr(event_config_tab, 'event_name_input'):
                        event_name = event_config_tab.event_name_input.text() or "Carrera"
            except:
                pass

            exporter = PDFExporter(event_name=event_name)
            exporter.export_classification_by_gender(
                distance_name=distance.name,
                results_by_gender=results_by_gender,
                output_path=file_path
            )

            logger.info(f"✅ PDF por género generado: {file_path}")

            QMessageBox.information(
                self,
                "Éxito",
                f"PDF por género exportado:\n{file_path}"
            )

        except Exception as e:
            logger.error(f"❌ Error en export_pdf_by_gender: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error exportando PDF:\n{str(e)}\n\nRevisa la consola para más detalles")

    def export_pdf_by_category(self):
        """Exportar clasificación por categorías IAAF a PDF"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.pdf_exporter import PDFExporter

        if not self.race_manager:
            QMessageBox.warning(self, "Sin Race Manager", "No hay race manager configurado")
            return

        # Obtener distancia del combo de podios
        selected_text = self.podiums_category_combo.currentText()
        if selected_text == "Selecciona una distancia" or not selected_text:
            QMessageBox.warning(self, "Sin selección", "Selecciona una distancia primero en el tab de Podios")
            return

        race_category_id = selected_text.split(" - ")[0]
        logger.info(f"  Distance ID: {race_category_id}")

        distance = self.race_manager.get_distance(race_category_id)
        if not distance:
            logger.error(f"  ❌ Distancia {race_category_id} no encontrada")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Clasificación por Categorías a PDF",
                f"clasificacion_categorias_{race_category_id}.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            # Obtener clasificación por categorías
            results_by_category = self.race_manager.get_results_by_award_category(race_category_id)

            event_name = "Carrera"
            if hasattr(self.parent(), 'event_name_input'):
                event_name = self.parent().event_name_input.text() or "Carrera"

            exporter = PDFExporter(event_name=event_name)
            exporter.export_classification_by_category(
                distance_name=distance.name,
                results_by_category=results_by_category,
                output_path=file_path
            )

            QMessageBox.information(
                self,
                "Éxito",
                f"PDF por categorías exportado:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exportando PDF:\n{str(e)}")
            import logging
            logging.error(f"Error en export_pdf_by_category: {e}", exc_info=True)

    def export_pdf_announcer(self):
        """Exportar formato para relator a PDF"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils.pdf_exporter import PDFExporter

        if not self.race_manager:
            QMessageBox.warning(self, "Sin Race Manager", "No hay race manager configurado")
            return

        # Obtener distancia del combo de podios
        selected_text = self.podiums_category_combo.currentText()
        if selected_text == "Selecciona una distancia" or not selected_text:
            QMessageBox.warning(self, "Sin selección", "Selecciona una distancia primero en el tab de Podios")
            return

        race_category_id = selected_text.split(" - ")[0]
        logger.info(f"  Distance ID: {race_category_id}")

        distance = self.race_manager.get_distance(race_category_id)
        if not distance:
            logger.error(f"  ❌ Distancia {race_category_id} no encontrada")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Formato para Relator a PDF",
                f"relator_{race_category_id}.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            # Obtener resultados
            results = self.race_manager.get_results(race_category_id)

            event_name = "Carrera"
            if hasattr(self.parent(), 'event_name_input'):
                event_name = self.parent().event_name_input.text() or "Carrera"

            exporter = PDFExporter(event_name=event_name)
            exporter.export_announcer_format(
                distance_name=distance.name,
                results=results,
                output_path=file_path
            )

            QMessageBox.information(
                self,
                "Éxito",
                f"PDF para relator exportado:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error exportando PDF:\n{str(e)}")
            import logging
            logging.error(f"Error en export_pdf_announcer: {e}", exc_info=True)

    def set_race_manager(self, race_manager):
        """Establecer el race manager"""
        self.race_manager = race_manager
        if race_manager:
            self.refresh_category_combo()
            self.system_status_label.setText("Sistema: Conectado")
            self.system_status_label.setStyleSheet("font-weight: bold; color: green;")
        
    def refresh_category_combo(self):
        """Actualizar combo de categorías"""
        if not self.race_manager:
            return

        current_text = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("Todas las categorías")

        for category in self.race_manager.get_all_categories():
            self.category_combo.addItem(f"{category.distance_id} - {category.name}")

        # Restaurar selección si es posible
        index = self.category_combo.findText(current_text)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

        # También actualizar el combo de podios y splits
        self.refresh_podiums_category_combo()
        self.refresh_splits_category_combo()
        
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
            
    def refresh(self):
        """Actualizar widget completo (para compatibilidad con señales)"""
        self.refresh_category_combo()
        self.refresh_all_data()

    def refresh_all_data(self):
        """Actualizar todos los datos"""
        if not self.race_manager or not self.race_manager:
            return

        self.refresh_categories_overview()
        self.refresh_participants_table()
        self.refresh_statistics()
        
    def refresh_categories_overview(self):
        """Actualizar resumen de categorías"""
        if not self.race_manager:
            return

        self.categories_overview_table.setRowCount(0)

        for category in self.race_manager.get_all_categories():
            # Obtener resultados de esta categoría
            results = self.race_manager.get_results(category.distance_id)

            # Contar por estado
            from src.core.race_tracking.models import AthleteStatus
            not_started = len([r for r in results if r.status == AthleteStatus.NOT_STARTED])
            in_progress = len([r for r in results if r.status == AthleteStatus.RUNNING])
            finished = len([r for r in results if r.status == AthleteStatus.FINISHED])
            total_participants = len(results)

            # Última actividad
            last_checkpoint = "N/A"
            if results:
                # Encontrar el último timestamp de cualquier resultado
                timestamps = []
                for r in results:
                    if r.start_time:
                        timestamps.append(r.start_time)
                    if r.finish_time:
                        timestamps.append(r.finish_time)
                    for cp_time in r.checkpoint_times.values():
                        timestamps.append(cp_time)

                if timestamps:
                    last_checkpoint = max(timestamps).strftime('%H:%M:%S')

            # Agregar fila
            row = self.categories_overview_table.rowCount()
            self.categories_overview_table.insertRow(row)

            self.categories_overview_table.setItem(row, 0,
                                                  QTableWidgetItem(f"{category.distance_id} - {category.name}"))

            # Estado con color
            from src.core.race_tracking.models import RaceStatus
            status_item = QTableWidgetItem(category.status.value.title())
            if category.status == RaceStatus.RUNNING:
                status_item.setBackground(Qt.GlobalColor.green)
            elif category.status == RaceStatus.FINISHED:
                status_item.setBackground(Qt.GlobalColor.gray)
            self.categories_overview_table.setItem(row, 1, status_item)

            # Hora de inicio
            start_time_str = category.start_time.strftime('%H:%M:%S') if category.start_time else "No iniciada"
            self.categories_overview_table.setItem(row, 2, QTableWidgetItem(start_time_str))

            self.categories_overview_table.setItem(row, 3, QTableWidgetItem(str(total_participants)))
            self.categories_overview_table.setItem(row, 4, QTableWidgetItem(str(not_started)))
            self.categories_overview_table.setItem(row, 5, QTableWidgetItem(str(in_progress)))
            self.categories_overview_table.setItem(row, 6, QTableWidgetItem(str(finished)))
            self.categories_overview_table.setItem(row, 7, QTableWidgetItem(last_checkpoint))
            
    def refresh_participants_table(self):
        """Actualizar tabla de participantes"""
        if not self.race_manager:
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
            all_participants = self.race_manager.get_results(selected_category)
        else:
            # Todas las categorías
            for category in self.race_manager.get_all_categories():
                all_participants.extend(self.race_manager.get_results(category.distance_id))
        
        # Filtrar por estado
        if status_filter != "todos":
            from src.core.race_tracking.models import AthleteStatus
            status_map = {
                "no iniciados": AthleteStatus.NOT_STARTED,
                "en carrera": AthleteStatus.RUNNING,
                "finalizados": AthleteStatus.FINISHED
            }
            filter_status = status_map.get(status_filter)
            if filter_status:
                all_participants = [p for p in all_participants if p.status == filter_status]
        
        # Actualizar contador
        self.participants_count_label.setText(f"Total: {len(all_participants)} participantes")
        
        # Llenar tabla
        from src.core.race_tracking.models import AthleteStatus
        for result in all_participants:
            row = self.participants_table.rowCount()
            self.participants_table.insertRow(row)

            # Chip ID, Categoría
            self.participants_table.setItem(row, 0, QTableWidgetItem(result.athlete.tag_id))
            self.participants_table.setItem(row, 1, QTableWidgetItem(result.distance_id))

            # Estado con color
            status_item = QTableWidgetItem(result.status.value.replace('_', ' ').title())
            if result.status == AthleteStatus.RUNNING:
                status_item.setBackground(Qt.GlobalColor.yellow)
            elif result.status == AthleteStatus.FINISHED:
                status_item.setBackground(Qt.GlobalColor.green)
            self.participants_table.setItem(row, 2, status_item)

            # Tiempos
            start_time_str = result.start_time.strftime('%H:%M:%S') if result.start_time else "N/A"
            self.participants_table.setItem(row, 3, QTableWidgetItem(start_time_str))

            # Tiempo actual/total
            if result.status == AthleteStatus.FINISHED and result.total_time:
                time_str = result.get_formatted_time()
            elif result.status == AthleteStatus.RUNNING and result.start_time:
                current_time = (datetime.now() - result.start_time).total_seconds()
                minutes = int(current_time // 60)
                seconds = int(current_time % 60)
                time_str = f"{minutes:02d}:{seconds:02d} (en curso)"
            else:
                time_str = "N/A"
            self.participants_table.setItem(row, 4, QTableWidgetItem(time_str))

            # Checkpoints - Mostrar cuáles checkpoints específicos pasó
            if result.checkpoint_times:
                # Obtener lista de checkpoints en orden
                checkpoint_numbers = sorted(result.checkpoint_times.keys())
                checkpoints_text = ", ".join([f"✓ CP{num}" for num in checkpoint_numbers])
                checkpoints_item = QTableWidgetItem(checkpoints_text)
                checkpoints_item.setForeground(QColor(0, 100, 200))  # Azul
            else:
                checkpoints_item = QTableWidgetItem("-")
            self.participants_table.setItem(row, 5, checkpoints_item)

            # Última lectura (último timestamp conocido)
            last_time = None
            last_antenna = "N/A"
            if result.finish_time:
                last_time = result.finish_time
                last_antenna = "Finish"
            elif result.checkpoint_times:
                last_checkpoint = max(result.checkpoint_times.keys())
                last_time = result.checkpoint_times[last_checkpoint]
                last_antenna = f"CP{last_checkpoint}"
            elif result.start_time:
                last_time = result.start_time
                last_antenna = "Start"

            last_reading_str = last_time.strftime('%H:%M:%S') if last_time else "N/A"

            self.participants_table.setItem(row, 6, QTableWidgetItem(last_reading_str))
            self.participants_table.setItem(row, 7, QTableWidgetItem(last_antenna))
            
    def refresh_statistics(self):
        """Actualizar estadísticas"""
        if not self.race_manager:
            return

        # Calcular estadísticas
        active_categories = self.race_manager.get_active_categories()
        all_categories = self.race_manager.get_all_categories()

        total_participants = 0
        total_in_race = 0
        total_finished = 0
        total_detections = len(self.race_manager.detection_history)

        from src.core.race_tracking.models import AthleteStatus

        stats_text = f"""ESTADÍSTICAS DEL SISTEMA
{'='*30}
Distancias activas: {len(active_categories)}
Total de distancias: {len(all_categories)}
Total de detecciones: {total_detections}

PARTICIPANTES POR DISTANCIA:
"""

        for category in all_categories:
            results = self.race_manager.get_results(category.distance_id)
            num_participants = len(results)
            num_running = len([r for r in results if r.status == AthleteStatus.RUNNING])
            num_finished = len([r for r in results if r.status == AthleteStatus.FINISHED])

            total_participants += num_participants
            total_in_race += num_running
            total_finished += num_finished

            stats_text += f"• {category.name}:\n"
            stats_text += f"  - Inscritos: {num_participants}\n"
            stats_text += f"  - En carrera: {num_running}\n"
            stats_text += f"  - Finalizados: {num_finished}\n\n"

        stats_text += f"""TOTALES:
- Total inscritos: {total_participants}
- Total en carrera: {total_in_race}
- Total finalizados: {total_finished}

Última actualización: {datetime.now().strftime('%H:%M:%S')}"""

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

    def show_export_dialog(self):
        """Mostrar diálogo de exportación de resultados"""
        try:
            from .export_results_dialog import ExportResultsDialog

            dialog = ExportResultsDialog(self.race_manager, parent=self)
            dialog.exec()

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error abriendo diálogo de exportación: {e}")
            import traceback
            traceback.print_exc()

            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo abrir el diálogo de exportación:\n{str(e)}"
            )