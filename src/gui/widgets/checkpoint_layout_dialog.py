#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diálogo de ubicación de checkpoints en el recorrido
src/gui/widgets/checkpoint_layout_dialog.py

Permite definir, para cada checkpoint de una distancia:
- el kilómetro donde está ubicado (habilita las ventanas de tiempo que
  evitan relecturas fantasma y splits corridos)
- la antena física que lo cubre (opcional; identifica el CP aunque al
  corredor no le hayan leído los anteriores)

No confundir con checkpoint_config_dialog.py, que solo confirma la
CANTIDAD de checkpoints al detectar una distancia nueva.
"""

import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QComboBox, QDoubleSpinBox, QDialogButtonBox,
    QMessageBox, QTableWidgetItem
)
from PyQt6.QtCore import Qt

from src.core.race_tracking.checkpoint_config import CheckpointDef

logger = logging.getLogger(__name__)

NO_ANTENNA_LABEL = "— (por secuencia)"


class CheckpointLayoutDialog(QDialog):
    """
    Editor del recorrido de checkpoints de una distancia.

    Example:
        >>> dlg = CheckpointLayoutDialog(distance, antenna_ports=[3, 7])
        >>> if dlg.exec():
        ...     distance.checkpoints = dlg.get_checkpoints()
    """

    def __init__(self, distance, antenna_ports=None, parent=None):
        """
        Args:
            distance: RaceDistance a configurar
            antenna_ports: Puertos de antenas con rol checkpoint
                           disponibles (para el combo de asignación)
            parent: Widget padre
        """
        super().__init__(parent)
        self.distance = distance
        self.antenna_ports = antenna_ports or []

        self.setWindowTitle(f"Checkpoints — {distance.name}")
        self.setMinimumWidth(540)
        self.setModal(True)
        self._setup_ui()
        self._load_existing()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            f"Recorrido de <b>{self.distance.name}</b> "
            f"({self.distance.distance_meters / 1000:.1f} km).<br>"
            "El <b>km</b> de cada checkpoint habilita las ventanas de "
            "tiempo (no hace falta que sea exacto, ±20% alcanza). "
            "La <b>antena</b> identifica el CP aunque falte una lectura "
            "anterior."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["CP Nº", "Km del recorrido", "Antena"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 160)
        layout.addWidget(self.table)

        row_buttons = QHBoxLayout()
        add_btn = QPushButton("➕ Agregar CP")
        add_btn.clicked.connect(self._add_row)
        row_buttons.addWidget(add_btn)

        remove_btn = QPushButton("➖ Quitar último")
        remove_btn.clicked.connect(self._remove_last_row)
        row_buttons.addWidget(remove_btn)
        row_buttons.addStretch()
        layout.addLayout(row_buttons)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_existing(self):
        existing = getattr(self.distance, 'checkpoints', None) or []
        if existing:
            for cp in sorted(existing, key=lambda c: c.number):
                self._add_row(km=cp.km, antenna_port=cp.antenna_port)
        else:
            # Pre-poblar según la cantidad esperada, con km repartidos
            # uniformes para que solo haya que ajustarlos
            n = self.distance.expected_checkpoints or 0
            total_km = self.distance.distance_meters / 1000.0
            for i in range(1, n + 1):
                km = round(total_km * i / (n + 1), 1)
                self._add_row(km=km)

    def _add_row(self, checked=False, km=None, antenna_port=None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        num_item = QTableWidgetItem(str(row + 1))
        num_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # solo lectura
        self.table.setItem(row, 0, num_item)

        km_spin = QDoubleSpinBox()
        km_spin.setRange(0.1, 1000.0)
        km_spin.setDecimals(1)
        km_spin.setSingleStep(0.5)
        km_spin.setSuffix(" km")
        km_spin.setValue(km if km is not None else 1.0)
        self.table.setCellWidget(row, 1, km_spin)

        antenna_combo = QComboBox()
        antenna_combo.addItem(NO_ANTENNA_LABEL, None)
        for port in self.antenna_ports:
            antenna_combo.addItem(f"Puerto {port}", port)
        if antenna_port is not None:
            idx = antenna_combo.findData(antenna_port)
            if idx < 0:
                # Antena guardada que hoy no está configurada: conservarla
                antenna_combo.addItem(f"Puerto {antenna_port} (no detectado)", antenna_port)
                idx = antenna_combo.count() - 1
            antenna_combo.setCurrentIndex(idx)
        self.table.setCellWidget(row, 2, antenna_combo)

    def _remove_last_row(self):
        if self.table.rowCount() > 0:
            self.table.removeRow(self.table.rowCount() - 1)

    def _validate_and_accept(self):
        """Validar km crecientes y dentro del recorrido"""
        total_km = self.distance.distance_meters / 1000.0
        prev_km = 0.0
        for row in range(self.table.rowCount()):
            km = self.table.cellWidget(row, 1).value()
            if km <= prev_km:
                QMessageBox.warning(
                    self, "Kilometraje inválido",
                    f"El CP{row + 1} (km {km}) debe estar después "
                    f"del punto anterior (km {prev_km})."
                )
                return
            if km >= total_km:
                QMessageBox.warning(
                    self, "Kilometraje inválido",
                    f"El CP{row + 1} (km {km}) no puede estar en o después "
                    f"de la meta ({total_km:.1f} km)."
                )
                return
            prev_km = km
        self.accept()

    def get_checkpoints(self):
        """Checkpoints definidos en el diálogo (tras accept)"""
        checkpoints = []
        for row in range(self.table.rowCount()):
            checkpoints.append(CheckpointDef(
                number=row + 1,
                km=self.table.cellWidget(row, 1).value(),
                antenna_port=self.table.cellWidget(row, 2).currentData(),
            ))
        return checkpoints
