"""
DetectionTab refactorizado con soporte para roles de antenas - VERSIÓN CORREGIDA
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QColor
from datetime import datetime
import time
import logging

from .base_tab import BaseTab

logger = logging.getLogger(__name__)

class ScanThread(QThread):
    """Thread para scanning continuo sin bloquear UI"""
    tag_detected = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, scanner):
        super().__init__()
        self.scanner = scanner
        self.running = False
    
    def run(self):
        """Loop de scanning"""
        self.running = True
        scan_count = 0
        
        logger.info("ScanThread iniciado")
        
        while self.running:
            try:
                if not self.scanner.available_antennas:
                    time.sleep(1)
                    continue
                
                antenna_id = self.scanner.available_antennas[
                    scan_count % len(self.scanner.available_antennas)
                ]
                
                tags = self.scanner.scan_single_antenna(antenna_id)
                
                for tag in tags:
                    self.tag_detected.emit(tag)
                
                scan_count += 1
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error en scan: {e}")
                self.error_occurred.emit(str(e))
                time.sleep(1)
        
        logger.info("ScanThread detenido")
    
    def stop(self):
        """Detiene el thread"""
        self.running = False


class DetectionTab(BaseTab):
    """Tab de detección de chips con soporte multi-antena"""
    
    def __init__(self, signals=None, parent=None):
        self.scanner = None
        self.scan_thread = None
        self.is_scanning = False
        self.antenna_roles = {}  # 🔥 {port(int): [roles]}
        self.antenna_names = {}  # {port(int): name}
        self.detected_tags = set()
        
        super().__init__(signals=signals, parent=parent)
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        
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
        """Conecta señales del sistema"""
        self.safe_connect('scanner_ready', self.on_scanner_ready)
        self.safe_connect('connection_status_changed', self.on_connection_status)
    
    def on_connection_status(self, connected, message):
        """Actualiza UI según estado de conexión"""
        if connected:
            self.log(f"✓ {message}")
        else:
            self.log(f"✗ {message}")
            self.start_btn.setEnabled(False)
            if self.is_scanning:
                self.stop_scanning()
    
    def on_scanner_ready(self, scanner):
        """Callback cuando el scanner está listo"""
        self.scanner = scanner
        self.update_antenna_info()
        self.start_btn.setEnabled(True)
        self.log("✓ Scanner listo para detección")
    
    # 🔥 NUEVO MÉTODO: Actualizar roles desde MainWindow
    def update_antenna_roles_from_config(self, antennas_config):
        """
        🔥 MÉTODO CRÍTICO: Actualizar roles desde configuración del wizard
        
        Args:
            antennas_config: dict {port(int): {'name', 'start', 'finish', 'checkpoint', ...}}
        """
        logger.info("=" * 80)
        logger.info("📡 DetectionTab.update_antenna_roles_from_config() LLAMADO")
        logger.info("=" * 80)
        
        # Debug: Ver qué llegó
        logger.info(f"📥 Recibido antennas_config:")
        logger.info(f"   Keys: {list(antennas_config.keys())}")
        logger.info(f"   Tipos: {[type(k).__name__ for k in antennas_config.keys()]}")
        
        # Limpiar datos anteriores
        self.antenna_roles.clear()
        self.antenna_names.clear()
        
        # Procesar cada antena
        for port, config in antennas_config.items():
            # 🔥 Asegurar que port es int
            port_int = int(port) if isinstance(port, str) else port
            
            if not config.get('enabled', False):
                logger.info(f"⏭️  Puerto {port_int}: deshabilitado, omitiendo")
                continue
            
            # Extraer TODOS los roles (puede tener múltiples)
            roles = []
            if config.get('start', False):
                roles.append('start')
            if config.get('finish', False):
                roles.append('finish')
            if config.get('checkpoint', False):
                roles.append('checkpoint')
            
            # Guardar información
            self.antenna_roles[port_int] = roles
            self.antenna_names[port_int] = config.get('name', f'Antena {port_int}')
            
            logger.info(f"✅ Puerto {port_int}:")
            logger.info(f"      Nombre: {self.antenna_names[port_int]}")
            logger.info(f"      Roles: {roles}")
        
        logger.info(f"📊 Total antenas configuradas: {len(self.antenna_roles)}")
        logger.info(f"📊 Puertos activos: {sorted(self.antenna_roles.keys())}")
        logger.info("=" * 80)
        
        # Actualizar UI
        self.update_antenna_list_ui()
    
    def update_antenna_list_ui(self):
        """Actualizar lista visual de antenas configuradas"""
        logger.info("🎨 Actualizando UI de lista de antenas...")
        
        # Limpiar layout anterior
        while self.antenna_info_layout.count():
            child = self.antenna_info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.antenna_roles:
            no_antennas = QLabel("⚠️ No hay antenas configuradas")
            no_antennas.setStyleSheet("color: orange;")
            self.antenna_info_layout.addWidget(no_antennas)
            logger.warning("⚠️  No hay antenas configuradas para mostrar")
            return
        
        # Crear widgets para cada antena
        for port in sorted(self.antenna_roles.keys()):
            roles = self.antenna_roles[port]
            name = self.antenna_names.get(port, f'Antena {port}')
            
            # Construir texto de roles
            if not roles:
                role_text = "⚪ Sin rol"
            else:
                role_parts = []
                if 'start' in roles:
                    role_parts.append('🟢 Largada')
                if 'finish' in roles:
                    role_parts.append('🏁 Meta')
                if 'checkpoint' in roles:
                    role_parts.append('🔵 Checkpoint')
                role_text = ' + '.join(role_parts)
            
            # Crear label
            info = QLabel(f"Puerto {port}: {name} ({role_text})")
            self.antenna_info_layout.addWidget(info)
            
            logger.info(f"✅ Widget creado: Puerto {port} - {name} - {role_text}")
        
        logger.info("✅ UI de antenas actualizada")
    
    def update_antenna_info(self):
        """
        MÉTODO LEGACY: Actualiza información de antenas desde scanner
        Mantener por compatibilidad, pero preferir update_antenna_roles_from_config()
        """
        if not self.scanner:
            return
        
        # Si ya tenemos roles configurados, solo actualizar UI
        if self.antenna_roles:
            self.update_antenna_list_ui()
            return
        
        # Si no, intentar obtener desde MainWindow (modo legacy)
        main_window = self.get_main_window()
        if not main_window:
            logger.warning("No se puede acceder a MainWindow")
            return
        
        if not self.scanner.available_antennas:
            self.update_antenna_list_ui()  # Mostrará "no hay antenas"
            return
        
        # Obtener roles desde MainWindow
        self.antenna_roles.clear()
        self.antenna_names.clear()
        
        for port in sorted(self.scanner.available_antennas):
            roles = main_window.get_antenna_roles(port)
            name = main_window.get_antenna_name(port)
            
            self.antenna_roles[port] = roles
            self.antenna_names[port] = name
        
        self.update_antenna_list_ui()

    def get_main_window(self):
        """Obtiene referencia a MainWindow"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'get_antenna_role') or hasattr(parent, 'get_antenna_roles'):
                return parent
            parent = parent.parent()
        return None
    
    def start_scanning(self):
        """Inicia detección continua"""
        if not self.scanner:
            self.log("ERROR: Scanner no disponible")
            QMessageBox.warning(self, "Error", "Scanner no disponible")
            return
        
        if self.is_scanning:
            return
        
        self.is_scanning = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        self.scan_thread = ScanThread(self.scanner)
        self.scan_thread.tag_detected.connect(self.on_tag_detected)
        self.scan_thread.error_occurred.connect(self.on_scan_error)
        self.scan_thread.start()
        
        self.log("🟢 Detección iniciada - Escaneando antenas...")
    
    def stop_scanning(self):
        """Detiene detección"""
        if self.scan_thread:
            self.scan_thread.stop()
            self.scan_thread.wait(2000)
            self.scan_thread = None
        
        self.is_scanning = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.log("🔴 Detección detenida")
    
    def on_scan_error(self, error_msg):
        """Maneja errores del scan"""
        self.log(f"❌ Error: {error_msg}")
    
    def on_tag_detected(self, tag_info):
        """Procesa tag detectado"""
        try:
            tag_number = tag_info['number']
            port = tag_info.get('antenna', 0)
            timestamp = tag_info['timestamp'].strftime('%H:%M:%S.%f')[:-3]
            
            # 🔥 Convertir port a int si es necesario
            port = int(port) if isinstance(port, str) else port
            
            # Verificar que el puerto esté configurado
            if port not in self.antenna_roles:
                logger.warning(f"Tag {tag_number} detectado en puerto {port} no configurado")
                logger.warning(f"Puertos configurados: {list(self.antenna_roles.keys())}")
                return
            
            # Obtener roles y nombre
            roles = self.antenna_roles.get(port, [])
            antenna_name = self.antenna_names.get(port, f"Puerto {port}")
            
            # Si es string (compatibilidad), convertir a lista
            if isinstance(roles, str):
                roles = [roles]
            
            self.detected_tags.add(tag_number)
            
            # Agregar a la tabla
            row = self.detections_table.rowCount()
            self.detections_table.insertRow(row)
            
            self.detections_table.setItem(row, 0, QTableWidgetItem(timestamp))
            self.detections_table.setItem(row, 1, QTableWidgetItem(tag_number))
            self.detections_table.setItem(row, 2, QTableWidgetItem(str(port)))
            
            # Mostrar TODOS los roles
            role_text_parts = []
            if 'start' in roles:
                role_text_parts.append('🟢 Largada')
            if 'finish' in roles:
                role_text_parts.append('🏁 Meta')
            if 'checkpoint' in roles:
                role_text_parts.append('🔵 Checkpoint')
            
            role_text = ' + '.join(role_text_parts) if role_text_parts else '⚪ Sin rol'
            self.detections_table.setItem(row, 3, QTableWidgetItem(role_text))
            
            self.detections_table.setItem(row, 4, QTableWidgetItem(antenna_name))
            
            # Color según rol principal
            if 'start' in roles and 'finish' in roles:
                color = QColor(255, 200, 100)  # Naranja (largada+meta)
            elif 'start' in roles:
                color = QColor(144, 238, 144)  # Verde
            elif 'finish' in roles:
                color = QColor(255, 215, 0)    # Dorado
            elif 'checkpoint' in roles:
                color = QColor(173, 216, 230)  # Azul
            else:
                color = None
            
            if color:
                for col in range(5):
                    self.detections_table.item(row, col).setBackground(color)
            
            self.detections_table.scrollToBottom()
            
            # Actualizar estadísticas
            total_detections = self.detections_table.rowCount()
            unique_tags = len(self.detected_tags)
            self.stats_label.setText(
                f"Detecciones: {total_detections} | Tags únicos: {unique_tags}"
            )
            
            # Emitir señales para TODOS los roles
            if 'start' in roles:
                self.signals.start_detected.emit(tag_number, timestamp)
                self.log(f"🟢 LARGADA: Tag {tag_number}")
            
            if 'finish' in roles:
                self.signals.finish_detected.emit(tag_number, timestamp)
                self.log(f"🏁 META: Tag {tag_number}")
            
            if 'checkpoint' in roles:
                self.signals.checkpoint_detected.emit(tag_number, port, timestamp)
                self.log(f"🔵 CHECKPOINT {port}: Tag {tag_number}")
                
        except Exception as e:
            logger.error(f"Error procesando tag: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_detections(self):
        """Limpia la tabla de detecciones"""
        reply = QMessageBox.question(
            self,
            "Limpiar Detecciones",
            "¿Estás seguro de limpiar todas las detecciones?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.detections_table.setRowCount(0)
            self.detected_tags.clear()
            self.stats_label.setText("Detecciones: 0 | Tags únicos: 0")
            self.log("🗑️ Detecciones limpiadas")
    
    def closeEvent(self, event):
        """Al cerrar, detener scanning"""
        if self.is_scanning:
            self.stop_scanning()
        event.accept()