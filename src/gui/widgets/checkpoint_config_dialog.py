#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diálogo para configurar checkpoints de una distancia
src/gui/widgets/checkpoint_config_dialog.py

Permite al usuario confirmar o modificar el número de checkpoints
cuando se detecta una nueva distancia.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QTextEdit, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class CheckpointConfigDialog(QDialog):
    """
    Diálogo para confirmar/editar configuración de checkpoints

    Se muestra cuando se detecta una nueva distancia para permitir
    al usuario verificar y ajustar el número de checkpoints.

    Casos de uso:
    - Distancias de montaña que pueden no tener checkpoints
    - Carreras urbanas con más checkpoints de lo normal
    - Confirmación de configuración automática
    """

    def __init__(self, distance_id: str, distance_name: str,
                 distance_meters: float, inferred_checkpoints: int,
                 parent=None):
        """
        Inicializar diálogo

        Args:
            distance_id: ID de la distancia (ej: "21k")
            distance_name: Nombre descriptivo (ej: "Media Maratón 21K")
            distance_meters: Distancia en metros
            inferred_checkpoints: Número de checkpoints inferido automáticamente
            parent: Widget padre
        """
        super().__init__(parent)

        self.distance_id = distance_id
        self.distance_name = distance_name
        self.distance_meters = distance_meters
        self.inferred_checkpoints = inferred_checkpoints
        self.confirmed_checkpoints = inferred_checkpoints

        self.setup_ui()

    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        self.setWindowTitle("Configurar Checkpoints")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("⚙️ Configuración de Checkpoints")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Información de la distancia
        info_group = QGroupBox("Distancia Detectada")
        info_layout = QGridLayout(info_group)

        info_layout.addWidget(QLabel("ID:"), 0, 0)
        id_label = QLabel(self.distance_id)
        id_label.setStyleSheet("font-weight: bold; color: #3b82f6;")
        info_layout.addWidget(id_label, 0, 1)

        info_layout.addWidget(QLabel("Nombre:"), 1, 0)
        name_label = QLabel(self.distance_name)
        name_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(name_label, 1, 1)

        info_layout.addWidget(QLabel("Distancia:"), 2, 0)
        distance_km = self.distance_meters / 1000.0
        distance_label = QLabel(f"{distance_km:.1f} km")
        distance_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(distance_label, 2, 1)

        layout.addWidget(info_group)

        # Configuración de checkpoints
        config_group = QGroupBox("Configuración de Checkpoints")
        config_layout = QVBoxLayout(config_group)

        # Explicación
        explanation = QLabel(
            "Los <b>checkpoints</b> son puntos de control intermedios "
            "(sin contar la largada y la meta).\n\n"
            "Ejemplos:\n"
            "• 21K urbano: 2 checkpoints típicos\n"
            "• 21K montaña: 0-1 checkpoints (puede variar)\n"
            "• 100K ultra: 5+ checkpoints"
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("background: #f0f0f0; padding: 10px; border-radius: 5px;")
        config_layout.addWidget(explanation)

        # Selector de checkpoints
        checkpoint_layout = QHBoxLayout()

        checkpoint_layout.addWidget(QLabel("Número de checkpoints:"))

        self.checkpoint_spinbox = QSpinBox()
        self.checkpoint_spinbox.setRange(0, 20)
        self.checkpoint_spinbox.setValue(self.inferred_checkpoints)
        self.checkpoint_spinbox.setToolTip(
            "Número de checkpoints intermedios (0 = solo largada y meta)"
        )
        self.checkpoint_spinbox.setStyleSheet("""
            QSpinBox {
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
                min-width: 80px;
            }
        """)
        checkpoint_layout.addWidget(self.checkpoint_spinbox)

        # Mostrar valor inferido
        inferred_label = QLabel(f"(inferido: {self.inferred_checkpoints})")
        inferred_label.setStyleSheet("color: #666; font-style: italic;")
        checkpoint_layout.addWidget(inferred_label)

        checkpoint_layout.addStretch()
        config_layout.addLayout(checkpoint_layout)

        # Advertencia si se cambia el valor
        self.warning_label = QLabel("")
        self.warning_label.setWordWrap(True)
        self.warning_label.setStyleSheet(
            "background: #fef3c7; color: #92400e; padding: 8px; "
            "border-radius: 5px; border-left: 3px solid #f59e0b;"
        )
        self.warning_label.hide()
        config_layout.addWidget(self.warning_label)

        # Conectar señal para mostrar advertencia
        self.checkpoint_spinbox.valueChanged.connect(self.on_checkpoint_changed)

        layout.addWidget(config_group)

        # Botones
        buttons_layout = QHBoxLayout()

        self.accept_btn = QPushButton("✅ Confirmar")
        self.accept_btn.clicked.connect(self.accept)
        self.accept_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background: #059669; }
        """)
        buttons_layout.addWidget(self.accept_btn)

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

        # Información adicional
        help_text = QLabel(
            "💡 Tip: Puedes cambiar esta configuración después "
            "desde la pestaña 'Configuración de Evento'"
        )
        help_text.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        help_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

    def on_checkpoint_changed(self, value):
        """Manejar cambio en el número de checkpoints"""
        if value != self.inferred_checkpoints:
            self.warning_label.setText(
                f"⚠️ Cambiaste el valor inferido ({self.inferred_checkpoints}) "
                f"a {value}. Asegúrate de que sea correcto para tu carrera."
            )
            self.warning_label.show()
        else:
            self.warning_label.hide()

    def accept(self):
        """Confirmar configuración"""
        self.confirmed_checkpoints = self.checkpoint_spinbox.value()
        logger.info(
            f"✅ Checkpoints confirmados para {self.distance_id}: "
            f"{self.confirmed_checkpoints} (inferido: {self.inferred_checkpoints})"
        )
        super().accept()

    def get_confirmed_checkpoints(self) -> int:
        """
        Obtener número de checkpoints confirmado por el usuario

        Returns:
            int: Número de checkpoints
        """
        return self.confirmed_checkpoints
