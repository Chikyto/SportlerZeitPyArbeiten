import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QLabel, QTextEdit)
from PyQt6.QtCore import Qt

from ..core.simple_scanner import SimpleScanner

class SimpleGUI(QMainWindow):
    """GUI mínima para probar el scanner"""
    
    def __init__(self):
        super().__init__()
        self.scanner = SimpleScanner()
        self.setup_ui()
        
    def setup_ui(self):
        """Crear interfaz básica"""
        self.setWindowTitle("RFID Scanner Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Status
        self.status_label = QLabel("Desconectado")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        layout.addWidget(self.status_label)
        
        # Botones
        self.connect_btn = QPushButton("Conectar")
        self.connect_btn.clicked.connect(self.connect_scanner)
        layout.addWidget(self.connect_btn)
        
        self.test_btn = QPushButton("Test Básico")
        self.test_btn.clicked.connect(self.test_scanner)
        self.test_btn.setEnabled(False)
        layout.addWidget(self.test_btn)
        
        self.scan_btn = QPushButton("Scan Simple")
        self.scan_btn.clicked.connect(self.scan_simple)
        self.scan_btn.setEnabled(False)
        layout.addWidget(self.scan_btn)
        
        self.scan_tags_btn = QPushButton("Scan con Tags")
        self.scan_tags_btn.clicked.connect(self.scan_with_tags)
        self.scan_tags_btn.setEnabled(False)
        layout.addWidget(self.scan_tags_btn)

        self.scan_continuous_btn = QPushButton("Scan Continuo (5s)")
        self.scan_continuous_btn.clicked.connect(self.scan_continuous)
        self.scan_continuous_btn.setEnabled(False)
        layout.addWidget(self.scan_continuous_btn)

        self.disconnect_btn = QPushButton("Desconectar")
        self.disconnect_btn.clicked.connect(self.disconnect_scanner)
        self.disconnect_btn.setEnabled(False)
        layout.addWidget(self.disconnect_btn)
        
        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)
        
    def log_message(self, message):
        """Agregar mensaje al log"""
        self.log.append(message)
        
    def connect_scanner(self):
        """Conectar al scanner"""
        self.log_message("Intentando conectar...")
        if self.scanner.connect():
            self.status_label.setText("Conectado")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
            self.connect_btn.setEnabled(False)
            self.test_btn.setEnabled(True)
            self.scan_btn.setEnabled(True)
            self.scan_continuous_btn.setEnabled(True)   
            self.scan_tags_btn.setEnabled(False)
            self.scan_tags_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(True)
            self.log_message("✓ Conectado exitosamente")
        else:
            self.log_message("✗ Error de conexión")
            
    def disconnect_scanner(self):
        """Desconectar del scanner"""
        self.scanner.disconnect()
        self.status_label.setText("Desconectado")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: red;")
        self.connect_btn.setEnabled(True)
        self.test_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(False)
        self.log_message("Desconectado")
        
    def test_scanner(self):
        """Test básico del scanner"""
        self.log_message("Ejecutando test básico...")
        if self.scanner.test_basic_command():
            self.log_message("✓ Test básico exitoso")
        else:
            self.log_message("✗ Test básico falló")
            
    def scan_simple(self):
        """Scan simple"""
        self.log_message("Ejecutando scan...")
        response = self.scanner.scan_single()
        if response:
            self.log_message(f"✓ Scan exitoso - {len(response)} bytes recibidos")
        else:
            self.log_message("✗ Sin respuesta de scan")

    def scan_with_tags(self):
        """Scan que muestra los tags detectados"""
        self.log_message("Ejecutando scan con parsing...")
        tags = self.scanner.scan_with_parsing()
        
        if tags:
            self.log_message(f"✓ {len(tags)} tag(s) detectado(s):")
            for tag in tags:
                timestamp = tag['timestamp'].strftime('%H:%M:%S')
                self.log_message(f"  • Chip {tag['number']} (Antena {tag['antenna']}) - {timestamp}")
                self.log_message(f"    EPC: {tag['epc_hex']}")
        else:
            self.log_message("- Sin tags detectados en este scan")

    def scan_continuous(self):
        """Scan continuo para capturar todos los chips"""
        self.log_message("Iniciando scan continuo de 5 segundos...")
        tags = self.scanner.continuous_scan_simple(5)
        
        self.log_message(f"✓ Scan completo - {len(tags)} chips únicos detectados:")
        for tag in tags:
            timestamp = tag['timestamp'].strftime('%H:%M:%S')
            self.log_message(f"  • Chip {tag['number']} (Antena {tag['antenna']}) - {timestamp}")