#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Category Configuration Dialog
src/gui/category_config_dialog.py

Dialog to configure race category details: distance, start time, checkpoints, etc.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateTimeEdit, QTextEdit,
    QFormLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont
from typing import Optional
from datetime import datetime


class CategoryConfigDialog(QDialog):
    """Dialog to configure race category settings"""

    def __init__(self, category=None, parent=None):
        """
        Args:
            category: Optional RaceCategory to edit (None for new category)
            parent: Parent widget
        """
        super().__init__(parent)
        self.category = category
        self.setup_ui()

        # Load existing data if editing
        if category:
            self.load_category_data()

    def setup_ui(self):
        """Setup dialog UI"""
        title = "Editar Distancia" if self.category else "Nueva Distancia"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel(f"⚙️ {title}")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # Basic Info Group
        basic_group = QGroupBox("Información Básica")
        basic_layout = QFormLayout(basic_group)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: 5 Kilómetros, 10K, Media Maratón")
        basic_layout.addRow("Nombre de Distancia *:", self.name_input)

        self.category_id_input = QLineEdit()
        self.category_id_input.setPlaceholderText("Ej: 5k, 10k, half-marathon")
        if self.category:
            self.category_id_input.setReadOnly(True)
            self.category_id_input.setStyleSheet("background: #f3f4f6;")
        basic_layout.addRow("ID de Distancia *:", self.category_id_input)

        layout.addWidget(basic_group)

        # Race Details Group
        race_group = QGroupBox("Detalles de la Carrera")
        race_layout = QFormLayout(race_group)

        self.distance_input = QDoubleSpinBox()
        self.distance_input.setRange(0, 100000)
        self.distance_input.setValue(5000)
        self.distance_input.setSuffix(" metros")
        self.distance_input.setStepType(QDoubleSpinBox.StepType.AdaptiveDecimalStepType)
        race_layout.addRow("Distancia *:", self.distance_input)

        self.start_time_input = QDateTimeEdit()
        self.start_time_input.setDateTime(QDateTime.currentDateTime())
        self.start_time_input.setCalendarPopup(True)
        self.start_time_input.setDisplayFormat("dd/MM/yyyy HH:mm:ss")
        race_layout.addRow("Hora de Largada:", self.start_time_input)

        self.checkpoints_input = QSpinBox()
        self.checkpoints_input.setRange(0, 50)
        self.checkpoints_input.setValue(0)
        self.checkpoints_input.setSuffix(" checkpoints")
        self.checkpoints_input.setToolTip("Número de puntos de control intermedios (sin contar largada/meta)")
        race_layout.addRow("Checkpoints:", self.checkpoints_input)

        layout.addWidget(race_group)

        # Notes Group
        notes_group = QGroupBox("Notas")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas adicionales sobre la distancia...")
        self.notes_input.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_input)

        layout.addWidget(notes_group)

        # Distance Presets
        presets_label = QLabel("Atajos de Distancia:")
        presets_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 10px;")
        layout.addWidget(presets_label)

        presets_layout = QHBoxLayout()
        presets = [
            ("5K", 5000),
            ("10K", 10000),
            ("15K", 15000),
            ("Media Maratón", 21097.5),
            ("Maratón", 42195)
        ]

        for name, distance in presets:
            btn = QPushButton(name)
            btn.setStyleSheet("""
                QPushButton {
                    background: #e5e7eb;
                    padding: 5px 10px;
                    border-radius: 3px;
                    font-size: 11px;
                }
                QPushButton:hover { background: #d1d5db; }
            """)
            btn.clicked.connect(lambda checked, d=distance: self.distance_input.setValue(d))
            presets_layout.addWidget(btn)

        presets_layout.addStretch()
        layout.addLayout(presets_layout)

        # Required fields note
        required_note = QLabel("* Campos obligatorios")
        required_note.setStyleSheet("color: #ef4444; font-size: 11px; margin-top: 10px;")
        layout.addWidget(required_note)

        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #6b7280;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover { background: #4b5563; }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        save_btn = QPushButton("✅ Guardar")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background: #059669; }
        """)
        save_btn.clicked.connect(self.accept)
        save_btn.setDefault(True)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

    def load_category_data(self):
        """Load existing category data into form"""
        if not self.category:
            return

        self.name_input.setText(self.category.name)
        self.category_id_input.setText(self.category.distance_id)
        self.distance_input.setValue(self.category.distance)
        self.checkpoints_input.setValue(self.category.expected_checkpoints)

        if self.category.start_time:
            qt_datetime = QDateTime(self.category.start_time)
            self.start_time_input.setDateTime(qt_datetime)

        if self.category.notes:
            self.notes_input.setPlainText(self.category.notes)

    def get_category_data(self) -> dict:
        """Get category data from form"""
        return {
            'name': self.name_input.text().strip(),
            'distance_id': self.category_id_input.text().strip(),
            'distance': self.distance_input.value(),
            'expected_checkpoints': self.checkpoints_input.value(),
            'start_time': self.start_time_input.dateTime().toPyDateTime(),
            'notes': self.notes_input.toPlainText().strip() or None
        }

    def validate(self) -> bool:
        """Validate form data"""
        data = self.get_category_data()

        if not data['name']:
            QMessageBox.warning(self, "Error", "El nombre de la distancia es obligatorio")
            return False

        if not data['distance_id']:
            QMessageBox.warning(self, "Error", "El ID de distancia es obligatorio")
            return False

        if data['distance'] <= 0:
            QMessageBox.warning(self, "Error", "La distancia debe ser mayor a 0")
            return False

        return True

    def accept(self):
        """Override accept to validate before closing"""
        if self.validate():
            super().accept()
