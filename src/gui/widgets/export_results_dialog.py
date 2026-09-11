#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diálogo para exportar resultados de carreras
src/gui/widgets/export_results_dialog.py

Permite al usuario elegir formato, distancia y opciones de exportación.
"""

import logging
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QCheckBox, QGroupBox, QGridLayout, QLineEdit,
    QFileDialog, QMessageBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.core.race_tracking.results_exporter import ResultsExporter, ExportConfig

logger = logging.getLogger(__name__)


class ExportResultsDialog(QDialog):
    """
    Diálogo para exportar resultados de carreras

    Permite seleccionar:
    - Formato de exportación (CSV, PDF, Excel)
    - Distancia específica o todas
    - Opciones de contenido (splits, categorías, etc.)
    - Ubicación del archivo
    """

    def __init__(self, race_manager, parent=None):
        """
        Inicializar diálogo

        Args:
            race_manager: Instancia de RaceManager con los resultados
            parent: Widget padre
        """
        super().__init__(parent)

        self.race_manager = race_manager
        self.exporter = ResultsExporter(race_manager)

        self.setup_ui()
        self.setModal(True)

    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle("Exportar Resultados")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("📊 Exportar Resultados de Carrera")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Grupo: Formato de exportación
        format_group = QGroupBox("Formato de Exportación")
        format_layout = QVBoxLayout(format_group)

        self.format_group = QButtonGroup(self)

        self.csv_radio = QRadioButton("CSV - Archivo compatible con Excel")
        self.csv_radio.setToolTip("Formato CSV separado por punto y coma, ideal para abrir en Excel")
        self.csv_radio.setChecked(True)
        self.format_group.addButton(self.csv_radio, 1)
        format_layout.addWidget(self.csv_radio)

        self.pdf_radio = QRadioButton("PDF - Documento imprimible")
        self.pdf_radio.setToolTip("Resultados formateados para imprimir")
        self.format_group.addButton(self.pdf_radio, 2)
        format_layout.addWidget(self.pdf_radio)

        self.excel_radio = QRadioButton("Excel - Archivo .xlsx con múltiples hojas")
        self.excel_radio.setToolTip("Archivo Excel nativo con formato profesional")
        self.format_group.addButton(self.excel_radio, 3)
        format_layout.addWidget(self.excel_radio)

        layout.addWidget(format_group)

        # Grupo: Selección de distancia
        distance_group = QGroupBox("Distancia a Exportar")
        distance_layout = QVBoxLayout(distance_group)

        self.distance_combo = QComboBox()
        self.distance_combo.addItem("Todas las distancias", None)

        # Agregar distancias disponibles
        distances = self.race_manager.get_all_distances()
        for distance in distances:
            self.distance_combo.addItem(distance.name, distance.distance_id)

        distance_layout.addWidget(self.distance_combo)
        layout.addWidget(distance_group)

        # Grupo: Información del evento
        event_group = QGroupBox("Información del Evento (Opcional)")
        event_layout = QGridLayout(event_group)

        event_layout.addWidget(QLabel("Nombre del evento:"), 0, 0)
        self.event_name_input = QLineEdit()
        self.event_name_input.setPlaceholderText("Ej: Maratón Ciudad 2026")
        event_layout.addWidget(self.event_name_input, 0, 1)

        event_layout.addWidget(QLabel("Organizador:"), 1, 0)
        self.organizer_input = QLineEdit()
        self.organizer_input.setPlaceholderText("Ej: Club Atlético")
        event_layout.addWidget(self.organizer_input, 1, 1)

        layout.addWidget(event_group)

        # Grupo: Opciones de contenido
        options_group = QGroupBox("Opciones de Contenido")
        options_layout = QVBoxLayout(options_group)

        self.include_splits_check = QCheckBox("Incluir tiempos parciales (checkpoints)")
        self.include_splits_check.setChecked(True)
        self.include_splits_check.setToolTip("Mostrar tiempos intermedios de cada checkpoint")
        options_layout.addWidget(self.include_splits_check)

        self.include_categories_check = QCheckBox("Incluir clasificaciones por categoría de edad")
        self.include_categories_check.setChecked(True)
        self.include_categories_check.setToolTip("Mostrar clasificaciones separadas por categoría")
        options_layout.addWidget(self.include_categories_check)

        self.include_awards_check = QCheckBox("Incluir podios por categoría de premiación")
        self.include_awards_check.setChecked(True)
        self.include_awards_check.setToolTip("Mostrar clasificaciones para premiación")
        options_layout.addWidget(self.include_awards_check)

        layout.addWidget(options_group)

        # Ubicación del archivo
        file_group = QGroupBox("Archivo de Destino")
        file_layout = QHBoxLayout(file_group)

        self.filepath_input = QLineEdit()
        self.filepath_input.setPlaceholderText("Selecciona ubicación...")
        self.filepath_input.setReadOnly(True)
        file_layout.addWidget(self.filepath_input)

        self.browse_btn = QPushButton("📁 Explorar...")
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)

        layout.addWidget(file_group)

        # Botones de acción
        buttons_layout = QHBoxLayout()

        self.export_btn = QPushButton("✅ Exportar")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background: #059669; }
            QPushButton:disabled { background: #9ca3af; }
        """)
        self.export_btn.setEnabled(False)  # Deshabilitado hasta elegir archivo
        buttons_layout.addWidget(self.export_btn)

        self.cancel_btn = QPushButton("❌ Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover { background: #4b5563; }
        """)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)

        # Conectar señales
        self.filepath_input.textChanged.connect(self.on_filepath_changed)

    def browse_file(self):
        """Abrir diálogo para seleccionar ubicación del archivo"""
        # Determinar extensión según formato seleccionado
        if self.csv_radio.isChecked():
            filter_str = "Archivos CSV (*.csv)"
            default_ext = ".csv"
        elif self.pdf_radio.isChecked():
            filter_str = "Archivos PDF (*.pdf)"
            default_ext = ".pdf"
        else:  # Excel
            filter_str = "Archivos Excel (*.xlsx)"
            default_ext = ".xlsx"

        # Nombre sugerido
        distance_name = self.distance_combo.currentText()
        if distance_name == "Todas las distancias":
            suggested_name = f"resultados_{datetime.now().strftime('%Y%m%d_%H%M%S')}{default_ext}"
        else:
            safe_name = distance_name.replace(" ", "_").replace("/", "-")
            suggested_name = f"resultados_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{default_ext}"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Resultados",
            suggested_name,
            filter_str
        )

        if filepath:
            self.filepath_input.setText(filepath)

    def on_filepath_changed(self, text):
        """Habilitar botón de exportar cuando hay archivo seleccionado"""
        self.export_btn.setEnabled(bool(text))

    def export_results(self):
        """Ejecutar exportación de resultados"""
        try:
            # Validar que hay un archivo seleccionado
            filepath = self.filepath_input.text()
            if not filepath:
                QMessageBox.warning(self, "Error", "Debes seleccionar un archivo de destino")
                return

            # Obtener configuración
            config = ExportConfig(
                event_name=self.event_name_input.text() or "Carrera",
                event_date=datetime.now(),
                organizer=self.organizer_input.text() or "",
                include_splits=self.include_splits_check.isChecked(),
                include_categories=self.include_categories_check.isChecked(),
                include_awards=self.include_awards_check.isChecked()
            )

            # Obtener distancia seleccionada
            distance_id = self.distance_combo.currentData()

            # Ejecutar exportación según formato
            success = False

            if self.csv_radio.isChecked():
                success = self.exporter.export_csv(filepath, distance_id, config)
            elif self.pdf_radio.isChecked():
                success = self.exporter.export_pdf(filepath, distance_id, config)
            else:  # Excel
                success = self.exporter.export_excel(filepath, distance_id, config)

            if success:
                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"✅ Resultados exportados correctamente a:\n{filepath}"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Error de Exportación",
                    "❌ No se pudo exportar los resultados.\n\n"
                    "Verifica que:\n"
                    "• Tengas permisos de escritura\n"
                    "• El archivo no esté abierto en otra aplicación"
                )

        except ImportError as e:
            # Error de librería faltante
            missing_lib = "reportlab" if "reportlab" in str(e) else "openpyxl"
            format_name = "PDF" if missing_lib == "reportlab" else "Excel"

            QMessageBox.warning(
                self,
                f"Librería {missing_lib} no instalada",
                f"⚠️ Para exportar a {format_name} necesitas instalar la librería {missing_lib}.\n\n"
                f"Ejecuta en la terminal:\n\n"
                f"   pip install {missing_lib}\n\n"
                f"Mientras tanto, puedes exportar a CSV que no requiere librerías adicionales."
            )

        except Exception as e:
            logger.error(f"❌ Error en exportación: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Error",
                f"❌ Error inesperado durante la exportación:\n{str(e)}"
            )
