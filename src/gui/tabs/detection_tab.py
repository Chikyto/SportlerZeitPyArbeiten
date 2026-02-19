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
    QTableWidgetItem, QGroupBox, QMessageBox, QFrame
)
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
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
        self.tag_rows = {}        # {tag_id: row_index} - mapeo de tags a filas
        self.tag_data = {}        # {tag_id: {'start': bool, 'checkpoints': set, 'finish': bool, 'last_time': str, 'last_antenna': str}}

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
        
        # Tabla de detecciones (agrupada por participante)
        self.detections_table = QTableWidget()
        self.detections_table.setColumnCount(7)
        self.detections_table.setHorizontalHeaderLabels([
            "Tag", "Nombre", "Distancia", "Largada", "Checkpoints", "Meta", "Última Lectura"
        ])
        self.detections_table.setAlternatingRowColors(True)

        # Asegurar que las barras de desplazamiento estén siempre disponibles
        self.detections_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.detections_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Configurar ancho de columnas
        header = self.detections_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.layout.addWidget(self.detections_table)
        
        # Panel de última llegada a meta
        finish_frame = QFrame()
        finish_frame.setFrameShape(QFrame.Shape.StyledPanel)
        finish_frame.setStyleSheet("background-color: #1a1a2e; border: 2px solid #f0a500; border-radius: 6px; padding: 4px;")
        finish_layout = QHBoxLayout(finish_frame)
        finish_layout.setContentsMargins(8, 4, 8, 4)

        finish_title = QLabel("🏁 Última llegada:")
        finish_title.setStyleSheet("color: #f0a500; font-weight: bold; font-size: 13px; background: transparent; border: none;")
        finish_layout.addWidget(finish_title)

        self.last_finish_label = QLabel("—")
        self.last_finish_label.setStyleSheet("color: #ffffff; font-size: 13px; background: transparent; border: none;")
        finish_layout.addWidget(self.last_finish_label)
        finish_layout.addStretch()
        self.layout.addWidget(finish_frame)

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
        self.safe_connect('athlete_tag_resolved', self.on_athlete_tag_resolved)
        self.safe_connect('athlete_finished', self.on_athlete_finished)
    
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
    
    @pyqtSlot(str, str, str)
    def on_athlete_tag_resolved(self, tag_id: str, athlete_name: str, distance_name: str):
        """Actualizar nombre y distancia en la tabla cuando el race_manager resuelve el atleta"""
        if tag_id in self.tag_data:
            self.tag_data[tag_id]['name'] = athlete_name
            self.tag_data[tag_id]['distance'] = distance_name

        if tag_id in self.tag_rows:
            row = self.tag_rows[tag_id]
            self.detections_table.setItem(row, 1, QTableWidgetItem(athlete_name))
            self.detections_table.setItem(row, 2, QTableWidgetItem(distance_name))

    @pyqtSlot(str, str, str)
    def on_athlete_finished(self, athlete_name: str, distance_name: str, formatted_time: str):
        """Actualizar panel de última llegada cuando un atleta cruza la meta"""
        text = f"{athlete_name}  |  {distance_name}  |  {formatted_time}"
        self.last_finish_label.setText(text)
        self.last_finish_label.setStyleSheet(
            "color: #00ff88; font-size: 13px; font-weight: bold; background: transparent; border: none;"
        )

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
            logger.info("⚠️  Ya se está escaneando, ignorando solicitud duplicada")
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

    def auto_start_scanning(self):
        """
        🔥 Método público para iniciar escaneo automáticamente desde señales

        Este método es llamado cuando se inicia una distancia desde EventConfigWidget.
        Inicia el escaneo sin mostrar mensajes de error si el scanner no está listo.
        """
        logger.info("🚀 DetectionTab.auto_start_scanning() llamado")

        if not self.scanner:
            logger.warning("⚠️  Scanner no disponible, no se puede auto-iniciar escaneo")
            self.log("⚠️ Scanner no disponible para auto-inicio de escaneo")
            return False

        if self.is_scanning:
            logger.info("✅ Ya se está escaneando, no es necesario iniciar de nuevo")
            return True

        if not self.antenna_roles:
            logger.warning("⚠️  No hay antenas configuradas, no se puede auto-iniciar escaneo")
            self.log("⚠️ No hay antenas configuradas para escaneo")
            return False

        logger.info("🟢 Iniciando escaneo automáticamente...")
        self.start_scanning()
        return True
    
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
        # 🔍 DEBUG: Mostrar info del tag detectado
        tag_id = tag_info.get('number', 'Unknown')
        antenna_port = tag_info.get('antenna', 'Unknown')
        logger.info("=" * 80)
        logger.info(f"🔔 CHIP DETECTADO: {tag_id} en puerto {antenna_port}")
        logger.info(f"   Puertos configurados: {list(self.antenna_roles.keys())}")
        logger.info("=" * 80)

        # Delegar procesamiento al TagProcessor
        processed = self.tag_processor.process_tag(tag_info)

        if not processed:
            logger.error("=" * 80)
            logger.error(f"❌ TAG RECHAZADO: {tag_id} en puerto {antenna_port}")
            logger.error(f"   Razón: Puerto no configurado o sin roles")
            logger.error(f"   Puertos configurados: {list(self.antenna_roles.keys())}")
            logger.error("=" * 80)
            return

        logger.info(f"✅ TAG PROCESADO: {processed['tag_id']} - Roles: {processed['roles']}")

        # Agregar tag a conjunto de únicos
        self.detected_tags.add(processed['tag_id'])

        # Agregar a la tabla
        self.add_detection_to_table(processed)

        # Actualizar estadísticas
        self.update_statistics()

        # 🏁 EMITIR SEÑAL PARA RACE MANAGER
        # Enviar información completa de la detección para procesamiento de carrera
        if self.signals:
            logger.info(f"📡 EMITIENDO SEÑAL tag_detected para RaceManager: {processed['tag_id']}")
            self.signals.tag_detected.emit(processed)
        else:
            logger.warning("⚠️  No hay objeto signals, no se puede emitir señal para RaceManager")
    
    def add_detection_to_table(self, processed: dict):
        """
        Agregar o actualizar detección en la tabla (vista agrupada por participante)

        Args:
            processed: Dict con información procesada del tag
        """
        tag_id = processed['tag_id']

        # Inicializar datos del tag si es la primera vez que lo vemos
        if tag_id not in self.tag_data:
            self.tag_data[tag_id] = {
                'start': False,
                'checkpoints': set(),
                'finish': False,
                'last_time': '',
                'last_antenna': '',
                'name': 'N/A',
                'distance': 'N/A'
            }

        # Actualizar datos según el rol detectado
        roles = processed['roles']
        if 'start' in roles:
            self.tag_data[tag_id]['start'] = True
        if 'checkpoint' in roles:
            # Determinar número de checkpoint basado en el nombre de antena
            antenna_name = self.antenna_names.get(processed['port'], processed['antenna_name'])
            self.tag_data[tag_id]['checkpoints'].add(antenna_name)
        if 'finish' in roles:
            self.tag_data[tag_id]['finish'] = True

        # Actualizar última lectura
        self.tag_data[tag_id]['last_time'] = processed['timestamp']
        antenna_name = self.antenna_names.get(processed['port'], processed['antenna_name'])
        self.tag_data[tag_id]['last_antenna'] = antenna_name

        # Buscar nombre y distancia del participante desde race_manager
        # (esto se puede mejorar conectando con signals, pero por ahora usamos valores por defecto)

        # Si el tag ya tiene una fila, actualizarla; si no, crear una nueva
        if tag_id in self.tag_rows:
            row = self.tag_rows[tag_id]
        else:
            row = self.detections_table.rowCount()
            self.detections_table.insertRow(row)
            self.tag_rows[tag_id] = row

        data = self.tag_data[tag_id]

        # Columna 0: Tag ID
        self.detections_table.setItem(row, 0, QTableWidgetItem(tag_id))

        # Columna 1: Nombre (placeholder por ahora)
        self.detections_table.setItem(row, 1, QTableWidgetItem(data['name']))

        # Columna 2: Distancia (placeholder por ahora)
        self.detections_table.setItem(row, 2, QTableWidgetItem(data['distance']))

        # Columna 3: Largada
        start_icon = "✓" if data['start'] else "-"
        start_item = QTableWidgetItem(start_icon)
        if data['start']:
            start_item.setForeground(QColor(0, 150, 0))  # Verde
        self.detections_table.setItem(row, 3, start_item)

        # Columna 4: Checkpoints
        if data['checkpoints']:
            checkpoints_text = ", ".join(sorted(data['checkpoints']))
            cp_item = QTableWidgetItem(f"✓ {checkpoints_text}")
            cp_item.setForeground(QColor(0, 100, 200))  # Azul
        else:
            cp_item = QTableWidgetItem("-")
        self.detections_table.setItem(row, 4, cp_item)

        # Columna 5: Meta
        finish_icon = "✓" if data['finish'] else "-"
        finish_item = QTableWidgetItem(finish_icon)
        if data['finish']:
            finish_item.setForeground(QColor(200, 150, 0))  # Dorado
        self.detections_table.setItem(row, 5, finish_item)

        # Columna 6: Última Lectura
        last_reading = f"{data['last_time']} ({data['last_antenna']})"
        self.detections_table.setItem(row, 6, QTableWidgetItem(last_reading))

        # Resaltar la fila completa con el color del último evento
        if processed['color_code'] != 'none':
            rgb = self.tag_processor.get_color_rgb(processed['color_code'])
            color = QColor(*rgb)
            color.setAlpha(100)  # Hacer el color más transparente

            for col in range(7):
                if self.detections_table.item(row, col):
                    self.detections_table.item(row, col).setBackground(color)

        # Scroll para asegurar que la fila actualizada sea visible
        self.detections_table.scrollToItem(self.detections_table.item(row, 0))
    
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
            self.tag_rows.clear()
            self.tag_data.clear()
            self.update_statistics()
            self.log("🗑️ Detecciones limpiadas")
    
    def closeEvent(self, event):
        """Al cerrar, detener scanning"""
        if self.is_scanning:
            self.stop_scanning()
        event.accept()