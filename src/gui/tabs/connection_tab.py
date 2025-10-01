"""
Pestaña de conexión con el lector RFID
"""
from PyQt6.QtWidgets import (QGroupBox, QHBoxLayout, QVBoxLayout, 
                            QLabel, QLineEdit, QSpinBox, QPushButton, QTextEdit)
from PyQt6.QtCore import pyqtSlot
from .base_tab import BaseTab


class ConnectionTab(BaseTab):
    """Pestaña de conexión RFID"""
    
    def __init__(self, scanner, parent=None):
        self.scanner = scanner
        self.edit_mode = False  # Inicializar ANTES de super().__init__
        super().__init__(parent)
        
    def setup_ui(self):
        """Configurar interfaz"""
        # Configuración básica
        config_group = QGroupBox("Configuración del Lector YR8900")
        config_layout = QHBoxLayout(config_group)
        
        config_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit("192.168.0.178")
        self.host_input.setReadOnly(True)  # Bloqueado inicialmente
        config_layout.addWidget(self.host_input)
        
        config_layout.addWidget(QLabel("Puerto:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(4001)
        self.port_input.setReadOnly(True)  # Bloqueado inicialmente
        config_layout.addWidget(self.port_input)
        
        # Botón de editar
        self.edit_config_btn = QPushButton("✏️ Editar")
        self.edit_config_btn.clicked.connect(self.toggle_edit_mode)
        self.edit_config_btn.setMaximumWidth(80)
        config_layout.addWidget(self.edit_config_btn)
        
        config_layout.addStretch()
        
        # Label de estado de configuración
        self.config_status_label = QLabel("⚙️ Configurado desde wizard")
        self.config_status_label.setStyleSheet("color: green; font-style: italic;")
        config_layout.addWidget(self.config_status_label)
        
        self.layout.addWidget(config_group)
        
        # Estado y botones
        status_group = QGroupBox("Estado de Conexión")
        status_layout = QVBoxLayout(status_group)
        
        self.connection_status = QLabel("Desconectado")
        self.connection_status.setStyleSheet("font-weight: bold; color: red;")
        status_layout.addWidget(self.connection_status)
        
        buttons_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.clicked.connect(self.connect_scanner)
        buttons_layout.addWidget(self.connect_btn)
        
        self.test_btn = QPushButton("Test")
        self.test_btn.clicked.connect(self.test_scanner)
        self.test_btn.setEnabled(False)
        buttons_layout.addWidget(self.test_btn)
        
        self.test_antennas_btn = QPushButton("Test Antenas")
        self.test_antennas_btn.clicked.connect(self.test_antennas)
        self.test_antennas_btn.setEnabled(False)
        buttons_layout.addWidget(self.test_antennas_btn)
        
        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.clicked.connect(self.disconnect_scanner)
        self.disconnect_btn.setEnabled(False)
        buttons_layout.addWidget(self.disconnect_btn)
        
        status_layout.addLayout(buttons_layout)
        self.layout.addWidget(status_group)
        
        # Log
        self.connection_log = QTextEdit()
        self.connection_log.setMaximumHeight(150)
        self.connection_log.setReadOnly(True)
        self.layout.addWidget(self.connection_log)
    
    def connect_signals(self):
        """Conectar señales"""
        self.signals.log_message.connect(self.on_log_message)
        self.signals.scanner_connected.connect(self.on_scanner_connected)
    
    @pyqtSlot()
    def connect_scanner(self):
        """Conectar al scanner"""
        host = self.host_input.text().strip()
        port = self.port_input.value()
        
        self.scanner.host = host
        self.scanner.port = port
        
        self.log("Intentando conectar...")
        if self.scanner.connect():
            self.signals.scanner_connected.emit(True)
            self.log("Conectado exitosamente")
        else:
            self.signals.scanner_connected.emit(False)
            self.log("Error de conexión", "error")
    
    @pyqtSlot(bool)
    def on_scanner_connected(self, connected):
        """Actualizar UI según estado de conexión"""
        if connected:
            self.connection_status.setText("Conectado")
            self.connection_status.setStyleSheet("font-weight: bold; color: green;")
            
            self.connect_btn.setEnabled(False)
            self.test_btn.setEnabled(True)
            self.test_antennas_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(True)
        else:
            self.connection_status.setText("Desconectado")
            self.connection_status.setStyleSheet("font-weight: bold; color: red;")
            
            self.connect_btn.setEnabled(True)
            self.test_btn.setEnabled(False)
            self.test_antennas_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
    
    @pyqtSlot()
    def disconnect_scanner(self):
        """Desconectar del scanner"""
        self.scanner.disconnect()
        self.signals.scanner_connected.emit(False)
        self.log("Desconectado")
    
    @pyqtSlot()
    def test_scanner(self):
        """Test básico del scanner"""
        self.log("Ejecutando test con comandos originales...")
        if hasattr(self.scanner, 'test_original_command'):
            success = self.scanner.test_original_command()
            if success:
                self.log("Test con comandos originales exitoso")
            else:
                self.log("Test con comandos originales falló", "warning")
        else:
            self.log("Método de test no disponible", "warning")
    
    @pyqtSlot()
    def test_antennas(self):
        """Test específico de antenas"""
        self.log("Ejecutando test de antenas individuales...")
        if hasattr(self.scanner, 'test_individual_antennas'):
            self.scanner.test_individual_antennas()
            self.log("Test de antenas completado - revisar consola")
        else:
            self.log("Método no disponible", "warning")
    
    @pyqtSlot()
    def toggle_edit_mode(self):
        """Alternar modo de edición"""
        self.edit_mode = not self.edit_mode
        
        if self.edit_mode:
            # Habilitar edición
            self.host_input.setReadOnly(False)
            self.port_input.setReadOnly(False)
            self.host_input.setStyleSheet("background-color: #fff9e6;")
            self.port_input.setStyleSheet("background-color: #fff9e6;")
            self.edit_config_btn.setText("💾 Guardar")
            self.config_status_label.setText("✏️ Editando configuración...")
            self.config_status_label.setStyleSheet("color: orange; font-style: italic;")
            self.log("Modo edición activado")
        else:
            # Deshabilitar edición
            self.host_input.setReadOnly(True)
            self.port_input.setReadOnly(True)
            self.host_input.setStyleSheet("")
            self.port_input.setStyleSheet("")
            self.edit_config_btn.setText("✏️ Editar")
            self.config_status_label.setText("⚙️ Configuración guardada")
            self.config_status_label.setStyleSheet("color: green; font-style: italic;")
            self.log("Configuración actualizada")
            
            # Si está conectado, desconectar para reconectar con nueva config
            if self.scanner.connected:
                self.disconnect_scanner()
                self.log("⚠️ Reconecte el scanner con la nueva configuración")
    
    @pyqtSlot(str, str)
    def on_log_message(self, message, level):
        """Agregar mensaje al log"""
        timestamp = self.get_timestamp()
        self.connection_log.append(f"[{timestamp}] {message}")