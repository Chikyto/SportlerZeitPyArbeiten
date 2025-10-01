#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Página de detección de antenas físicas
src/gui/wizard/antenna_detection_page.py
"""

import logging
from PyQt6.QtWidgets import (
    QWizardPage, QVBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

logger = logging.getLogger(__name__)

class AntennaScanWorker(QThread):
    """Worker thread para escanear antenas sin bloquear UI"""
    progress = pyqtSignal(int, str)  # progreso, mensaje
    finished = pyqtSignal(dict)  # resultados
    
    def __init__(self, reader_manager):
        super().__init__()
        self.reader_manager = reader_manager
    
    def run(self):
        """Ejecuta el escaneo en thread separado"""
        try:
            self.progress.emit(5, "Iniciando escaneo...")
            results = {}
            
            for port in range(1, 9):
                self.progress.emit(
                    5 + (port * 90 // 8),
                    f"Escaneando puerto {port}/8..."
                )
                
                try:
                    is_connected, return_loss = \
                        self.reader_manager.antenna_detector.detect_physical_antenna(port)
                    results[port] = (is_connected, return_loss)
                except Exception as e:
                    logger.error(f"Error escaneando puerto {port}: {e}")
                    results[port] = (False, 0)
            
            self.progress.emit(100, "Escaneo completado")
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"Error en escaneo: {e}")
            self.finished.emit({})

class AntennaDetectionPage(QWizardPage):
    """Página de detección de antenas"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.detection_results = {}
        self.detection_completed = False
        
        self.setTitle("Detección de Antenas")
        self.setSubTitle("Detecta las antenas físicamente conectadas")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Descripción
        desc = QLabel(
            "Ahora detectaremos las antenas físicamente conectadas al lector.\n"
            "Este proceso usa medición de return loss para verificar cada puerto."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Botón de escaneo
        self.scan_button = QPushButton("Escanear Antenas")
        self.scan_button.clicked.connect(self.scan_antennas)
        layout.addWidget(self.scan_button)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        layout.addWidget(self.progress_label)
        
        # Resultados
        results_group = QGroupBox("Resultados del Escaneo")
        results_layout = QVBoxLayout()
        
        self.results_label = QLabel("")
        results_layout.addWidget(self.results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Puerto", "Estado", "Return Loss"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.results_table)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        self.setLayout(layout)
    
    def scan_antennas(self):
        """Inicia el escaneo de antenas"""
        wizard = self.wizard()
        if not wizard or not hasattr(wizard, 'reader_manager'):
            QMessageBox.warning(self, "Error", "Reader no disponible")
            return
        
        self.scan_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.detection_results = {}
        
        # Crear y ejecutar worker thread
        self.worker = AntennaScanWorker(wizard.reader_manager)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.scan_finished)
        self.worker.start()
    
    def update_progress(self, value, message):
        """Actualiza la barra de progreso"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
    
    def scan_finished(self, results):
        """Maneja la finalización del escaneo"""
        self.detection_results = results
        self.detection_completed = True
        self.scan_button.setEnabled(True)
        
        self.display_results()
        
        connected_count = sum(1 for conn, _ in results.values() if conn)
        
        if connected_count > 0:
            self.completeChanged.emit()
        else:
            QMessageBox.warning(
                self,
                "Sin antenas",
                "No se detectaron antenas conectadas.\n"
                "Verifica las conexiones físicas y vuelve a escanear."
            )
    
    def display_results(self):
        """Muestra los resultados en la tabla"""
        connected_count = sum(1 for conn, _ in self.detection_results.values() if conn)
        self.results_label.setText(f"Antenas detectadas: {connected_count}/8")
        
        self.results_table.setRowCount(8)
        
        for port in range(1, 9):
            if port in self.detection_results:
                connected, return_loss = self.detection_results[port]
                
                # Puerto
                self.results_table.setItem(port-1, 0, QTableWidgetItem(f"Puerto {port}"))
                
                # Estado
                status = "CONECTADA" if connected else "NO CONECTADA"
                status_item = QTableWidgetItem(status)
                if connected:
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                else:
                    status_item.setForeground(Qt.GlobalColor.gray)
                self.results_table.setItem(port-1, 1, status_item)
                
                # Return Loss
                self.results_table.setItem(port-1, 2, QTableWidgetItem(f"{return_loss} dB"))
    
    def isComplete(self):
        """Determina si la página está completa"""
        if not self.detection_completed:
            return False
        
        connected_count = sum(1 for conn, _ in self.detection_results.values() if conn)
        return connected_count > 0
    
    def validatePage(self):
        """Validación al avanzar"""
        if not self.detection_completed:
            QMessageBox.warning(
                self,
                "Escaneo requerido",
                "Debe escanear las antenas antes de continuar"
            )
            return False
        
        connected_count = sum(1 for conn, _ in self.detection_results.values() if conn)
        if connected_count == 0:
            QMessageBox.warning(
                self,
                "Sin antenas",
                "No se detectaron antenas conectadas"
            )
            return False
        
        return True