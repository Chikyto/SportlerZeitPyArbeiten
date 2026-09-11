#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multiple Chip Selection Dialog
src/gui/multiple_chip_dialog.py

Shows a dialog to select one chip when multiple tags are detected.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import List, Dict, Optional


class MultipleChipDialog(QDialog):
    """
    Dialog to select one chip from multiple detected tags

    Shows chips sorted by RSSI (signal strength) to help select the closest one.
    """

    def __init__(self, chips: List[Dict], parent=None):
        """
        Args:
            chips: List of chip dicts with 'tag_id', 'rssi', 'timestamp'
            parent: Parent widget
        """
        super().__init__(parent)
        self.chips = sorted(chips, key=lambda x: x.get('rssi', 0), reverse=True)
        self.selected_chip = None
        self.setup_ui()

    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Múltiples Chips Detectados")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("⚠️ Se Detectaron Múltiples Chips")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Instruction
        instruction = QLabel(
            "Selecciona el chip que deseas asignar.\n"
            "Los chips están ordenados por señal (más fuerte = más cerca)."
        )
        instruction.setStyleSheet("color: #666; margin: 10px 0;")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setWordWrap(True)
        layout.addWidget(instruction)

        # Chips group
        chips_group = QGroupBox("Chips Detectados")
        chips_layout = QVBoxLayout(chips_group)

        self.button_group = QButtonGroup(self)

        for i, chip in enumerate(self.chips):
            chip_id = chip.get('tag_id', 'Unknown')
            rssi = chip.get('rssi', 0)

            # Signal strength indicator
            if rssi > 50:
                signal_icon = "🟢"  # Strong signal
                signal_text = "Muy cerca"
            elif rssi > 30:
                signal_icon = "🟡"  # Medium signal
                signal_text = "Cerca"
            else:
                signal_icon = "🔴"  # Weak signal
                signal_text = "Lejos"

            # Radio button with chip info
            radio = QRadioButton(
                f"{signal_icon} Chip {chip_id}  |  Señal: {rssi}  ({signal_text})"
            )
            radio.setStyleSheet("font-size: 12px; padding: 8px;")

            # Pre-select the strongest signal (first one)
            if i == 0:
                radio.setChecked(True)
                self.selected_chip = chip_id

            # Store chip_id in radio button
            radio.setProperty("chip_id", chip_id)

            # Connect signal
            radio.toggled.connect(lambda checked, cid=chip_id: self.on_chip_selected(checked, cid))

            self.button_group.addButton(radio)
            chips_layout.addWidget(radio)

        layout.addWidget(chips_group)

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
                font-size: 13px;
            }
            QPushButton:hover { background: #4b5563; }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        assign_btn = QPushButton("✅ Asignar Este Chip")
        assign_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: #059669; }
        """)
        assign_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(assign_btn)

        layout.addLayout(buttons_layout)

    def on_chip_selected(self, checked: bool, chip_id: str):
        """Handle chip selection"""
        if checked:
            self.selected_chip = chip_id

    def get_selected_chip(self) -> Optional[str]:
        """Get the selected chip ID"""
        return self.selected_chip
