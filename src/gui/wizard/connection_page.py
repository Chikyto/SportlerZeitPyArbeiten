#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Página de conexión con el lector YR8900
src/gui/wizard/connection_page.py
"""

import logging
from PyQt6.QtWidgets import (
    QWizardPage, QVBoxLayout, QLabel, QPushButton,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class ConnectionPage(QWizardPage):
    """Página de conexión con el lector"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.connection_tested = False
        
        self.setTitle("Conexión con YR8900")
        self.setSubTitle("Verifica la conexión con el lector RFID")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Descripción
        desc = QLabel(
            "Primero verificaremos la conexión con el lector RFID YR8900."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Grupo de configuración
        config_group = QGroupBox("Configuración de Conexión")
        config_layout = QVBoxLayout()
        
        wizard = self.wizard()
        if wizard and hasattr(wizard, 'reader_manager'):
            config = wizard.reader_manager.config
            config_layout.addWidget(QLabel(f"Dirección IP: {config.host}"))
            config_layout.addWidget(QLabel(f"Puerto: {config.port}"))
            config_layout.addWidget(QLabel(f"Reader Address: 0x{config.reader_address:02X}"))
            config_layout.addWidget(QLabel(f"Timeout: {config.timeout}s"))
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Botón de prueba
        self.test_button = QPushButton("Probar Conexión")
        self.test_button.clicked.connect(self.test_connection)
        layout.addWidget(self.test_button)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.status_label.setFont(font)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def test_connection(self):
        """Prueba la conexión con el lector"""
        self.status_label.setText("Probando conexión...")
        self.status_label.setStyleSheet("color: blue;")
        
        wizard = self.wizard()
        if not wizard or not hasattr(wizard, 'reader_manager'):
            self.status_label.setText("✗ Error: Reader no disponible")
            self.status_label.setStyleSheet("color: red;")
            return
        
        try:
            if wizard.reader_manager.test_connection():
                fw = wizard.reader_manager.firmware_version
                self.status_label.setText(f"✓ Conexión exitosa - Firmware v{fw}")
                self.status_label.setStyleSheet("color: green;")
                self.connection_tested = True
                self.completeChanged.emit()
            else:
                self.status_label.setText("✗ Error de conexión")
                self.status_label.setStyleSheet("color: red;")
                self.connection_tested = False
        
        except Exception as e:
            logger.error(f"Error en conexión: {e}")
            self.status_label.setText(f"✗ Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            self.connection_tested = False
    
    def isComplete(self):
        """Determina si la página está completa"""
        return self.connection_tested
    
    def validatePage(self):
        """Validación al avanzar"""
        if not self.connection_tested:
            QMessageBox.warning(
                self,
                "Conexión requerida",
                "Debe probar la conexión antes de continuar"
            )
            return False
        return True