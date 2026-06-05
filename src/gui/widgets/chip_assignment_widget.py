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
    QLineEdit, QComboBox, QMessageBox, QSplitter, QTextEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QTimer
from PyQt6.QtGui import QColor, QFont
import logging
from datetime import datetime
from typing import Optional, Dict, List

# Import helper modules
from .chip_assignment_csv_handler import ChipAssignmentCSVHandler
from .chip_assignment_scanner_manager import ChipAssignmentScannerManager
from .quick_athlete_registration_dialog import QuickAthleteRegistrationDialog

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
    categories_imported = pyqtSignal()  # Se emite después de importar categorías desde CSV

    def __init__(self, race_manager=None, scanner=None, signals=None):
        super().__init__()
        self.race_manager = race_manager
        self.scanner = scanner  # CRÍTICO: Inicializar para evitar AttributeError
        self.signals = signals
        self.scan_mode = False
        self.selected_athlete = None
        self.assignments = {}  # {athlete_id: chip_id}

        # Chip detection buffer for multi-chip selection
        self.detected_chips_buffer = []  # List of chip dicts
        self.chip_accumulation_timer = None

        # Initialize helper modules
        self.csv_handler = ChipAssignmentCSVHandler(self, race_manager)
        self.scanner_manager = ChipAssignmentScannerManager(self)
        self.scanner_manager.set_network_scanner(scanner)

        # Initialize persistence manager
        from src.core.race_data_persistence import RaceDataPersistence
        self.persistence = RaceDataPersistence()

        # Connect scanner manager signals
        self.scanner_manager.scanner_mode_changed.connect(self.on_scanner_mode_changed)
        self.scanner_manager.scanner_connected.connect(self.on_scanner_connected)
        self.scanner_manager.scanner_disconnected.connect(self.on_scanner_disconnected)

        self.setup_ui()

        # Auto-load saved data if available
        self.auto_load_saved_data()

        self.refresh_athletes_table()

        # Conectar señal global de tags detectados (YR8900)
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

        filter_layout.addWidget(QLabel("Distancia:"))
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
        self.athletes_table.setColumnCount(8)
        self.athletes_table.setHorizontalHeaderLabels([
            "Dorsal", "Nombre", "Distancia", "Género", "Fecha Nac.", "Chip RFID", "Estado", "Info"
        ])

        header = self.athletes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)

        self.athletes_table.setAlternatingRowColors(True)
        self.athletes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.athletes_table.itemSelectionChanged.connect(self.on_athlete_selected)

        # Asegurar que las barras de desplazamiento estén siempre disponibles
        self.athletes_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.athletes_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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

        # Selector de tipo de lector
        scanner_type_group = QGroupBox("Tipo de Lector")
        scanner_type_layout = QVBoxLayout(scanner_type_group)

        self.scanner_button_group = QButtonGroup()

        self.network_scanner_radio = QRadioButton("🌐 Antenas de Competencia (YR8900)")
        self.network_scanner_radio.setChecked(True)
        self.network_scanner_radio.toggled.connect(lambda: self.set_scanner_mode("network"))
        self.scanner_button_group.addButton(self.network_scanner_radio)
        scanner_type_layout.addWidget(self.network_scanner_radio)

        self.usb_scanner_radio = QRadioButton("🔌 Lector USB Kiosco (YR9011)")
        self.usb_scanner_radio.toggled.connect(lambda: self.set_scanner_mode("usb"))
        self.scanner_button_group.addButton(self.usb_scanner_radio)
        scanner_type_layout.addWidget(self.usb_scanner_radio)

        self.usb_status_label = QLabel("📴 Lector USB no conectado")
        self.usb_status_label.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px;")
        scanner_type_layout.addWidget(self.usb_status_label)

        assignment_layout.addWidget(scanner_type_group)

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

        self.clear_all_button = QPushButton("🗑️ Nuevo Evento")
        self.clear_all_button.setToolTip("Borra todos los atletas y chips. Usá esto antes de cargar un nuevo evento.")
        self.clear_all_button.setStyleSheet("color: #dc2626;")
        self.clear_all_button.clicked.connect(self.clear_all_data)
        bottom_buttons.addWidget(self.clear_all_button)

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

    # Propiedades para delegar al scanner_manager (compatibilidad hacia atrás)
    @property
    def usb_scanner(self):
        """Acceso al USB scanner a través del scanner_manager"""
        return self.scanner_manager.usb_scanner if hasattr(self, 'scanner_manager') else None

    @property
    def scanner_mode(self):
        """Acceso al modo de scanner a través del scanner_manager"""
        return self.scanner_manager.scanner_mode if hasattr(self, 'scanner_manager') else "network"

    def set_scanner_mode(self, mode: str):
        """
        Cambiar modo de scanner

        Args:
            mode: "network" para YR8900, "usb" para YR9011
        """
        # Update scanner_manager mode
        self.scanner_manager.scanner_mode = mode
        logger.info(f"🔄 Modo de scanner cambiado a: {mode}")

        if mode == "usb":
            # Connect USB scanner (handled by widget to connect signals properly)
            self.connect_usb_scanner()
        elif mode == "network":
            # Disconnect USB scanner
            self.scanner_manager.disconnect_usb_scanner()
            self.usb_status_label.setText("📴 Lector USB no conectado")
            self.usb_status_label.setStyleSheet("")

    def connect_usb_scanner(self):
        """Conectar lector USB YR9011 con diálogo de configuración"""
        try:
            from src.core.yr9011_usb_scanner import YR9011USBScanner
            from src.gui.usb_scanner_config_dialog import USBScannerConfigDialog

            logger.info("📡 Abriendo configuración de lector USB...")

            # Mostrar diálogo de configuración
            dialog = USBScannerConfigDialog(self)

            if dialog.exec() == dialog.DialogCode.Accepted:
                config = dialog.get_config()

                if not config['port']:
                    self.usb_status_label.setText("❌ No se seleccionó puerto")
                    self.network_scanner_radio.setChecked(True)
                    return

                logger.info(f"📡 Conectando a {config['port']} @ {config['baudrate']} bps...")
                self.usb_status_label.setText(f"⏳ Conectando a {config['port']}...")

                # Crear scanner USB con configuración
                usb_scanner = YR9011USBScanner(port=config['port'])

                # Conectar señales
                usb_scanner.tag_detected.connect(self.on_chip_scanned)
                usb_scanner.error_occurred.connect(self.on_usb_scanner_error)

                # Intentar conectar
                if usb_scanner.connect():
                    # CRÍTICO: Asegurar que NO esté en modo escaneo continuo al conectar
                    usb_scanner.stop_continuous_reading()

                    # Asignar al scanner_manager
                    self.scanner_manager.usb_scanner = usb_scanner

                    self.usb_status_label.setText(f"✅ Conectado a {config['port']}")
                    self.usb_status_label.setStyleSheet("color: #10b981; font-size: 11px; margin-left: 20px; font-weight: bold;")
                    logger.info(f"✅ Lector USB conectado en {config['port']}")
                    logger.info(f"💡 Lector USB listo. Escaneo iniciará al presionar 'Escanear Chip'")
                else:
                    self.usb_status_label.setText("❌ No se pudo conectar")
                    self.usb_status_label.setStyleSheet("color: #ef4444; font-size: 11px; margin-left: 20px;")
                    QMessageBox.warning(
                        self,
                        "Conexión Fallida",
                        f"No se pudo conectar al puerto {config['port']}.\n\n"
                        "Verifica que:\n"
                        "• El puerto sea el correcto\n"
                        "• No esté siendo usado por otra aplicación\n"
                        "• El lector esté encendido"
                    )
                    # Volver a modo network
                    self.network_scanner_radio.setChecked(True)
            else:
                # Usuario canceló
                logger.info("⏭️ Usuario canceló configuración USB")
                self.network_scanner_radio.setChecked(True)

        except ImportError as e:
            logger.error(f"❌ Error importando YR9011USBScanner: {e}")
            self.usb_status_label.setText("❌ Error: módulo no disponible")
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cargar el driver del lector USB:\n{str(e)}"
            )
            self.network_scanner_radio.setChecked(True)
        except Exception as e:
            logger.error(f"❌ Error conectando lector USB: {e}")
            self.usb_status_label.setText(f"❌ Error: {str(e)[:30]}...")
            QMessageBox.critical(
                self,
                "Error",
                f"Error conectando lector USB:\n{str(e)}"
            )
            self.network_scanner_radio.setChecked(True)

    def on_usb_scanner_error(self, error_msg: str):
        """Manejar errores del lector USB"""
        logger.error(f"❌ Error lector USB: {error_msg}")
        self.usb_status_label.setText(f"⚠️ {error_msg[:40]}...")
        self.usb_status_label.setStyleSheet("color: #f59e0b; font-size: 11px; margin-left: 20px;")

    def refresh_category_filter(self):
        """Actualizar combo de categorías"""
        if not self.race_manager:
            return

        self.category_filter.clear()
        self.category_filter.addItem("Todas")

        for category in self.race_manager.get_all_categories():
            self.category_filter.addItem(category.name, category.distance_id)

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

                # Distancia
                self.athletes_table.setItem(row, 2, QTableWidgetItem(category.name))

                # Género
                gender_map = {"M": "M", "F": "F", "Otro": "Otro", None: "-"}
                gender_display = gender_map.get(athlete.gender, athlete.gender or "-")
                self.athletes_table.setItem(row, 3, QTableWidgetItem(gender_display))

                # Fecha de Nacimiento
                if athlete.birth_date:
                    birth_date_str = athlete.birth_date.strftime('%d/%m/%Y')
                else:
                    birth_date_str = "-"
                self.athletes_table.setItem(row, 4, QTableWidgetItem(birth_date_str))

                # Chip RFID
                chip_item = QTableWidgetItem(athlete.tag_id or "-")
                if athlete.tag_id:
                    chip_item.setBackground(QColor("#d1fae5"))  # Verde claro
                    assigned_count += 1
                else:
                    chip_item.setBackground(QColor("#fef3c7"))  # Amarillo claro
                self.athletes_table.setItem(row, 5, chip_item)

                # Estado
                status = "✅ Asignado" if athlete.tag_id else "⏳ Pendiente"
                status_item = QTableWidgetItem(status)
                self.athletes_table.setItem(row, 6, status_item)

                # Info adicional
                self.athletes_table.setItem(row, 7, QTableWidgetItem(athlete.notes or ""))

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
                chip = self.athletes_table.item(row, 5).text().lower()  # Actualizado: chip ahora en columna 5

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
                            cat_match = cat.distance_id
                            break

                if cat_match != category_filter:
                    show_row = False

            # Filtrar por estado
            if status_filter != "Todos" and show_row:
                status = self.athletes_table.item(row, 6).text()  # Actualizado: estado ahora en columna 6
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
<b>Distancia:</b> {athlete.distance_id}<br>
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
        try:
            # Verificar que haya atleta seleccionado PRIMERO
            if not self.selected_athlete:
                QMessageBox.warning(
                    self,
                    "Selecciona un Atleta",
                    "⚠️ Primero selecciona un atleta de la tabla.\n\n"
                    "Luego haz click en 'Escanear Chip' para activar el modo de asignación."
                )
                return

            # Verificar que haya scanner disponible según el modo
            if self.scanner_mode == "network":
                if not self.scanner:
                    QMessageBox.warning(
                        self,
                        "Scanner No Disponible",
                        "❌ No hay scanner de red conectado.\n\n"
                        "Opciones:\n"
                        "• Cambia a modo USB\n"
                        "• Usa asignación manual\n"
                        "• Verifica la conexión de las antenas"
                    )
                    return
            elif self.scanner_mode == "usb":
                if not hasattr(self, 'usb_scanner') or not self.usb_scanner or not self.usb_scanner.connected:
                    QMessageBox.warning(
                        self,
                        "Lector USB No Disponible",
                        "❌ El lector USB no está conectado.\n\n"
                        "Opciones:\n"
                        "• Cambia a modo de red\n"
                        "• Usa asignación manual\n"
                        "• Verifica la conexión del lector USB"
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
                athlete_name = self.selected_athlete.name if self.selected_athlete else "???"
                self.scan_status_label.setText(f"🔴 ESCANEANDO para {athlete_name}... Acerca el chip al lector")
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

        except AttributeError as e:
            logger.error(f"❌ Error de atributo en toggle_scan_mode: {e}")
            QMessageBox.critical(
                self,
                "Error de Configuración",
                f"❌ Error interno al activar el escaneo.\n\n"
                f"El sistema de escaneo no está correctamente configurado.\n\n"
                f"Detalles técnicos: {str(e)}\n\n"
                f"Intenta:\n"
                f"• Reiniciar la aplicación\n"
                f"• Verificar las conexiones\n"
                f"• Usar asignación manual"
            )
        except Exception as e:
            logger.error(f"❌ Error inesperado en toggle_scan_mode: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error Inesperado",
                f"❌ Ocurrió un error al activar el escaneo.\n\n"
                f"Error: {str(e)}\n\n"
                f"Por favor, verifica los logs para más detalles."
            )

    def start_scanning(self):
        """Iniciar modo de escaneo"""
        athlete_name = self.selected_athlete.name if self.selected_athlete else "???"
        scanner_type = "YR9011 USB" if self.scanner_mode == "usb" else "YR8900 Network"
        logger.info(f"🔍 Modo de escaneo activado para: {athlete_name}")
        logger.info(f"   • Dorsal: #{self.selected_athlete.bib_number if self.selected_athlete else '?'}")
        logger.info(f"   • Lector: {scanner_type}")
        logger.info(f"   • Esperando detección de chip...")

        # Si estamos en modo USB, iniciar lectura continua
        if self.scanner_mode == "usb" and self.usb_scanner:
            logger.info("🟢 Iniciando escaneo continuo USB...")
            self.usb_scanner.start_continuous_reading()

    def stop_scanning(self):
        """Detener modo de escaneo"""
        logger.info("⏸️ Modo de escaneo desactivado")

        # Si estamos en modo USB, detener lectura continua
        if self.scanner_mode == "usb" and self.usb_scanner:
            logger.info("🔴 Deteniendo escaneo continuo USB...")
            self.usb_scanner.stop_continuous_reading()

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

        # LOGGING DETALLADO para debugging
        logger.info(f"📡 Tag detectado: {chip_id}")
        logger.info(f"   • Modo escaneo activo: {self.scan_mode}")
        logger.info(f"   • Atleta seleccionado: {self.selected_athlete.name if self.selected_athlete else 'Ninguno'}")

        # Solo procesar si estamos en modo escaneo y hay atleta seleccionado
        if not self.scan_mode:
            logger.warning(f"⚠️  Chip {chip_id} ignorado: Modo escaneo NO activo. Haz click en '📡 Escanear Chip' primero.")
            # Mostrar notificación visual AMARILLA (útil para ver qué chips hay sin asignar)
            self.scan_status_label.setText(f"⚠️ Chip detectado ({chip_id}) pero modo escaneo NO activo")
            self.scan_status_label.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 13px;")

            # Auto-limpiar después de 5 segundos
            QTimer.singleShot(5000, lambda: self.scan_status_label.setText(""))
            return

        if not self.selected_athlete:
            logger.warning(f"⚠️  Chip {chip_id} detectado sin atleta seleccionado")
            # Ofrecer opción de registro rápido para casos excepcionales
            self.handle_unassigned_chip(chip_id)
            return

        logger.info(f"✅ Chip {chip_id} detectado en modo escaneo")

        # Acumular chip en buffer (para manejar múltiples chips cercanos)
        # Evitar duplicados en el buffer
        if not any(c['tag_id'] == chip_id for c in self.detected_chips_buffer):
            self.detected_chips_buffer.append(tag_info)
            logger.info(f"📋 Chip agregado al buffer ({len(self.detected_chips_buffer)} chips acumulados)")

        # Cancelar timer previo si existe
        if self.chip_accumulation_timer:
            self.chip_accumulation_timer.stop()
            self.chip_accumulation_timer = None

        # Iniciar timer de 1.5 segundos para procesar chips acumulados
        self.chip_accumulation_timer = QTimer()
        self.chip_accumulation_timer.setSingleShot(True)
        self.chip_accumulation_timer.timeout.connect(self.process_accumulated_chips)
        self.chip_accumulation_timer.start(1500)  # 1.5 segundos para acumular

        # Mostrar status temporal
        if len(self.detected_chips_buffer) == 1:
            self.scan_status_label.setText(f"📡 Chip detectado: {chip_id}")
        else:
            self.scan_status_label.setText(f"📡 {len(self.detected_chips_buffer)} chips detectados...")
        self.scan_status_label.setStyleSheet("color: #3b82f6; font-weight: bold;")

    def process_accumulated_chips(self):
        """
        Procesar chips acumulados después del período de acumulación

        Si hay un solo chip, asigna directamente.
        Si hay múltiples, muestra diálogo de selección.
        """
        if not self.detected_chips_buffer:
            logger.warning("⚠️  Buffer de chips vacío")
            return

        # Guardar referencia al atleta antes de cualquier cambio
        athlete_to_assign = self.selected_athlete

        if not athlete_to_assign:
            logger.error("❌ No hay atleta seleccionado")
            self.detected_chips_buffer.clear()
            return

        num_chips = len(self.detected_chips_buffer)
        logger.info(f"📊 Procesando {num_chips} chip(s) acumulado(s)")

        if num_chips == 1:
            # Un solo chip - asignar directamente
            chip_id = self.detected_chips_buffer[0]['tag_id']
            logger.info(f"✓ Un solo chip detectado: {chip_id}")

            # Detener escaneo
            self.toggle_scan_mode()

            # Asignar
            self._assign_chip_to_athlete(athlete_to_assign, chip_id)

        else:
            # Múltiples chips - mostrar diálogo de selección
            logger.info(f"🔀 Múltiples chips detectados ({num_chips}), mostrando selector...")

            from src.gui.multiple_chip_dialog import MultipleChipDialog

            # Detener escaneo primero
            self.toggle_scan_mode()

            # Mostrar diálogo
            dialog = MultipleChipDialog(self.detected_chips_buffer, self)
            result = dialog.exec()

            if result == dialog.DialogCode.Accepted:
                selected_chip = dialog.get_selected_chip()

                if selected_chip:
                    logger.info(f"✓ Usuario seleccionó chip: {selected_chip}")
                    self._assign_chip_to_athlete(athlete_to_assign, selected_chip)
                else:
                    logger.warning("⚠️  No se seleccionó ningún chip")
                    QMessageBox.warning(
                        self,
                        "Sin Selección",
                        "No se seleccionó ningún chip.\n\nVuelve a escanear si quieres asignar."
                    )
            else:
                logger.info("ℹ️  Usuario canceló selección de chip")

        # Limpiar buffer
        self.detected_chips_buffer.clear()

    def assign_chip_manually(self):
        """Asignar chip manualmente desde el input"""
        if not self.selected_athlete:
            return

        chip_id = self.manual_chip_input.text().strip()
        if not chip_id:
            QMessageBox.warning(self, "Error", "Ingresa un Chip ID")
            return

        # Asignar usando referencia local
        self._assign_chip_to_athlete(self.selected_athlete, chip_id)

    def _assign_chip_to_athlete(self, athlete, chip_id: str):
        """
        Asignar chip a un atleta específico (método interno)

        Args:
            athlete: Objeto Athlete al que asignar el chip
            chip_id: ID del chip RFID
        """
        if not athlete:
            logger.error("❌ Intento de asignar chip a atleta None")
            return

        # Verificar si el chip ya está asignado a otro atleta
        for category in self.race_manager.get_all_categories():
            for other_athlete in category.participants:
                if other_athlete.tag_id == chip_id and other_athlete.athlete_id != athlete.athlete_id:
                    QMessageBox.warning(
                        self,
                        "Chip Ya Asignado",
                        f"El chip {chip_id} ya está asignado a:\n{other_athlete.name} (#{other_athlete.bib_number})"
                    )
                    return

        # Asignar chip
        old_chip = athlete.tag_id
        athlete.tag_id = chip_id

        logger.info(f"✅ Chip {chip_id} asignado a {athlete.name} (#{athlete.bib_number})")

        # Emitir señal
        self.chip_assigned.emit(athlete.athlete_id, chip_id)

        # Actualizar tabla
        self.refresh_athletes_table()

        # Limpiar input
        self.manual_chip_input.clear()

        # Mostrar confirmación
        QMessageBox.information(
            self,
            "Asignación Exitosa",
            f"✅ Chip {chip_id} asignado a:\n{athlete.name} (#{athlete.bib_number})"
        )

        # AUTO-SAVE: Guardar datos automáticamente después de cada asignación
        self.auto_save_data()

    def handle_unassigned_chip(self, chip_id: str):
        """
        Manejar chip detectado sin corredor asignado (caso excepcional)

        Muestra un diálogo preguntando si desea registrar un nuevo corredor.

        Args:
            chip_id: ID del chip detectado
        """
        # Detener modo escaneo primero
        if self.scan_mode:
            self.toggle_scan_mode()

        # Mostrar diálogo de confirmación
        reply = QMessageBox.question(
            self,
            "Chip sin Corredor Asignado",
            f"Se detectó el chip {chip_id} pero no hay ningún corredor seleccionado.\n\n"
            "¿Es un corredor excepcional que no estaba en el sistema?\n"
            "(Por ejemplo: un atleta élite que se registra el día del evento)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            logger.info("ℹ️  Usuario rechazó registro de corredor excepcional")
            return

        # Abrir diálogo de registro rápido
        logger.info(f"🚀 Abriendo diálogo de registro rápido para chip {chip_id}")

        dialog = QuickAthleteRegistrationDialog(
            chip_id=chip_id,
            race_manager=self.race_manager,
            parent=self
        )

        if dialog.exec() != dialog.DialogCode.Accepted:
            logger.info("ℹ️  Usuario canceló registro de corredor excepcional")
            return

        # Obtener datos del atleta
        athlete_data = dialog.get_athlete_data()

        if not athlete_data:
            logger.error("❌ No se obtuvieron datos del atleta")
            return

        # Crear atleta
        try:
            from src.core.race_tracking.models import Athlete

            # Generar número de dorsal si es automático
            if athlete_data['bib_number'] is None:
                # Obtener el siguiente número de dorsal disponible para la categoría
                category_id = athlete_data['category_id']
                bib_number = self._generate_bib_number(category_id)
            else:
                bib_number = athlete_data['bib_number']

            # Crear objeto Athlete
            athlete_id = f"{athlete_data['category_id']}_{bib_number}"

            new_athlete = Athlete(
                athlete_id=athlete_id,
                tag_id=athlete_data['chip_id'],
                bib_number=bib_number,
                name=athlete_data['name'],
                category_id=athlete_data['category_id'],
                gender=athlete_data['gender'],
                birth_date=athlete_data['birth_date'],
                team='',
                notes='Registrado el día del evento (excepcional)'
            )

            # Agregar a la categoría correspondiente
            category = self.race_manager.get_category(athlete_data['category_id'])

            if not category:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"No se encontró la categoría {athlete_data['category_id']}"
                )
                return

            category.add_participant(new_athlete)

            logger.info(f"✅ Atleta excepcional registrado: {new_athlete.name} (#{bib_number})")

            # Refrescar tabla
            self.refresh_athletes_table()

            # AUTO-SAVE
            self.auto_save_data()

            # Mostrar confirmación
            QMessageBox.information(
                self,
                "Registro Exitoso",
                f"✅ Corredor registrado exitosamente:\n\n"
                f"• Nombre: {new_athlete.name}\n"
                f"• Dorsal: #{bib_number}\n"
                f"• Distancia: {athlete_data['category_id']}\n"
                f"• Chip: {athlete_data['chip_id']}"
            )

        except Exception as e:
            logger.error(f"❌ Error creando atleta excepcional: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Error al crear el corredor:\n{str(e)}"
            )

    def _generate_bib_number(self, category_id: str) -> int:
        """
        Generar número de dorsal automático para una categoría

        Args:
            category_id: ID de la categoría

        Returns:
            int: Número de dorsal único
        """
        # Rangos base por categoría (igual que en csv_importer.py)
        BIB_RANGES = {
            '5k': 1,      # 1-999
            '10k': 1000,  # 1000-1999
            '21k': 2000,  # 2000-2999
            '30k': 3000,  # 3000-3999
            '42k': 4000,  # 4000-4999
            '50k': 5000,  # 5000-5999
            '100k': 6000, # 6000-6999
        }

        base = BIB_RANGES.get(category_id, 1)

        # Obtener todos los dorsales existentes en esta categoría
        category = self.race_manager.get_category(category_id)
        if not category:
            return base

        existing_bibs = [a.bib_number for a in category.participants]

        if not existing_bibs:
            return base

        # Retornar el siguiente número disponible
        max_bib = max(existing_bibs)
        return max_bib + 1

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
        """Importar atletas desde Cloud Run API"""
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

            # Crear distancias (con diálogo de confirmación de checkpoints)
            distances = importer.create_distances(
                parent_widget=self,
                show_checkpoint_dialog=True
            )

            if not distances:
                raise ValueError("No se pudieron crear distancias. Verifica la columna 'Distancia' en el CSV o si cancelaste todas las configuraciones.")

            # Preguntar si limpiar datos existentes antes de agregar
            if self.race_manager.get_all_distances():
                reply = QMessageBox.question(
                    self,
                    "Datos existentes",
                    "Ya hay atletas cargados en el sistema.\n\n"
                    "¿Querés limpiar TODOS los datos antes de importar?\n\n"
                    "• Sí → borra todo y reimporta desde cero (recomendado)\n"
                    "• No → actualiza/agrega sin borrar",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Cancel:
                    return
                if reply == QMessageBox.StandardButton.Yes:
                    self.race_manager.clear_all()
                    self.persistence.clear_data()
                    logger.info("🗑️ Todos los datos limpiados antes de importar CSV")

            # Agregar a race_manager
            for distance in distances:
                # Verificar si ya existe
                existing = self.race_manager.get_distance(distance.distance_id)
                if existing:
                    # Agregar participantes a distancia existente
                    for athlete in distance.participants:
                        try:
                            existing.add_participant(athlete)
                        except ValueError as e:
                            logger.warning(f"No se pudo agregar {athlete.name}: {e}")
                else:
                    # Agregar distancia nueva
                    self.race_manager.add_distance(distance)

            # Actualizar tabla
            self.refresh_athletes_table()
            self.refresh_category_filter()

            # Emitir señal para que otros tabs se actualicen
            self.categories_imported.emit()
            logger.info("📢 Señal categories_imported emitida para sincronizar tabs")

            # Mostrar resumen (calcular total correctamente)
            total = sum(len(dist.participants) for dist in distances)

            QMessageBox.information(
                self,
                "Importación Exitosa",
                f"✅ Importados desde CSV:\n\n"
                f"• {len(distances)} distancias\n"
                f"• {total} atletas\n"
                f"• Dorsales asignados automáticamente\n\n"
                f"Ahora puedes asignar chips RFID a cada corredor."
            )

            logger.info(f"✅ Importación CSV completa: {total} atletas en {len(distances)} distancias")

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
        """Importar atletas desde Cloud Run API usando api_config.json"""
        import json
        import os
        import sys
        from src.core.athlete_importer import AthleteImporter
        from src.core.race_tracking.models import RaceDistance
        from src.core.csv_importer import CSVAthleteImporter

        # Buscar api_config.json desde la raíz del proyecto
        config_path = None
        for root in [os.path.dirname(os.path.abspath(sys.argv[0])), os.getcwd()]:
            candidate = os.path.join(root, 'config', 'api_config.json')
            if os.path.exists(candidate):
                config_path = candidate
                break

        if not config_path:
            QMessageBox.critical(self, "Configuración no encontrada",
                "No se encontró config/api_config.json.\n"
                "Verificá que el archivo exista en la carpeta config/ del proyecto.")
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error de configuración",
                                f"No se pudo leer api_config.json:\n{e}")
            return

        api_url  = config.get('api_url',  '').rstrip('/')
        api_key  = config.get('api_key',  '')
        event_id = config.get('event_id', '')

        if not api_url or not event_id:
            QMessageBox.critical(self, "Configuración incompleta",
                f"Faltan campos en api_config.json:\n"
                f"  api_url:  {'✓' if api_url  else '✗ falta'}\n"
                f"  event_id: {'✓' if event_id else '✗ falta'}\n"
                f"  api_key:  {'✓' if api_key  else '✗ (opcional)'}")
            return

        try:
            importer = AthleteImporter(api_url=api_url, api_key=api_key)
            athletes_by_dist = importer.import_athletes(event_id=event_id)

            if not athletes_by_dist:
                QMessageBox.warning(self, "Sin atletas",
                    "No se encontraron atletas con pago aprobado para este evento.\n\n"
                    "Verificá que el event_id en api_config.json sea correcto.")
                return

            # Preguntar si limpiar datos existentes
            has_existing = bool(self.race_manager.get_all_distances())
            clear_first = False
            if has_existing:
                reply = QMessageBox.question(
                    self,
                    "Datos existentes",
                    "Ya hay atletas cargados en el sistema.\n\n"
                    "¿Querés limpiar TODOS los datos antes de importar?\n\n"
                    "• Sí → borra todo y reimporta desde cero (recomendado)\n"
                    "• No → actualiza/agrega sin borrar",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Cancel:
                    return
                clear_first = (reply == QMessageBox.StandardButton.Yes)

            if clear_first:
                self.race_manager.clear_all()
                self.persistence.clear_data()
                logger.info("🗑️ Todos los datos limpiados antes de importar")

            # Reusar el mapeo de distancias del importador CSV
            distance_map = {
                info['distance_id']: info
                for info in CSVAthleteImporter.DISTANCE_MAPPING.values()
            }

            for dist_id, athletes in athletes_by_dist.items():
                if not athletes:
                    continue
                existing = self.race_manager.get_distance(dist_id)
                if existing:
                    for athlete in athletes:
                        existing_athlete = next(
                            (a for a in existing.participants if a.athlete_id == athlete.athlete_id),
                            None
                        )
                        if existing_athlete:
                            # Actualizar chip si cambió
                            if athlete.tag_id:
                                existing_athlete.tag_id = athlete.tag_id
                        else:
                            try:
                                existing.add_participant(athlete)
                            except ValueError:
                                pass
                else:
                    info = distance_map.get(dist_id, {})
                    distance = RaceDistance(
                        distance_id=dist_id,
                        name=info.get('name', dist_id.upper()),
                        distance_meters=info.get('distance_m', 0),
                        expected_checkpoints=0,
                        participants=athletes,
                        start_time=None,
                        notes=f"Importado desde API — evento {event_id}"
                    )
                    self.race_manager.add_distance(distance)

            self.refresh_athletes_table()
            self.refresh_category_filter()
            self.categories_imported.emit()

            total = sum(len(a) for a in athletes_by_dist.values())

            # Detectar chips duplicados en todo el sistema
            chip_map = {}  # chip_id -> lista de (nombre, distancia)
            for dist in self.race_manager.get_all_distances():
                for a in dist.participants:
                    if a.tag_id:
                        chip_map.setdefault(a.tag_id, []).append((a.name, dist.name))
            duplicates = {chip: owners for chip, owners in chip_map.items() if len(owners) > 1}

            msg = f"✅ Importados desde Cloud Run:\n\n• {len(athletes_by_dist)} distancias\n• {total} atletas"
            if duplicates:
                msg += f"\n\n⚠️ CHIPS DUPLICADOS ({len(duplicates)}):\n"
                for chip, owners in duplicates.items():
                    owners_str = ", ".join(f"{n} ({d})" for n, d in owners)
                    msg += f"  • Chip {chip}: {owners_str}\n"
                msg += "\nCorregí las asignaciones antes de la carrera."
                QMessageBox.warning(self, "Importación con advertencias", msg)
            else:
                QMessageBox.information(self, "Importación Exitosa", msg + "\n\nPodés asignar chips RFID a cada corredor.")

            logger.info(f"✅ Importación API: {total} atletas en {len(athletes_by_dist)} distancias")

        except Exception as e:
            QMessageBox.critical(self, "Error",
                f"Error importando desde API:\n{str(e)}\n\n"
                f"Verificá que el backend esté accesible y el api_key sea válido.")
            logger.error(f"❌ Error importando desde API: {e}")
            import traceback
            traceback.print_exc()

    @staticmethod
    def _distance_meters(category_id: str) -> float:

        """Infiere distancia en metros del nombre de categoría."""
        mapping = {
            '5K': 5000, '10K': 10000, '15K': 15000,
            '21K': 21097, '42K': 42195,
            'MEDIO': 21097, 'MEDIA': 21097,
            'MARATON': 42195, 'MARATÓN': 42195,
        }
        return float(mapping.get(category_id.upper().replace(' ', ''), 0))

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
                        nombre    = row.get('Nombre', '').strip()
                        distancia = row.get('Distancia', '').strip()

                        if not nombre:
                            not_found += 1
                            errors.append(f"Dorsal {dorsal_num}: no encontrado y sin columna Nombre para crear el atleta")
                            continue

                        try:
                            from src.core.race_tracking.models import Athlete, RaceDistance
                            from datetime import date

                            dist_id = distancia.upper().replace(' ', '_') if distancia else 'GENERAL'

                            # Buscar distancia existente o crearla
                            target_dist = self.race_manager.get_distance(dist_id)
                            if target_dist is None:
                                meters = self._distance_meters(dist_id)
                                target_dist = RaceDistance(
                                    distance_id=dist_id,
                                    name=distancia or 'General',
                                    distance_meters=meters,
                                    expected_checkpoints=0,
                                )
                                self.race_manager.add_distance(target_dist)
                                logger.info(f"✚ Distancia creada automáticamente: {distancia}")

                            # Parsear fecha de nacimiento si está disponible
                            birth_date = None
                            fecha_str = row.get('Fecha Nacimiento', '').strip()
                            if fecha_str:
                                for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
                                    try:
                                        from datetime import datetime as _dt
                                        birth_date = _dt.strptime(fecha_str, fmt).date()
                                        break
                                    except ValueError:
                                        pass

                            new_athlete = Athlete(
                                bib_number=dorsal_num,
                                name=nombre,
                                tag_id=chip_id if chip_id else None,
                                distance_id=dist_id,
                                gender=row.get('Género', '').strip() or None,
                                birth_date=birth_date,
                            )
                            target_dist.add_participant(new_athlete)
                            updated += 1
                            logger.info(f"✚ Atleta creado desde CSV: {nombre} (#{dorsal_num}) distancia={distancia} chip={chip_id}")

                        except Exception as e:
                            not_found += 1
                            errors.append(f"Error creando atleta dorsal {dorsal_num}: {e}")

            # Actualizar tabla y guardar
            self.refresh_athletes_table()
            self.refresh_category_filter()
            self.categories_imported.emit()
            self.update_stats()
            self.auto_save_data()

            # Mostrar resultado
            msg = f"✅ Importación completada:\n\n"
            msg += f"• Atletas procesados: {updated}\n"
            if not_found > 0:
                msg += f"• Errores: {not_found}\n"
            if errors:
                msg += f"\n⚠️ Advertencias:\n"
                msg += '\n'.join(errors[:5])
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
                    'Dorsal', 'Nombre', 'Distancia', 'Género', 'Fecha Nacimiento',
                    'Chip RFID', 'Estado', 'DNI', 'Email', 'Teléfono', 'Notas'
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

                        # Formatear género y fecha de nacimiento
                        gender_display = athlete.gender or ''
                        birth_date_str = athlete.birth_date.strftime('%d/%m/%Y') if athlete.birth_date else ''

                        writer.writerow([
                            athlete.bib_number,
                            athlete.name,
                            category.name,
                            gender_display,
                            birth_date_str,
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
<b>Por Distancia:</b><br>
"""

        for cat_name, stats in by_category.items():
            cat_progress = (stats['assigned'] / stats['total'] * 100) if stats['total'] > 0 else 0
            stats_text += f"• {cat_name}: {stats['assigned']}/{stats['total']} ({cat_progress:.0f}%)<br>"

        self.stats_text.setHtml(stats_text)

    def auto_save_data(self):
        """Guardar datos automáticamente (llamado después de cada asignación)"""
        try:
            if not self.race_manager:
                return

            success = self.persistence.save_race_data(self.race_manager)

            if success:
                logger.info("💾 Datos guardados automáticamente")
                # Actualizar indicador de última guardado si existe
                if hasattr(self, 'last_save_label'):
                    now = datetime.now().strftime("%H:%M:%S")
                    self.last_save_label.setText(f"💾 Guardado: {now}")
                    self.last_save_label.setStyleSheet("color: #10b981; font-size: 10px;")
            else:
                logger.warning("⚠️  Error en auto-guardado")

        except Exception as e:
            logger.error(f"❌ Error en auto-guardado: {e}")

    def auto_load_saved_data(self):
        """Cargar datos guardados automáticamente al iniciar"""
        try:
            if not self.race_manager:
                return

            if not self.persistence.has_saved_data():
                logger.info("ℹ️  No hay datos guardados previos")
                return

            # Preguntar al usuario si desea cargar los datos guardados
            last_save = self.persistence.get_last_save_time()
            if last_save:
                last_save_str = last_save.strftime("%d/%m/%Y %H:%M:%S")
            else:
                last_save_str = "desconocida"

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Sesión anterior encontrada")
            msg_box.setText(
                f"Hay datos guardados del evento anterior.\n\n"
                f"Guardado: {last_save_str}\n\n"
                f"¿Qué querés hacer?"
            )
            msg_box.setInformativeText(
                "• Retomar → carga atletas y chips del evento anterior\n"
                "• Nuevo evento → arranca vacío (el archivo guardado se conserva)\n"
                "• Eliminar datos → borra el archivo guardado definitivamente"
            )
            btn_load   = msg_box.addButton("Retomar evento anterior", QMessageBox.ButtonRole.YesRole)
            btn_skip   = msg_box.addButton("Nuevo evento",            QMessageBox.ButtonRole.NoRole)
            btn_delete = msg_box.addButton("Eliminar datos guardados", QMessageBox.ButtonRole.DestructiveRole)
            msg_box.setDefaultButton(btn_skip)
            msg_box.exec()

            clicked = msg_box.clickedButton()
            if clicked == btn_load:
                success = self.persistence.load_race_data(self.race_manager)
                if success:
                    logger.info("✅ Datos cargados exitosamente")
                else:
                    logger.error("❌ Error cargando datos guardados")
                    QMessageBox.warning(
                        self,
                        "Error de Carga",
                        "No se pudieron cargar los datos guardados.\n\n"
                        "Comenzarás con una sesión nueva."
                    )
            elif clicked == btn_delete:
                self.persistence.clear_data()
                logger.info("🗑️ Datos guardados eliminados por el usuario")

        except Exception as e:
            logger.error(f"❌ Error en auto-carga: {e}")

    def clear_all_data(self):
        """Limpiar todos los datos para comenzar una sesión nueva"""
        if not self.race_manager:
            return

        n_distances = len(self.race_manager.get_all_distances())
        n_athletes  = sum(len(d.participants) for d in self.race_manager.get_all_distances())

        reply = QMessageBox.question(
            self,
            "Nueva Sesión — Confirmar",
            f"Esto va a borrar TODOS los datos actuales:\n\n"
            f"• {n_distances} distancias\n"
            f"• {n_athletes} atletas con sus chips asignados\n"
            f"• Datos guardados en disco\n\n"
            f"Esta acción no se puede deshacer.\n\n"
            f"¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.race_manager.clear_all()
            self.persistence.clear_data()
            self.refresh_athletes_table()
            self.refresh_category_filter()
            self.update_stats()
            logger.info("🗑️ Sesión limpiada por el usuario")
            QMessageBox.information(self, "Sesión nueva", "✅ Datos borrados. Sistema listo para un nuevo evento.")

    def manual_save_data(self):
        """Guardar datos manualmente (con confirmación)"""
        try:
            if not self.race_manager:
                QMessageBox.warning(self, "Error", "No hay datos para guardar")
                return

            success = self.persistence.save_race_data(self.race_manager)

            if success:
                logger.info("💾 Guardado manual exitoso")
                QMessageBox.information(
                    self,
                    "Guardado Exitoso",
                    "✅ Datos guardados correctamente.\n\n"
                    f"Archivo: {self.persistence.data_file}"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    "❌ Error al guardar los datos.\n\nRevisa los logs para más información."
                )

        except Exception as e:
            logger.error(f"❌ Error en guardado manual: {e}")
            QMessageBox.critical(self, "Error", f"Error al guardar:\n{str(e)}")

    def on_scanner_mode_changed(self, mode: str):
        """Callback cuando cambia el modo de scanner"""
        logger.debug(f"Scanner mode changed to: {mode}")

    def on_scanner_connected(self, scanner_type: str):
        """Callback cuando se conecta un scanner"""
        if hasattr(self, 'usb_status_label') and scanner_type == "usb":
            self.usb_status_label.setText(f"✅ Conectado")
            self.usb_status_label.setStyleSheet("color: #10b981; font-size: 11px; margin-left: 20px; font-weight: bold;")

    def on_scanner_disconnected(self, scanner_type: str):
        """Callback cuando se desconecta un scanner"""
        if hasattr(self, 'usb_status_label') and scanner_type == "usb":
            self.usb_status_label.setText("📴 Lector USB no conectado")
            self.usb_status_label.setStyleSheet("")

    def __del__(self):
        """Limpieza al destruir widget"""
        try:
            # AUTO-SAVE: Guardar datos al cerrar la aplicación
            if hasattr(self, 'persistence') and hasattr(self, 'race_manager'):
                logger.info("💾 Guardando datos al cerrar aplicación...")
                self.persistence.save_race_data(self.race_manager)

            # Desconectar lector USB si está conectado
            if hasattr(self, 'usb_scanner') and self.usb_scanner and self.usb_scanner.connected:
                self.usb_scanner.stop_continuous_reading()
                self.usb_scanner.disconnect()
                logger.info("✅ Lector USB desconectado")

        except Exception as e:
            logger.debug(f"Error en limpieza de widget: {e}")
