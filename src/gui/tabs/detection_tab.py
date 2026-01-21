#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DetectionTab refactorizado - Solo UI y coordinación
src/gui/tabs/detection_tab.py

Responsabilidad única: UI y coordinación entre componentes
Delegación: ScanThread para scanning, TagProcessor para lógica
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox, QMessageBox
)
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QColor
import logging

from .base_tab import BaseTab
from ..components.scan_thread import ScanThread  # 🔥 Desde components/
from src.core.tag_processor import TagProcessor   # 🔥 Desde core/

logger = logging.getLogger(__name__)


class DetectionTab(BaseTab):
    """
    Tab de detección de chips RFID
    
    Responsabilidades:
    - Crear y gestionar UI
    - Coordinar ScanThread y TagProcessor
    - Mostrar detecciones en tabla
    - Actualizar estadísticas
    """
    
    def __init__(self, signals=None, parent=None):
        self.scanner = None
        self.scan_thread = None
        self.tag_processor = None
        self.is_scanning = False
        self.antenna_roles = {}   # {port: [roles]}
        self.antenna_names = {}   # {port: name}
        self.detected_tags = set()
        
        super().__init__(signals=signals, parent=parent)
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        
        # Título
        title = QLabel("🔍 Detección de Chips RFID")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.layout.addWidget(title)
        
        # Información de antenas configuradas
        self.antenna_info_group = QGroupBox("Antenas Configuradas")
        self.antenna_info_layout = QVBoxLayout()
        self.antenna_info_group.setLayout(self.antenna_info_layout)
        self.layout.addWidget(self.antenna_info_group)
        
        # Controles de scan
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🟢 Iniciar Detección")
        self.start_btn.clicked.connect(self.start_scanning)
        self.start_btn.setEnabled(False)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("🔴 Detener")
        self.stop_btn.clicked.connect(self.stop_scanning)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("🗑️ Limpiar")
        self.clear_btn.clicked.connect(self.clear_detections)
        controls_layout.addWidget(self.clear_btn)
        
        self.layout.addLayout(controls_layout)
        
        # Tabla de detecciones
        self.detections_table = QTableWidget()
        self.detections_table.setColumnCount(5)
        self.detections_table.setHorizontalHeaderLabels([
            "Hora", "Tag", "Puerto", "Rol", "Antena"
        ])
        self.detections_table.setAlternatingRowColors(True)
        self.layout.addWidget(self.detections_table)
        
        # Estadísticas
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("Detecciones: 0 | Tags únicos: 0")
        self.stats_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        self.layout.addLayout(stats_layout)
    
    def connect_signals(self):
        """Conectar señales del sistema"""
        self.safe_connect('scanner_ready', self.on_scanner_ready)
        self.safe_connect('connection_status_changed', self.on_connection_status)
    
    @pyqtSlot(bool, str)
    def on_connection_status(self, connected, message):
        """Actualizar UI según estado de conexión"""
        if connected:
            self.log(f"✓ {message}")
        else:
            self.log(f"✗ {message}")
            self.start_btn.setEnabled(False)
            if self.is_scanning:
                self.stop_scanning()
    
    @pyqtSlot(object)
    def on_scanner_ready(self, scanner):
        """Callback cuando el scanner está listo"""
        self.scanner = scanner
        self.update_antenna_info()
        self.start_btn.setEnabled(True)
        self.log("✓ Scanner listo para detección")
    
    def update_antenna_roles_from_config(self, antennas_config):
        """
        🔥 MÉTODO CRÍTICO: Actualizar roles desde configuración
        
        Args:
            antennas_config: dict {port(int): {'name', 'start', 'finish', 'checkpoint', ...}}
        """
        logger.info("=" * 80)
        logger.info("📡 DetectionTab: Actualizando roles desde config")
        logger.info("=" * 80)
        
        # Limpiar datos anteriores
        self.antenna_roles.clear()
        self.antenna_names.clear()
        
        # Procesar cada antena
        for port, config in antennas_config.items():
            port_int = int(port) if isinstance(port, str) else port
            
            if not config.get('enabled', False):
                continue
            
            # Extraer TODOS los roles
            roles = []
            if config.get('start', False):
                roles.append('start')
            if config.get('finish', False):
                roles.append('finish')
            if config.get('checkpoint', False):
                roles.append('checkpoint')
            
            self.antenna_roles[port_int] = roles
            self.antenna_names[port_int] = config.get('name', f'Antena {port_int}')
            
            logger.info(f"✅ Puerto {port_int}: {self.antenna_names[port_int]} → {roles}")
        
        logger.info(f"📊 Total: {len(self.antenna_roles)} antenas configuradas")
        logger.info("=" * 80)
        
        # Actualizar UI
        self.update_antenna_list_ui()
        
        # Actualizar procesador de tags si existe
        if self.tag_processor:
            self.tag_processor.update_antenna_roles(self.antenna_roles)
    
    def update_antenna_list_ui(self):
        """Actualizar lista visual de antenas configuradas"""
        # Limpiar layout anterior
        while self.antenna_info_layout.count():
            child = self.antenna_info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.antenna_roles:
            no_antennas = QLabel("⚠️ No hay antenas configuradas")
            no_antennas.setStyleSheet("color: orange;")
            self.antenna_info_layout.addWidget(no_antennas)
            return
        
        # Crear procesador temporal para formatear texto
        temp_processor = TagProcessor(self.antenna_roles, self.signals)
        
        # Crear widgets para cada antena
        for port in sorted(self.antenna_roles.keys()):
            roles = self.antenna_roles[port]
            name = self.antenna_names.get(port, f'Antena {port}')
            role_text = temp_processor.format_role_text(roles)
            
            info = QLabel(f"Puerto {port}: {name} ({role_text})")
            self.antenna_info_layout.addWidget(info)
    
    def update_antenna_info(self):
        """Método legacy para compatibilidad"""
        if self.antenna_roles:
            self.update_antenna_list_ui()
    
    def start_scanning(self):
        """Iniciar detección continua"""
        if not self.scanner:
            self.log("ERROR: Scanner no disponible")
            QMessageBox.warning(self, "Error", "Scanner no disponible")
            return
        
        if self.is_scanning:
            return
        
        # Crear procesador de tags
        self.tag_processor = TagProcessor(self.antenna_roles, self.signals)
        
        # Crear y arrancar thread de scanning
        self.scan_thread = ScanThread(self.scanner)
        self.scan_thread.tag_detected.connect(self.on_tag_detected)
        self.scan_thread.error_occurred.connect(self.on_scan_error)
        self.scan_thread.start()
        
        self.is_scanning = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        self.log("🟢 Detección iniciada - Escaneando antenas...")
    
    def stop_scanning(self):
        """Detener detección"""
        if self.scan_thread:
            self.scan_thread.stop()
            self.scan_thread.wait(2000)  # Esperar max 2 segundos
            self.scan_thread = None
        
        self.is_scanning = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.log("🔴 Detección detenida")
    
    @pyqtSlot(str)
    def on_scan_error(self, error_msg):
        """Manejar errores del scan"""
        self.log(f"❌ Error: {error_msg}")
    
    @pyqtSlot(dict)
    def on_tag_detected(self, tag_info):
        """Procesar tag detectado"""
        # Delegar procesamiento al TagProcessor
        processed = self.tag_processor.process_tag(tag_info)

        if not processed:
            return

        # Agregar tag a conjunto de únicos
        self.detected_tags.add(processed['tag_id'])

        # Agregar a la tabla
        self.add_detection_to_table(processed)

        # Actualizar estadísticas
        self.update_statistics()

        # 🏁 EMITIR SEÑAL PARA RACE MANAGER
        # Enviar información completa de la detección para procesamiento de carrera
        if self.signals:
            self.signals.tag_detected.emit(processed)
    
    def add_detection_to_table(self, processed: dict):
        """
        Agregar detección a la tabla
        
        Args:
            processed: Dict con información procesada del tag
        """
        row = self.detections_table.rowCount()
        self.detections_table.insertRow(row)
        
        # Agregar datos
        self.detections_table.setItem(row, 0, QTableWidgetItem(processed['timestamp']))
        self.detections_table.setItem(row, 1, QTableWidgetItem(processed['tag_id']))
        self.detections_table.setItem(row, 2, QTableWidgetItem(str(processed['port'])))
        
        # Formatear texto de roles
        role_text = self.tag_processor.format_role_text(processed['roles'])
        self.detections_table.setItem(row, 3, QTableWidgetItem(role_text))
        
        # Usar nombre de antena si está disponible
        antenna_name = self.antenna_names.get(processed['port'], processed['antenna_name'])
        self.detections_table.setItem(row, 4, QTableWidgetItem(antenna_name))
        
        # Aplicar color si existe
        if processed['color_code'] != 'none':
            rgb = self.tag_processor.get_color_rgb(processed['color_code'])
            color = QColor(*rgb)
            
            for col in range(5):
                self.detections_table.item(row, col).setBackground(color)
        
        # Scroll al final
        self.detections_table.scrollToBottom()
    
    def update_statistics(self):
        """Actualizar estadísticas de detecciones"""
        total_detections = self.detections_table.rowCount()
        unique_tags = len(self.detected_tags)
        self.stats_label.setText(
            f"Detecciones: {total_detections} | Tags únicos: {unique_tags}"
        )
    
    def clear_detections(self):
        """Limpiar la tabla de detecciones"""
        reply = QMessageBox.question(
            self,
            "Limpiar Detecciones",
            "¿Estás seguro de limpiar todas las detecciones?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.detections_table.setRowCount(0)
            self.detected_tags.clear()
            self.update_statistics()
            self.log("🗑️ Detecciones limpiadas")
    
    def closeEvent(self, event):
        """Al cerrar, detener scanning"""
        if self.is_scanning:
            self.stop_scanning()
        event.accept()