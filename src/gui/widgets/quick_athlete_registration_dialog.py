#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diálogo de Registro Rápido de Atletas
src/gui/widgets/quick_athlete_registration_dialog.py

Permite registrar un nuevo corredor directamente desde
la interfaz de asignación de chips (casos excepcionales).
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QComboBox, QDateEdit, QPushButton, QMessageBox,
    QGroupBox, QSpinBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QuickAthleteRegistrationDialog(QDialog):
    """
    Diálogo para registro rápido de atletas excepcionales

    Permite ingresar:
    - Nombre completo
    - Género (M/F/Otro)
    - Fecha de nacimiento
    - Distancia a correr
    - Número de dorsal (auto o manual)
    - Chip RFID (pre-llenado desde escaneo)
    """

    def __init__(self, chip_id: str = "", race_manager=None, parent=None):
        super().__init__(parent)
        self.chip_id = chip_id
        self.race_manager = race_manager
        self.athlete_data = None  # Se llena si el usuario confirma

        self.setup_ui()

    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle("🏃 Registro Rápido de Corredor")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("Registro de Corredor Excepcional")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtítulo explicativo
        subtitle = QLabel(
            "Este corredor no está en el sistema. Ingresa sus datos para registrarlo ahora."
        )
        subtitle.setStyleSheet("color: #666; margin-bottom: 15px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Formulario de datos
        form_group = QGroupBox("Datos del Corredor")
        form_layout = QFormLayout(form_group)

        # Nombre
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Juan Pérez")
        form_layout.addRow("Nombre Completo: *", self.name_input)

        # Género
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Masculino", "Femenino", "Otro"])
        form_layout.addRow("Género: *", self.gender_combo)

        # Fecha de nacimiento
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDisplayFormat("dd/MM/yyyy")
        # Fecha por defecto: hace 30 años
        default_date = QDate.currentDate().addYears(-30)
        self.birth_date_input.setDate(default_date)
        # Límites: entre 1920 y hoy
        self.birth_date_input.setMinimumDate(QDate(1920, 1, 1))
        self.birth_date_input.setMaximumDate(QDate.currentDate())
        form_layout.addRow("Fecha de Nacimiento: *", self.birth_date_input)

        # Distancia (categoría)
        self.distance_combo = QComboBox()
        self.populate_distances()
        form_layout.addRow("Distancia/Categoría: *", self.distance_combo)

        # Número de dorsal
        dorsal_layout = QHBoxLayout()
        self.dorsal_auto_radio = QPushButton("Generar Automático")
        self.dorsal_auto_radio.setCheckable(True)
        self.dorsal_auto_radio.setChecked(True)
        self.dorsal_auto_radio.clicked.connect(self.on_dorsal_mode_changed)
        dorsal_layout.addWidget(self.dorsal_auto_radio)

        self.dorsal_manual_input = QSpinBox()
        self.dorsal_manual_input.setRange(1, 9999)
        self.dorsal_manual_input.setValue(1)
        self.dorsal_manual_input.setEnabled(False)
        dorsal_layout.addWidget(self.dorsal_manual_input)

        form_layout.addRow("Número de Dorsal:", dorsal_layout)

        # Chip RFID (pre-llenado, read-only)
        self.chip_input = QLineEdit()
        self.chip_input.setText(self.chip_id)
        self.chip_input.setReadOnly(True)
        self.chip_input.setStyleSheet("background: #f0f0f0; color: #666;")
        form_layout.addRow("Chip RFID:", self.chip_input)

        layout.addWidget(form_group)

        # Nota sobre campos obligatorios
        required_note = QLabel("* Campos obligatorios")
        required_note.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(required_note)

        # Botones
        buttons_layout = QHBoxLayout()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        buttons_layout.addStretch()

        self.register_btn = QPushButton("✅ Registrar y Asignar Chip")
        self.register_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background: #059669; }
            QPushButton:disabled { background: #d1d5db; }
        """)
        self.register_btn.clicked.connect(self.on_register)
        buttons_layout.addWidget(self.register_btn)

        layout.addLayout(buttons_layout)

    def populate_distances(self):
        """Poblar combo de distancias desde race_manager"""
        if not self.race_manager:
            # Distancias por defecto
            self.distance_combo.addItems(["5K", "10K", "21K", "42K"])
            return

        # Obtener categorías (distancias) del race_manager
        categories = self.race_manager.get_all_categories()

        if not categories:
            # Si no hay categorías, usar valores por defecto
            self.distance_combo.addItems(["5K", "10K", "21K", "42K"])
            return

        # Agregar categorías existentes
        for category in categories:
            # Mostrar nombre amigable (ej: "5 Kilómetros (5k)")
            display_name = f"{category.name} ({category.category_id})"
            self.distance_combo.addItem(display_name, category.category_id)

    def on_dorsal_mode_changed(self):
        """Cambiar entre modo automático y manual para dorsal"""
        is_auto = self.dorsal_auto_radio.isChecked()
        self.dorsal_manual_input.setEnabled(not is_auto)

        if is_auto:
            self.dorsal_auto_radio.setText("Generar Automático")
        else:
            self.dorsal_auto_radio.setText("Ingresar Manual")

    def validate_input(self) -> bool:
        """
        Validar que todos los campos obligatorios estén completos

        Returns:
            bool: True si es válido, False si falta algo
        """
        # Nombre
        if not self.name_input.text().strip():
            QMessageBox.warning(
                self,
                "Campo Requerido",
                "Por favor ingresa el nombre completo del corredor."
            )
            self.name_input.setFocus()
            return False

        # Distancia
        if self.distance_combo.currentIndex() < 0:
            QMessageBox.warning(
                self,
                "Campo Requerido",
                "Por favor selecciona la distancia que correrá."
            )
            self.distance_combo.setFocus()
            return False

        return True

    def on_register(self):
        """Procesar registro cuando se hace click en registrar"""
        if not self.validate_input():
            return

        try:
            # Extraer datos del formulario
            full_name = self.name_input.text().strip()

            # Género (normalizar a M/F/Otro)
            gender_text = self.gender_combo.currentText()
            if gender_text == "Masculino":
                gender = "M"
            elif gender_text == "Femenino":
                gender = "F"
            else:
                gender = "Otro"

            # Fecha de nacimiento
            birth_qdate = self.birth_date_input.date()
            birth_date = datetime(birth_qdate.year(), birth_qdate.month(), birth_qdate.day())

            # Distancia (category_id)
            category_id = self.distance_combo.currentData()
            if not category_id:
                # Si no hay data asociada, usar el texto como category_id
                # (ej: "5K" -> "5k")
                category_id = self.distance_combo.currentText().lower().replace("k", "k")

            # Número de dorsal
            if self.dorsal_auto_radio.isChecked():
                # Generar automático (delegarlo al race_manager)
                bib_number = None  # Se generará después
            else:
                bib_number = self.dorsal_manual_input.value()

            # Chip RFID
            chip_id = self.chip_input.text().strip()

            # Guardar datos
            self.athlete_data = {
                'name': full_name,
                'gender': gender,
                'birth_date': birth_date,
                'category_id': category_id,
                'bib_number': bib_number,
                'chip_id': chip_id
            }

            logger.info(f"✅ Datos de atleta excepcional capturados: {full_name} ({gender}, {category_id})")

            # Aceptar diálogo
            self.accept()

        except Exception as e:
            logger.error(f"❌ Error procesando registro: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al procesar el registro:\n{str(e)}"
            )

    def get_athlete_data(self) -> dict:
        """
        Obtener datos del atleta ingresados

        Returns:
            dict con datos del atleta o None si se canceló
        """
        return self.athlete_data


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    # Mostrar diálogo de prueba
    dialog = QuickAthleteRegistrationDialog(chip_id="E280116060000209C882B827")

    if dialog.exec() == QDialog.DialogCode.Accepted:
        data = dialog.get_athlete_data()
        print("\n✅ Atleta registrado:")
        print(f"   • Nombre: {data['name']}")
        print(f"   • Género: {data['gender']}")
        print(f"   • Nacimiento: {data['birth_date']}")
        print(f"   • Distancia: {data['category_id']}")
        print(f"   • Dorsal: {data['bib_number'] or 'AUTO'}")
        print(f"   • Chip: {data['chip_id']}")
    else:
        print("\n❌ Registro cancelado")

    sys.exit(0)
