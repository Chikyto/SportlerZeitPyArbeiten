#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Widget de Asignación de Chips RFID
src/gui/widgets/chip_assignment_widget.py

Permite asignar chips físicos RFID a atletas pre-registrados
importados desde el sistema web.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox, QMessageBox, QSplitter, QTextEdit
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QTimer
from PyQt6.QtGui import QColor, QFont
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class ChipAssignmentWidget(QWidget):
    """
    Widget para asignar chips RFID a atletas pre-registrados

    Features:
    - Lista de atletas importados
    - Búsqueda y filtrado
    - Modo de escaneo para leer chips
    - Asignación manual o por escaneo
    - Visualización de asignaciones pendientes/completadas
    """

    # Señales
    chip_assigned = pyqtSignal(str, str)  # athlete_id, chip_id
    chip_scanned = pyqtSignal(str)  # chip_id
    assignment_completed = pyqtSignal()

    def __init__(self, race_manager=None, scanner=None, signals=None):
        super().__init__()
        self.race_manager = race_manager
        self.scanner = scanner
        self.signals = signals
        self.scan_mode = False
        self.selected_athlete = None
        self.assignments = {}  # {athlete_id: chip_id}

        self.setup_ui()
        self.refresh_athletes_table()

        # Conectar señal global de tags detectados
        if self.signals:
            self.signals.tag_detected.connect(self.on_chip_scanned)

    def setup_ui(self):
        """Configurar interfaz"""
        layout = QVBoxLayout(self)

        # Título
        title = QLabel("🏷️ Asignación de Chips RFID")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Instrucciones
        instructions = QLabel(
            "Importa atletas desde el sistema web, luego asigna chips RFID físicos a cada corredor"
        )
        instructions.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instructions)

        # Controles superiores
        controls_layout = QHBoxLayout()

        # Búsqueda
        search_group = QGroupBox("Búsqueda")
        search_layout = QHBoxLayout(search_group)

        search_layout.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nombre, dorsal o chip...")
        self.search_input.textChanged.connect(self.filter_athletes)
        search_layout.addWidget(self.search_input)

        controls_layout.addWidget(search_group)

        # Filtro por categoría
        filter_group = QGroupBox("Filtros")
        filter_layout = QHBoxLayout(filter_group)

        filter_layout.addWidget(QLabel("Categoría:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("Todas")
        self.category_filter.currentTextChanged.connect(self.filter_athletes)
        filter_layout.addWidget(self.category_filter)

        filter_layout.addWidget(QLabel("Estado:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Todos", "Pendientes", "Asignados"])
        self.status_filter.currentTextChanged.connect(self.filter_athletes)
        filter_layout.addWidget(self.status_filter)

        controls_layout.addWidget(filter_group)

        layout.addLayout(controls_layout)

        # Splitter: Tabla de atletas + Panel de asignación
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Tabla de atletas
        athletes_group = QGroupBox("Atletas Pre-registrados")
        athletes_layout = QVBoxLayout(athletes_group)

        self.athletes_table = QTableWidget()
        self.athletes_table.setColumnCount(6)
        self.athletes_table.setHorizontalHeaderLabels([
            "Dorsal", "Nombre", "Categoría", "Chip RFID", "Estado", "Info"
        ])

        header = self.athletes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        self.athletes_table.setAlternatingRowColors(True)
        self.athletes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.athletes_table.itemSelectionChanged.connect(self.on_athlete_selected)

        athletes_layout.addWidget(self.athletes_table)

        # Contador
        self.count_label = QLabel("Total: 0 atletas")
        self.count_label.setStyleSheet("font-weight: bold; color: #333;")
        athletes_layout.addWidget(self.count_label)

        splitter.addWidget(athletes_group)

        # Panel de asignación
        assignment_group = QGroupBox("Asignación de Chip")
        assignment_layout = QVBoxLayout(assignment_group)

        # Info del atleta seleccionado
        self.athlete_info_label = QLabel("Selecciona un atleta de la lista")
        self.athlete_info_label.setStyleSheet(
            "background: #f0f0f0; padding: 15px; border-radius: 5px; font-size: 14px;"
        )
        self.athlete_info_label.setWordWrap(True)
        assignment_layout.addWidget(self.athlete_info_label)

        # Modo de asignación
        mode_label = QLabel("Modo de Asignación:")
        mode_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        assignment_layout.addWidget(mode_label)

        # Botón de escaneo
        self.scan_button = QPushButton("📡 Escanear Chip")
        self.scan_button.setEnabled(False)
        self.scan_button.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background: #2563eb; }
            QPushButton:disabled { background: #9ca3af; }
        """)
        self.scan_button.clicked.connect(self.toggle_scan_mode)
        assignment_layout.addWidget(self.scan_button)

        # Status de escaneo
        self.scan_status_label = QLabel("")
        self.scan_status_label.setStyleSheet("color: #666; font-style: italic;")
        self.scan_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        assignment_layout.addWidget(self.scan_status_label)

        # Separador
        separator = QLabel("─── O ───")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator.setStyleSheet("color: #999; margin: 10px 0;")
        assignment_layout.addWidget(separator)

        # Asignación manual
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Chip ID:"))
        self.manual_chip_input = QLineEdit()
        self.manual_chip_input.setPlaceholderText("Ej: 7662")
        self.manual_chip_input.setEnabled(False)
        manual_layout.addWidget(self.manual_chip_input)

        self.assign_button = QPushButton("Asignar")
        self.assign_button.setEnabled(False)
        self.assign_button.clicked.connect(self.assign_chip_manually)
        manual_layout.addWidget(self.assign_button)

        assignment_layout.addLayout(manual_layout)

        # Botón de limpiar asignación
        self.clear_button = QPushButton("🗑️ Limpiar Asignación")
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_assignment)
        assignment_layout.addWidget(self.clear_button)

        assignment_layout.addStretch()

        # Estadísticas
        stats_label = QLabel("Estadísticas:")
        stats_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        assignment_layout.addWidget(stats_label)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        assignment_layout.addWidget(self.stats_text)

        splitter.addWidget(assignment_group)

        splitter.setStretchFactor(0, 2)  # Tabla más grande
        splitter.setStretchFactor(1, 1)  # Panel más pequeño

        layout.addWidget(splitter)

        # Botones inferiores
        bottom_buttons = QHBoxLayout()

        self.import_button = QPushButton("📥 Importar desde Web")
        self.import_button.clicked.connect(self.import_from_web)
        bottom_buttons.addWidget(self.import_button)

        self.import_assignments_button = QPushButton("📤 Importar Asignaciones")
        self.import_assignments_button.setToolTip("Importar chips ya asignados desde CSV externo")
        self.import_assignments_button.clicked.connect(self.import_assignments_from_csv)
        bottom_buttons.addWidget(self.import_assignments_button)

        self.export_button = QPushButton("💾 Exportar Asignaciones")
        self.export_button.clicked.connect(self.save_assignments)
        bottom_buttons.addWidget(self.export_button)

        bottom_buttons.addStretch()

        layout.addLayout(bottom_buttons)

        # Actualizar estadísticas
        self.update_stats()

    def set_scanner(self, scanner):
        """Establecer referencia al scanner"""
        self.scanner = scanner
        logger.info("✅ Scanner asignado a ChipAssignmentWidget")

    def set_race_manager(self, race_manager):
        """Establecer referencia al race manager"""
        self.race_manager = race_manager
        self.refresh_category_filter()
        self.refresh_athletes_table()

    def refresh_category_filter(self):
        """Actualizar combo de categorías"""
        if not self.race_manager:
            return

        self.category_filter.clear()
        self.category_filter.addItem("Todas")

        for category in self.race_manager.get_all_categories():
            self.category_filter.addItem(category.name, category.category_id)

    def refresh_athletes_table(self):
        """Actualizar tabla de atletas"""
        if not self.race_manager:
            self.athletes_table.setRowCount(0)
            self.count_label.setText("Total: 0 atletas")
            return

        self.athletes_table.setRowCount(0)

        total_count = 0
        assigned_count = 0

        for category in self.race_manager.get_all_categories():
            for athlete in category.participants:
                row = self.athletes_table.rowCount()
                self.athletes_table.insertRow(row)

                # Dorsal
                self.athletes_table.setItem(row, 0, QTableWidgetItem(str(athlete.bib_number)))

                # Nombre
                name_item = QTableWidgetItem(athlete.name)
                name_item.setData(Qt.ItemDataRole.UserRole, athlete.athlete_id)  # Guardar ID
                self.athletes_table.setItem(row, 1, name_item)

                # Categoría
                self.athletes_table.setItem(row, 2, QTableWidgetItem(category.name))

                # Chip RFID
                chip_item = QTableWidgetItem(athlete.tag_id or "-")
                if athlete.tag_id:
                    chip_item.setBackground(QColor("#d1fae5"))  # Verde claro
                    assigned_count += 1
                else:
                    chip_item.setBackground(QColor("#fef3c7"))  # Amarillo claro
                self.athletes_table.setItem(row, 3, chip_item)

                # Estado
                status = "✅ Asignado" if athlete.tag_id else "⏳ Pendiente"
                status_item = QTableWidgetItem(status)
                self.athletes_table.setItem(row, 4, status_item)

                # Info adicional
                self.athletes_table.setItem(row, 5, QTableWidgetItem(athlete.notes or ""))

                total_count += 1

        pending_count = total_count - assigned_count

        self.count_label.setText(
            f"Total: {total_count} atletas | "
            f"✅ Asignados: {assigned_count} | "
            f"⏳ Pendientes: {pending_count}"
        )

        self.update_stats()

    def filter_athletes(self):
        """Filtrar atletas según búsqueda y filtros"""
        search_term = self.search_input.text().lower()
        category_filter = self.category_filter.currentData()
        status_filter = self.status_filter.currentText()

        for row in range(self.athletes_table.rowCount()):
            show_row = True

            # Filtrar por búsqueda
            if search_term:
                name = self.athletes_table.item(row, 1).text().lower()
                bib = self.athletes_table.item(row, 0).text().lower()
                chip = self.athletes_table.item(row, 3).text().lower()

                if search_term not in name and search_term not in bib and search_term not in chip:
                    show_row = False

            # Filtrar por categoría
            if category_filter and show_row:
                cat_name = self.athletes_table.item(row, 2).text()
                # Buscar categoría por nombre
                cat_match = None
                if self.race_manager:
                    for cat in self.race_manager.get_all_categories():
                        if cat.name == cat_name:
                            cat_match = cat.category_id
                            break

                if cat_match != category_filter:
                    show_row = False

            # Filtrar por estado
            if status_filter != "Todos" and show_row:
                status = self.athletes_table.item(row, 4).text()
                if status_filter == "Pendientes" and "Pendiente" not in status:
                    show_row = False
                elif status_filter == "Asignados" and "Asignado" not in status:
                    show_row = False

            self.athletes_table.setRowHidden(row, not show_row)

    def on_athlete_selected(self):
        """Manejar selección de atleta en la tabla"""
        selected_rows = self.athletes_table.selectedItems()
        if not selected_rows:
            self.selected_athlete = None
            self.athlete_info_label.setText("Selecciona un atleta de la lista")
            self.scan_button.setEnabled(False)
            self.manual_chip_input.setEnabled(False)
            self.assign_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            return

        # Obtener ID del atleta
        row = self.athletes_table.currentRow()
        athlete_id = self.athletes_table.item(row, 1).data(Qt.ItemDataRole.UserRole)

        # Buscar atleta en race_manager
        if not self.race_manager:
            return

        athlete = None
        for category in self.race_manager.get_all_categories():
            for a in category.participants:
                if a.athlete_id == athlete_id:
                    athlete = a
                    break
            if athlete:
                break

        if not athlete:
            return

        self.selected_athlete = athlete

        # Mostrar info
        info_text = f"""
<b>Atleta Seleccionado:</b><br>
<b>Nombre:</b> {athlete.name}<br>
<b>Dorsal:</b> #{athlete.bib_number}<br>
<b>Categoría:</b> {athlete.category_id}<br>
<b>Chip Actual:</b> {athlete.tag_id or 'Sin asignar'}<br>
<br>
{athlete.notes or ''}
        """.strip()

        self.athlete_info_label.setText(info_text)

        # Habilitar controles
        self.scan_button.setEnabled(True)
        self.manual_chip_input.setEnabled(True)
        self.assign_button.setEnabled(True)
        self.clear_button.setEnabled(bool(athlete.tag_id))

    def toggle_scan_mode(self):
        """Activar/desactivar modo de escaneo"""
        if not self.scanner:
            QMessageBox.warning(
                self,
                "Scanner No Disponible",
                "No hay scanner conectado. Usa asignación manual."
            )
            return

        self.scan_mode = not self.scan_mode

        if self.scan_mode:
            self.scan_button.setText("🛑 Detener Escaneo")
            self.scan_button.setStyleSheet("""
                QPushButton {
                    background: #ef4444;
                    color: white;
                    padding: 15px;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover { background: #dc2626; }
            """)
            self.scan_status_label.setText("🔴 ESCANEANDO... Acerca el chip al lector")
            self.scan_status_label.setStyleSheet("color: #ef4444; font-weight: bold;")

            # Iniciar escaneo (implementar según tu scanner)
            self.start_scanning()

        else:
            self.scan_button.setText("📡 Escanear Chip")
            self.scan_button.setStyleSheet("""
                QPushButton {
                    background: #3b82f6;
                    color: white;
                    padding: 15px;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover { background: #2563eb; }
            """)
            self.scan_status_label.setText("")

            # Detener escaneo
            self.stop_scanning()

    def start_scanning(self):
        """Iniciar modo de escaneo"""
        # TODO: Implementar según tu scanner
        # Por ahora, simular con timer
        logger.info("🔍 Modo de escaneo activado")

    def stop_scanning(self):
        """Detener modo de escaneo"""
        logger.info("⏸️ Modo de escaneo desactivado")

    @pyqtSlot(dict)
    def on_chip_scanned(self, tag_info: dict):
        """
        Callback cuando se escanea un chip

        Args:
            tag_info: Dict con información del tag (tag_id, antenna_port, timestamp, etc.)
        """
        # Extraer chip_id del dict
        chip_id = tag_info.get('tag_id') or tag_info.get('epc', '')

        if not chip_id:
            logger.warning("⚠️  Tag detectado pero sin ID válido")
            return

        # Solo procesar si estamos en modo escaneo y hay atleta seleccionado
        if not self.scan_mode or not self.selected_athlete:
            logger.debug(f"📡 Chip detectado: {chip_id} (ignorado - no en modo asignación)")
            return

        logger.info(f"📡 Chip escaneado para asignación: {chip_id}")

        # Detener escaneo
        self.toggle_scan_mode()

        # Asignar chip
        self.assign_chip(chip_id)

    def assign_chip_manually(self):
        """Asignar chip manualmente desde el input"""
        if not self.selected_athlete:
            return

        chip_id = self.manual_chip_input.text().strip()
        if not chip_id:
            QMessageBox.warning(self, "Error", "Ingresa un Chip ID")
            return

        self.assign_chip(chip_id)

    def assign_chip(self, chip_id: str):
        """Asignar chip a atleta seleccionado"""
        if not self.selected_athlete:
            return

        # Verificar si el chip ya está asignado
        for category in self.race_manager.get_all_categories():
            for athlete in category.participants:
                if athlete.tag_id == chip_id and athlete.athlete_id != self.selected_athlete.athlete_id:
                    QMessageBox.warning(
                        self,
                        "Chip Ya Asignado",
                        f"El chip {chip_id} ya está asignado a:\n{athlete.name} (#{athlete.bib_number})"
                    )
                    return

        # Asignar
        old_chip = self.selected_athlete.tag_id
        self.selected_athlete.tag_id = chip_id

        logger.info(f"✅ Chip {chip_id} asignado a {self.selected_athlete.name}")

        # Emitir señal
        self.chip_assigned.emit(self.selected_athlete.athlete_id, chip_id)

        # Actualizar tabla
        self.refresh_athletes_table()

        # Limpiar input
        self.manual_chip_input.clear()

        # Mostrar confirmación
        QMessageBox.information(
            self,
            "Asignación Exitosa",
            f"Chip {chip_id} asignado a:\n{self.selected_athlete.name} (#{self.selected_athlete.bib_number})"
        )

    def clear_assignment(self):
        """Limpiar asignación de chip del atleta seleccionado"""
        if not self.selected_athlete or not self.selected_athlete.tag_id:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar",
            f"¿Limpiar asignación de chip {self.selected_athlete.tag_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.selected_athlete.tag_id = ""
            self.refresh_athletes_table()
            logger.info(f"🗑️ Asignación limpiada para {self.selected_athlete.name}")

    def import_from_web(self):
        """Importar atletas desde CSV o API web"""
        from PyQt6.QtWidgets import QFileDialog

        # Diálogo para elegir método
        reply = QMessageBox.question(
            self,
            "Método de Importación",
            "¿Cómo deseas importar los atletas?\n\n"
            "• CSV: Archivo exportado desde Firebase\n"
            "• API: Conectar directamente a Cloud Run",
            QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Open
        )

        if reply == QMessageBox.StandardButton.Cancel:
            return

        if reply == QMessageBox.StandardButton.Open:
            # Importar desde CSV
            self.import_from_csv()
        elif reply == QMessageBox.StandardButton.Apply:
            # Importar desde API
            self.import_from_api()

    def import_from_csv(self):
        """Importar desde archivo CSV"""
        from PyQt6.QtWidgets import QFileDialog
        from src.core.csv_importer import CSVAthleteImporter

        # Seleccionar archivo
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo CSV de inscriptos",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Crear importador
            importer = CSVAthleteImporter()

            # Importar con diferentes encodings si falla
            athletes_by_cat = None
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

            for encoding in encodings_to_try:
                try:
                    logger.info(f"Intentando importar con encoding: {encoding}")
                    athletes_by_cat = importer.import_from_csv(
                        csv_path=file_path,
                        encoding=encoding,
                        filter_approved=True
                    )
                    logger.info(f"✅ Importación exitosa con encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    logger.warning(f"⚠️  Encoding {encoding} falló, probando siguiente...")
                    continue

            if athletes_by_cat is None:
                raise ValueError("No se pudo leer el archivo con ningún encoding soportado")

            # Verificar si se importó algo
            if not athletes_by_cat:
                raise ValueError(
                    "No se importaron atletas. Verifica:\n"
                    "1. Que el CSV tenga datos\n"
                    "2. Que la columna 'Estado Pago' contenga 'Aprobado' o 'Approved'\n"
                    "3. Que las columnas 'Nombre', 'Apellido' y 'Distancia' tengan datos"
                )

            # Crear categorías
            categories = importer.create_categories()

            if not categories:
                raise ValueError("No se pudieron crear categorías. Verifica la columna 'Distancia' en el CSV.")

            # Agregar a race_manager
            for category in categories:
                # Verificar si ya existe
                existing = self.race_manager.get_category(category.category_id)
                if existing:
                    # Agregar participantes a categoría existente
                    for athlete in category.participants:
                        try:
                            existing.add_participant(athlete)
                        except ValueError as e:
                            logger.warning(f"No se pudo agregar {athlete.name}: {e}")
                else:
                    # Agregar categoría nueva
                    self.race_manager.add_category(category)

            # Actualizar tabla
            self.refresh_athletes_table()
            self.refresh_category_filter()

            # Mostrar resumen (calcular total correctamente)
            total = sum(len(cat.participants) for cat in categories)

            QMessageBox.information(
                self,
                "Importación Exitosa",
                f"✅ Importados desde CSV:\n\n"
                f"• {len(categories)} categorías\n"
                f"• {total} atletas\n"
                f"• Dorsales asignados automáticamente\n\n"
                f"Ahora puedes asignar chips RFID a cada corredor."
            )

            logger.info(f"✅ Importación CSV completa: {total} atletas en {len(categories)} categorías")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error importando CSV:\n{str(e)}\n\n"
                f"Verifica que el archivo tenga el formato correcto."
            )
            logger.error(f"❌ Error importando CSV: {e}")
            import traceback
            traceback.print_exc()

    def import_from_api(self):
        """Importar desde Cloud Run API"""
        QMessageBox.information(
            self,
            "API Cloud Run",
            "Importación desde Cloud Run próximamente.\n\n"
            "Por ahora, usa importación desde CSV exportado de Firebase."
        )

    def import_assignments_from_csv(self):
        """Importar asignaciones de chips desde CSV externo"""
        from PyQt6.QtWidgets import QFileDialog
        import csv

        # Seleccionar archivo
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar CSV con Asignaciones",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        try:
            updated = 0
            not_found = 0
            errors = []

            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                # Verificar que tenga las columnas necesarias
                required_cols = ['Dorsal', 'Chip RFID']
                if not all(col in reader.fieldnames for col in required_cols):
                    raise ValueError(
                        f"El CSV debe tener las columnas: {', '.join(required_cols)}\n"
                        f"Columnas encontradas: {', '.join(reader.fieldnames)}"
                    )

                for row in reader:
                    dorsal = row.get('Dorsal', '').strip()
                    chip_id = row.get('Chip RFID', '').strip()

                    if not dorsal or not chip_id:
                        continue

                    try:
                        dorsal_num = int(dorsal)
                    except ValueError:
                        errors.append(f"Dorsal inválido: {dorsal}")
                        continue

                    # Buscar atleta por dorsal
                    found = False
                    for category in self.race_manager.get_all_categories():
                        for athlete in category.participants:
                            if athlete.bib_number == dorsal_num:
                                # Verificar que el chip no esté usado
                                chip_in_use = False
                                for cat in self.race_manager.get_all_categories():
                                    for ath in cat.participants:
                                        if ath.tag_id == chip_id and ath.athlete_id != athlete.athlete_id:
                                            chip_in_use = True
                                            break
                                    if chip_in_use:
                                        break

                                if chip_in_use:
                                    errors.append(f"Chip {chip_id} ya asignado a otro atleta")
                                else:
                                    # Asignar chip
                                    athlete.tag_id = chip_id
                                    updated += 1
                                    logger.info(f"✓ Chip {chip_id} asignado a {athlete.name} (#{dorsal_num})")

                                found = True
                                break
                        if found:
                            break

                    if not found:
                        not_found += 1
                        errors.append(f"Atleta con dorsal {dorsal_num} no encontrado")

            # Actualizar tabla
            self.refresh_athletes_table()
            self.update_stats()

            # Mostrar resultado
            msg = f"✅ Importación completada:\n\n"
            msg += f"• Chips asignados: {updated}\n"
            if not_found > 0:
                msg += f"• No encontrados: {not_found}\n"
            if errors:
                msg += f"\n⚠️ Advertencias:\n"
                msg += '\n'.join(errors[:5])  # Mostrar solo las primeras 5
                if len(errors) > 5:
                    msg += f"\n... y {len(errors) - 5} más"

            if updated > 0:
                QMessageBox.information(self, "Importación Completada", msg)
            else:
                QMessageBox.warning(self, "Sin Cambios", msg)

            logger.info(f"✅ Importación de asignaciones: {updated} actualizados, {not_found} no encontrados")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error importando asignaciones:\n{str(e)}"
            )
            logger.error(f"❌ Error importando asignaciones: {e}")
            import traceback
            traceback.print_exc()

    def save_assignments(self):
        """Exportar asignaciones de chips a CSV"""
        from PyQt6.QtWidgets import QFileDialog
        import csv
        from datetime import datetime

        # Seleccionar archivo de salida
        default_name = f"asignaciones_chips_{datetime.now().strftime('%Y-%m-%d_%H%M')}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Asignaciones de Chips",
            default_name,
            "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Header
                writer.writerow([
                    'Dorsal', 'Nombre', 'Categoría', 'Chip RFID', 'Estado',
                    'DNI', 'Email', 'Teléfono', 'Notas'
                ])

                # Datos de todos los atletas
                for category in self.race_manager.get_all_categories():
                    for athlete in category.participants:
                        # Extraer info adicional de las notas
                        dni = email = telefono = ''
                        if athlete.notes:
                            for part in athlete.notes.split('|'):
                                part = part.strip()
                                if part.startswith('DNI:'):
                                    dni = part.replace('DNI:', '').strip()
                                elif part.startswith('Email:'):
                                    email = part.replace('Email:', '').strip()
                                elif part.startswith('Tel:'):
                                    telefono = part.replace('Tel:', '').strip()

                        estado = '✅ Asignado' if athlete.has_chip_assigned() else '⏳ Pendiente'

                        writer.writerow([
                            athlete.bib_number,
                            athlete.name,
                            category.name,
                            athlete.tag_id or '',
                            estado,
                            dni,
                            email,
                            telefono,
                            athlete.notes or ''
                        ])

            # Contar asignaciones
            total = 0
            assigned = 0
            for category in self.race_manager.get_all_categories():
                for athlete in category.participants:
                    total += 1
                    if athlete.has_chip_assigned():
                        assigned += 1

            QMessageBox.information(
                self,
                "Exportación Exitosa",
                f"✅ Asignaciones exportadas:\n\n"
                f"• Total atletas: {total}\n"
                f"• Con chip asignado: {assigned}\n"
                f"• Pendientes: {total - assigned}\n\n"
                f"Archivo guardado en:\n{file_path}"
            )

            logger.info(f"✅ Asignaciones exportadas a: {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error exportando asignaciones:\n{str(e)}"
            )
            logger.error(f"❌ Error exportando asignaciones: {e}")

    def update_stats(self):
        """Actualizar panel de estadísticas"""
        if not self.race_manager:
            return

        total = 0
        assigned = 0
        by_category = {}

        for category in self.race_manager.get_all_categories():
            cat_total = len(category.participants)
            cat_assigned = len([a for a in category.participants if a.tag_id])

            total += cat_total
            assigned += cat_assigned

            by_category[category.name] = {
                'total': cat_total,
                'assigned': cat_assigned,
                'pending': cat_total - cat_assigned
            }

        pending = total - assigned
        progress = (assigned / total * 100) if total > 0 else 0

        stats_text = f"""
<b>Progreso General:</b> {assigned}/{total} ({progress:.1f}%)<br>
<br>
<b>Por Categoría:</b><br>
"""

        for cat_name, stats in by_category.items():
            cat_progress = (stats['assigned'] / stats['total'] * 100) if stats['total'] > 0 else 0
            stats_text += f"• {cat_name}: {stats['assigned']}/{stats['total']} ({cat_progress:.0f}%)<br>"

        self.stats_text.setHtml(stats_text)
