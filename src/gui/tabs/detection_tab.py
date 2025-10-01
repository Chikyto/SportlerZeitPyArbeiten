"""
Pestaña de detección de chips RFID
"""
from PyQt6.QtWidgets import (QGroupBox, QHBoxLayout, QVBoxLayout, 
                            QLabel, QPushButton, QTableWidget, 
                            QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import pyqtSlot
from .base_tab import BaseTab


class DetectionTab(BaseTab):
    """Pestaña de detección de chips"""
    
    def __init__(self, scanner, parent=None):
        self.scanner = scanner
        self.detected_tags = {}
        super().__init__(parent)
        
    def setup_ui(self):
        """Configurar interfaz"""
        # Controles de scanning
        scan_group = QGroupBox("Control de Scanning")
        scan_layout = QHBoxLayout(scan_group)
        
        self.scan_single_btn = QPushButton("Scan Simple")
        self.scan_single_btn.clicked.connect(self.scan_single)
        self.scan_single_btn.setEnabled(False)
        scan_layout.addWidget(self.scan_single_btn)
        
        self.scan_continuous_btn = QPushButton("Scan Continuo (5s)")
        self.scan_continuous_btn.clicked.connect(self.scan_continuous)
        self.scan_continuous_btn.setEnabled(False)
        scan_layout.addWidget(self.scan_continuous_btn)
        
        self.clear_tags_btn = QPushButton("Limpiar Lista")
        self.clear_tags_btn.clicked.connect(self.clear_tags)
        scan_layout.addWidget(self.clear_tags_btn)
        
        scan_layout.addStretch()
        
        # Contador
        self.tag_counter = QLabel("Chips detectados: 0")
        self.tag_counter.setStyleSheet("font-weight: bold;")
        scan_layout.addWidget(self.tag_counter)
        
        self.layout.addWidget(scan_group)
        
        # Tabla de chips detectados
        table_group = QGroupBox("Chips Detectados")
        table_layout = QVBoxLayout(table_group)
        
        self.tags_table = QTableWidget()
        self.tags_table.setColumnCount(4)
        self.tags_table.setHorizontalHeaderLabels(["Chip", "Antena", "Hora", "EPC"])
        
        # Configurar tabla
        header = self.tags_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tags_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.tags_table)
        
        self.layout.addWidget(table_group)
    
    def connect_signals(self):
        """Conectar señales"""
        self.signals.scanner_connected.connect(self.on_scanner_connected)
        self.signals.tag_detected.connect(self.on_tag_detected)
        self.signals.tags_cleared.connect(self.on_tags_cleared)
    
    @pyqtSlot(bool)
    def on_scanner_connected(self, connected):
        """Actualizar botones según conexión"""
        self.scan_single_btn.setEnabled(connected)
        self.scan_continuous_btn.setEnabled(connected)
    
    @pyqtSlot()
    def scan_single(self):
        """Scan simple"""
        tags = self.scanner.scan_with_parsing()
        if tags:
            for tag in tags:
                self.signals.tag_detected.emit(tag)
            self.log(f"Scan simple: {len(tags)} chip(s) detectado(s)")
        else:
            self.log("Scan simple: sin chips detectados")
    
    @pyqtSlot()
    def scan_continuous(self):
        """Scan continuo multi-antena"""
        self.log("Iniciando scan continuo multi-antena...")
        tags = self.scanner.continuous_scan_multi_antenna(5)
        
        for tag in tags:
            self.signals.tag_detected.emit(tag)
        
        self.log(f"Scan completado: {len(tags)} chips únicos")
    
    @pyqtSlot(dict)
    def on_tag_detected(self, tag):
        """Agregar tag detectado a la tabla"""
        tag_number = tag['number']
        
        # Evitar duplicados en la tabla de detección
        if tag_number in self.detected_tags:
            return
        
        self.detected_tags[tag_number] = tag
        
        row = self.tags_table.rowCount()
        self.tags_table.insertRow(row)
        
        self.tags_table.setItem(row, 0, QTableWidgetItem(tag_number))
        self.tags_table.setItem(row, 1, QTableWidgetItem(str(tag['antenna'])))
        self.tags_table.setItem(row, 2, QTableWidgetItem(tag['timestamp'].strftime('%H:%M:%S')))
        self.tags_table.setItem(row, 3, QTableWidgetItem(tag['epc_hex'][:16] + "..."))
        
        self.update_counter()
    
    @pyqtSlot()
    def clear_tags(self):
        """Limpiar lista de tags"""
        self.detected_tags.clear()
        self.tags_table.setRowCount(0)
        self.update_counter()
        self.signals.tags_cleared.emit()
        self.log("Lista de chips limpiada")
    
    @pyqtSlot()
    def on_tags_cleared(self):
        """Responder a señal de tags cleared"""
        self.update_counter()
    
    def update_counter(self):
        """Actualizar contador de tags"""
        count = len(self.detected_tags)
        self.tag_counter.setText(f"Chips detectados: {count}")