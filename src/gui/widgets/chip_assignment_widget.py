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
        self.scanner = scanner  # YR8900 (network scanner)
        self.signals = signals
        self.scan_mode = False
        self.selected_athlete = None
        self.assignments = {}  # {athlete_id: chip_id}

        # Lector USB YR9011 para kiosco de asignación
        self.usb_scanner = None
        self.scanner_mode = "network"  # "network" o "usb"

        self.setup_ui()
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

    def set_scanner_mode(self, mode: str):
        """
        Cambiar modo de scanner

        Args:
            mode: "network" para YR8900, "usb" para YR9011
        """
        self.scanner_mode = mode
        logger.info(f"🔄 Modo de scanner cambiado a: {mode}")

        if mode == "usb":
            # Conectar lector USB
            self.connect_usb_scanner()
        elif mode == "network":
            # Desconectar lector USB si está conectado
            if self.usb_scanner and self.usb_scanner.connected:
                self.usb_scanner.disconnect()

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
                self.usb_scanner = YR9011USBScanner(port=config['port'])

                # Conectar señales
                self.usb_scanner.tag_detected.connect(self.on_chip_scanned)
                self.usb_scanner.error_occurred.connect(self.on_usb_scanner_error)

                # Intentar conectar
                if self.usb_scanner.connect():
                    self.usb_status_label.setText(f"✅ Conectado a {config['port']}")
                    self.usb_status_label.setStyleSheet("color: #10b981; font-size: 11px; margin-left: 20px; font-weight: bold;")
                    logger.info(f"✅ Lector USB conectado en {config['port']}")

                    # Iniciar lectura continua
                    self.usb_scanner.start_continuous_reading()
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
                    "No hay scanner de red conectado. Cambia a modo USB o usa asignación manual."
                )
                return
        elif self.scanner_mode == "usb":
            if not self.usb_scanner or not self.usb_scanner.connected:
                QMessageBox.warning(
                    self,
                    "Lector USB No Disponible",
                    "El lector USB no está conectado. Cambia a modo de red o usa asignación manual."
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

    def start_scanning(self):
        """Iniciar modo de escaneo"""
        athlete_name = self.selected_athlete.name if self.selected_athlete else "???"
        scanner_type = "YR9011 USB" if self.scanner_mode == "usb" else "YR8900 Network"
        logger.info(f"🔍 Modo de escaneo activado para: {athlete_name}")
        logger.info(f"   • Dorsal: #{self.selected_athlete.bib_number if self.selected_athlete else '?'}")
        logger.info(f"   • Lector: {scanner_type}")
        logger.info(f"   • Esperando detección de chip...")

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

        # LOGGING DETALLADO para debugging
        logger.info(f"📡 Tag detectado: {chip_id}")
        logger.info(f"   • Modo escaneo activo: {self.scan_mode}")
        logger.info(f"   • Atleta seleccionado: {self.selected_athlete.name if self.selected_athlete else 'Ninguno'}")

        # Solo procesar si estamos en modo escaneo y hay atleta seleccionado
        if not self.scan_mode:
            logger.warning(f"⚠️  Chip {chip_id} ignorado: Modo escaneo NO activo. Haz click en '📡 Escanear Chip' primero.")
            # Mostrar notificación visual
            self.scan_status_label.setText(f"⚠️ Chip detectado ({chip_id[:8]}...) pero modo escaneo NO activo")
            self.scan_status_label.setStyleSheet("color: #f59e0b; font-weight: bold;")
            return

        if not self.selected_athlete:
            logger.warning(f"⚠️  Chip {chip_id} ignorado: No hay atleta seleccionado. Selecciona un atleta en la tabla primero.")
            # Mostrar notificación visual
            self.scan_status_label.setText(f"⚠️ Chip detectado ({chip_id[:8]}...) pero no hay atleta seleccionado")
            self.scan_status_label.setStyleSheet("color: #f59e0b; font-weight: bold;")
            return

        logger.info(f"✅ Chip {chip_id} escaneado para asignación a {self.selected_athlete.name}")

        # IMPORTANTE: Guardar referencia al atleta antes de toggle_scan_mode
        # porque toggle_scan_mode puede afectar selected_athlete
        athlete_to_assign = self.selected_athlete

        # Detener escaneo
        self.toggle_scan_mode()

        # Asignar chip (usando referencia guardada)
        self._assign_chip_to_athlete(athlete_to_assign, chip_id)

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

    def __del__(self):
        """Limpieza al destruir widget"""
        try:
            # Desconectar lector USB si está conectado
            if self.usb_scanner and self.usb_scanner.connected:
                self.usb_scanner.stop_continuous_reading()
                self.usb_scanner.disconnect()
                logger.info("✅ Lector USB desconectado")
        except Exception as e:
            logger.debug(f"Error en limpieza de widget: {e}")
