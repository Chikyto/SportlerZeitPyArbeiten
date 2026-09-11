#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diálogo de configuración para lector USB YR9011
src/gui/usb_scanner_config_dialog.py
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QGroupBox, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class USBScannerConfigDialog(QDialog):
    """
    Diálogo para configurar conexión con lector USB

    Permite:
    - Seleccionar puerto COM manualmente
    - Probar conexión
    - Ver puertos disponibles
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_port = None
        self.selected_baudrate = 115200
        self.setup_ui()
        self.refresh_ports()

    def setup_ui(self):
        """Configurar interfaz"""
        self.setWindowTitle("Configuración Lector USB YR9011")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Título
        title = QLabel("🔌 Configuración Lector USB")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Instrucciones
        instructions = QLabel(
            "Selecciona el puerto COM donde está conectado el lector YR9011.\n"
            "Si no aparece, verifica que esté conectado y que los drivers estén instalados."
        )
        instructions.setStyleSheet("color: #666; padding: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Grupo de puerto COM
        port_group = QGroupBox("Puerto COM")
        port_layout = QVBoxLayout(port_group)

        port_select_layout = QHBoxLayout()
        port_select_layout.addWidget(QLabel("Puerto:"))

        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(300)
        port_select_layout.addWidget(self.port_combo)

        self.refresh_button = QPushButton("🔄 Actualizar")
        self.refresh_button.clicked.connect(self.refresh_ports)
        port_select_layout.addWidget(self.refresh_button)

        port_layout.addLayout(port_select_layout)

        # Información del puerto seleccionado
        self.port_info_label = QLabel("")
        self.port_info_label.setStyleSheet(
            "background: #f0f0f0; padding: 10px; border-radius: 5px; font-size: 12px;"
        )
        self.port_info_label.setWordWrap(True)
        port_layout.addWidget(self.port_info_label)

        layout.addWidget(port_group)

        # Grupo de velocidad (baudrate)
        baudrate_group = QGroupBox("Velocidad de Comunicación")
        baudrate_layout = QHBoxLayout(baudrate_group)

        baudrate_layout.addWidget(QLabel("Baudrate:"))

        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems([
            "115200 bps (recomendado)",
            "57600 bps",
            "9600 bps"
        ])
        self.baudrate_combo.setCurrentIndex(0)
        baudrate_layout.addWidget(self.baudrate_combo)

        baudrate_layout.addStretch()

        layout.addWidget(baudrate_group)

        # Botón de prueba
        self.test_button = QPushButton("🔍 Probar Conexión")
        self.test_button.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover { background: #2563eb; }
        """)
        self.test_button.clicked.connect(self.test_connection)
        layout.addWidget(self.test_button)

        # Resultado del test
        self.test_result_label = QLabel("")
        self.test_result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.test_result_label.setWordWrap(True)
        layout.addWidget(self.test_result_label)

        # Botones de acción
        buttons_layout = QHBoxLayout()

        self.connect_button = QPushButton("✅ Conectar")
        self.connect_button.setEnabled(False)
        self.connect_button.setStyleSheet("""
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
        self.connect_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.connect_button)

        cancel_button = QPushButton("❌ Cancelar")
        cancel_button.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover { background: #dc2626; }
        """)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)

        # Conectar cambio de selección
        self.port_combo.currentTextChanged.connect(self.on_port_changed)

    def refresh_ports(self):
        """Actualizar lista de puertos disponibles"""
        try:
            from src.core.yr9011_usb_scanner import YR9011USBScanner

            self.port_combo.clear()
            ports = YR9011USBScanner.list_available_ports()

            if not ports:
                self.port_combo.addItem("No se encontraron puertos COM")
                self.port_info_label.setText(
                    "⚠️ No se detectaron puertos COM.\n\n"
                    "Verifica:\n"
                    "• Que el lector esté conectado al USB\n"
                    "• Que los drivers estén instalados\n"
                    "• Que el dispositivo esté encendido"
                )
                self.port_info_label.setStyleSheet(
                    "background: #fef3c7; padding: 10px; border-radius: 5px; font-size: 12px;"
                )
                return

            for port_info in ports:
                display_text = f"{port_info['port']} - {port_info['description']}"
                self.port_combo.addItem(display_text, port_info)

            logger.info(f"✅ {len(ports)} puertos COM detectados")

        except Exception as e:
            logger.error(f"❌ Error listando puertos: {e}")
            self.port_combo.addItem("Error listando puertos")

    def on_port_changed(self, text):
        """Manejar cambio de puerto seleccionado"""
        index = self.port_combo.currentIndex()
        port_info = self.port_combo.itemData(index)

        if port_info:
            info_text = f"<b>Puerto:</b> {port_info['port']}<br>"
            info_text += f"<b>Descripción:</b> {port_info['description']}<br>"
            info_text += f"<b>Hardware ID:</b> {port_info['hwid']}"

            self.port_info_label.setText(info_text)
            self.port_info_label.setStyleSheet(
                "background: #dbeafe; padding: 10px; border-radius: 5px; font-size: 12px;"
            )

            self.selected_port = port_info['port']
            self.test_result_label.setText("")
            self.connect_button.setEnabled(False)

    def test_connection(self):
        """Probar conexión con el puerto seleccionado"""
        if not self.selected_port:
            QMessageBox.warning(
                self,
                "Selecciona un Puerto",
                "Primero selecciona un puerto COM de la lista."
            )
            return

        # Obtener baudrate
        baudrate_text = self.baudrate_combo.currentText()
        if "115200" in baudrate_text:
            self.selected_baudrate = 115200
        elif "57600" in baudrate_text:
            self.selected_baudrate = 57600
        elif "9600" in baudrate_text:
            self.selected_baudrate = 9600

        self.test_result_label.setText("⏳ Probando conexión...")
        self.test_result_label.setStyleSheet("color: #3b82f6; font-weight: bold;")
        self.test_button.setEnabled(False)

        # Usar QTimer para no bloquear UI
        QTimer.singleShot(100, self._do_test_connection)

    def _do_test_connection(self):
        """Ejecutar test de conexión"""
        try:
            from src.core.yr9011_usb_scanner import YR9011USBScanner

            logger.info(f"🔍 Probando {self.selected_port} a {self.selected_baudrate} bps...")

            # Crear scanner temporal
            scanner = YR9011USBScanner(port=self.selected_port)

            # Intentar conectar
            if scanner.connect():
                version = scanner.get_firmware_version()
                scanner.disconnect()

                version_text = f"v{version}" if version else "desconocida"

                self.test_result_label.setText(
                    f"✅ Conexión exitosa!\n"
                    f"Firmware: {version_text}"
                )
                self.test_result_label.setStyleSheet("color: #10b981; font-weight: bold;")
                self.connect_button.setEnabled(True)

                logger.info(f"✅ Conexión exitosa - Firmware: {version_text}")
            else:
                self.test_result_label.setText(
                    "❌ No se pudo conectar\n"
                    "Prueba con otra velocidad o verifica el puerto"
                )
                self.test_result_label.setStyleSheet("color: #ef4444; font-weight: bold;")
                logger.warning("❌ Test de conexión falló")

        except Exception as e:
            self.test_result_label.setText(f"❌ Error: {str(e)}")
            self.test_result_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            logger.error(f"❌ Error en test: {e}")

        finally:
            self.test_button.setEnabled(True)

    def get_config(self):
        """Obtener configuración seleccionada"""
        return {
            'port': self.selected_port,
            'baudrate': self.selected_baudrate
        }
