#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DetectionTab refactorizado - Solo UI y coordinación
src/gui/tabs/detection_tab.py

Responsabilidad única: UI y coordinación entre componentes
Delegación: ScanThread para scanning, TagProcessor para lógica
"""

from datetime import datetime

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox, QMessageBox, QFrame, QSlider, QSpinBox
)
from PyQt6.QtCore import pyqtSlot, Qt, QTimer
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
        self.tag_rows = {}        # {tag_id: row_index}
        # tag_data structure:
        # {tag_id: {start_ts, start_dt, checkpoint_ts: {cp_num: str},
        #           finish_ts, finish_dt, name, distance, bib}}
        self.tag_data = {}

        # Timer para actualizar tiempo acumulado en vivo
        self._elapsed_timer = QTimer()
        self._elapsed_timer.timeout.connect(self._update_elapsed_times)
        self._elapsed_timer.start(1000)

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

        # --- Panel de potencia online ---
        power_frame = QFrame()
        power_frame.setFrameShape(QFrame.Shape.StyledPanel)
        power_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; padding: 2px;")
        power_online_layout = QHBoxLayout(power_frame)
        power_online_layout.setContentsMargins(8, 4, 8, 4)

        power_icon = QLabel("⚡")
        power_online_layout.addWidget(power_icon)

        power_lbl = QLabel("Potencia:")
        power_lbl.setStyleSheet("font-weight: bold; border: none; background: transparent;")
        power_online_layout.addWidget(power_lbl)

        self.online_power_slider = QSlider(Qt.Orientation.Horizontal)
        self.online_power_slider.setRange(10, 33)
        self.online_power_slider.setValue(25)
        self.online_power_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.online_power_slider.setTickInterval(5)
        self.online_power_slider.setMaximumWidth(160)
        self.online_power_slider.valueChanged.connect(self._on_online_power_slider_changed)
        power_online_layout.addWidget(self.online_power_slider)

        self.online_power_spinbox = QSpinBox()
        self.online_power_spinbox.setRange(10, 33)
        self.online_power_spinbox.setValue(25)
        self.online_power_spinbox.setSuffix(" dBm")
        self.online_power_spinbox.setMaximumWidth(80)
        self.online_power_spinbox.valueChanged.connect(self.online_power_slider.setValue)
        self.online_power_slider.valueChanged.connect(self.online_power_spinbox.setValue)
        power_online_layout.addWidget(self.online_power_spinbox)

        self.online_distance_label = QLabel("≈ 3 m")
        self.online_distance_label.setStyleSheet("color: #0f3460; font-weight: bold; border: none; background: transparent; min-width: 50px;")
        power_online_layout.addWidget(self.online_distance_label)

        self.apply_power_btn = QPushButton("Aplicar")
        self.apply_power_btn.setToolTip("Aplicar potencia al lector RFID conectado")
        self.apply_power_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: white;
                font-weight: bold;
                padding: 3px 10px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #1a5276; }
            QPushButton:disabled { background-color: #aaa; }
        """)
        self.apply_power_btn.clicked.connect(self.apply_power_online)
        power_online_layout.addWidget(self.apply_power_btn)

        self.layout.addWidget(power_frame)

        # Tabla de detecciones (agrupada por participante)
        self.detections_table = QTableWidget()
        self.detections_table.setAlternatingRowColors(True)
        self.detections_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.detections_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        header = self.detections_table.horizontalHeader()
        header.setStretchLastSection(True)
        self._rebuild_columns()  # Construir columnas iniciales (sin CPs)
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

    # ── Helpers de columnas dinámicas ──────────────────────────────────────

    @property
    def _checkpoint_ports(self) -> list:
        """Puertos de antenas checkpoint, ordenados = CP1, CP2, ..."""
        return sorted(p for p, roles in self.antenna_roles.items() if 'checkpoint' in roles)

    def _n_cp(self) -> int:
        return len(self._checkpoint_ports)

    def _col_meta(self) -> int:
        return 5 + self._n_cp()   # Tag(0) Dorsal(1) Nombre(2) Distancia(3) Largada(4) CP…

    def _col_elapsed(self) -> int:
        return 6 + self._n_cp()

    def _port_to_cp_num(self, port: int):
        """Puerto de antena → número de checkpoint (1-based), o None si no es CP."""
        pts = self._checkpoint_ports
        return pts.index(port) + 1 if port in pts else None

    def _rebuild_columns(self):
        """Reconstruir encabezados de tabla según antenas checkpoint configuradas."""
        n_cp = self._n_cp()
        cols = ["Tag", "Dorsal", "Nombre", "Distancia", "🟢 Largada"]
        for i in range(1, n_cp + 1):
            cols.append(f"🔵 CP{i}")
        cols += ["🏁 Meta", "⏱ Acumulado"]
        self.detections_table.setColumnCount(len(cols))
        self.detections_table.setHorizontalHeaderLabels(cols)

    def _update_elapsed_times(self):
        """Actualizar columna Acumulado para atletas en carrera (cada segundo)."""
        now = datetime.now()
        elapsed_col = self._col_elapsed()
        if elapsed_col >= self.detections_table.columnCount():
            return
        for tag_id, data in self.tag_data.items():
            if tag_id not in self.tag_rows:
                continue
            if data['finish_dt'] or not data['start_dt']:
                continue  # ya terminó o no arrancó
            row = self.tag_rows[tag_id]
            elapsed = now - data['start_dt']
            secs = int(elapsed.total_seconds())
            h, rem = divmod(secs, 3600)
            m, s = divmod(rem, 60)
            text = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
            item = self.detections_table.item(row, elapsed_col)
            if item:
                item.setText(text)
            else:
                self.detections_table.setItem(row, elapsed_col, QTableWidgetItem(text))
    
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
    
    @pyqtSlot(str, str, str, str)
    def on_athlete_tag_resolved(self, tag_id: str, athlete_name: str,
                                distance_name: str, bib: str):
        """Actualizar nombre, distancia y dorsal en la tabla."""
        if tag_id in self.tag_data:
            self.tag_data[tag_id]['name'] = athlete_name
            self.tag_data[tag_id]['distance'] = distance_name
            self.tag_data[tag_id]['bib'] = bib

        if tag_id in self.tag_rows:
            row = self.tag_rows[tag_id]
            self.detections_table.setItem(row, 1, QTableWidgetItem(bib))
            self.detections_table.setItem(row, 2, QTableWidgetItem(athlete_name))
            self.detections_table.setItem(row, 3, QTableWidgetItem(distance_name))

    @pyqtSlot(str, str, str)
    def on_athlete_finished(self, athlete_name: str, distance_name: str, formatted_time: str):
        """Actualizar panel de última llegada cuando un atleta cruza la meta"""
        text = f"{athlete_name}  |  {distance_name}  |  {formatted_time}"
        self.last_finish_label.setText(text)
        self.last_finish_label.setStyleSheet(
            "color: #00ff88; font-size: 13px; font-weight: bold; background: transparent; border: none;"
        )

    def _on_online_power_slider_changed(self, value: int):
        """Actualizar etiqueta de distancia estimada"""
        if value <= 15:
            dist = "≈ 1 m"
        elif value <= 20:
            dist = "≈ 2 m"
        elif value <= 25:
            dist = "≈ 3 m"
        elif value <= 28:
            dist = "≈ 4-5 m"
        elif value <= 30:
            dist = "≈ 6 m"
        else:
            dist = "≈ 7-8 m"
        self.online_distance_label.setText(dist)

    def apply_power_online(self):
        """Aplicar potencia al lector RFID conectado en tiempo real"""
        power_dbm = self.online_power_spinbox.value()

        if not self.scanner:
            QMessageBox.warning(self, "Sin conexión", "No hay lector RFID conectado.")
            return

        if not hasattr(self.scanner, 'set_output_power'):
            QMessageBox.warning(self, "No soportado", "Este lector no soporta cambio de potencia en línea.")
            return

        try:
            ok = self.scanner.set_output_power(power_dbm)
            if ok:
                self.apply_power_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #10b981;
                        color: white;
                        font-weight: bold;
                        padding: 3px 10px;
                        border-radius: 3px;
                    }
                """)
                self.apply_power_btn.setText("✓ Aplicado")
                logger.info(f"⚡ Potencia aplicada online: {power_dbm} dBm")
                # Restaurar el botón después de 2 segundos
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(2000, self._reset_apply_power_btn)
            else:
                QMessageBox.warning(self, "Error", f"No se pudo aplicar {power_dbm} dBm al lector.")
        except Exception as e:
            logger.error(f"❌ Error aplicando potencia: {e}")
            QMessageBox.critical(self, "Error", f"Error al aplicar potencia:\n{e}")

    def _reset_apply_power_btn(self):
        """Restaurar el botón de potencia a su estado normal"""
        self.apply_power_btn.setText("Aplicar")
        self.apply_power_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: white;
                font-weight: bold;
                padding: 3px 10px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #1a5276; }
        """)

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

        # Actualizar antenas disponibles en el scanner
        if hasattr(self, 'scanner') and self.scanner:
            self.scanner.available_antennas = sorted(self.antenna_roles.keys())
            logger.info(f"🔄 Scanner actualizado con antenas: {self.scanner.available_antennas}")

        if self.is_scanning and self.scan_thread and self.scanner:
            self.scanner.available_antennas = sorted(self.antenna_roles.keys())
            logger.info(f"🔄 Scanner actualizado en caliente: {self.scanner.available_antennas}")

        # Reconstruir columnas según nuevas antenas checkpoint
        self._rebuild_columns()



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

        self.scanner.available_antennas = sorted(self.antenna_roles.keys())
        logger.info(f"🔄 Iniciando scan con antenas: {self.scanner.available_antennas}")

        # Crear procesador de tags
        self.tag_processor = TagProcessor(self.antenna_roles, self.signals)

        # Crear y arrancar thread de scanning
        self.scan_thread = ScanThread(self.scanner)


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
        """Agregar o actualizar detección en la tabla (agrupada por participante)."""
        tag_id = processed['tag_id']
        roles = processed['roles']
        port = processed['port']
        ts_str = processed['timestamp']             # "HH:MM:SS.mmm"
        ts_dt = processed.get('timestamp_obj')      # datetime o None
        ts_display = ts_str[:8] if len(ts_str) >= 8 else ts_str  # "HH:MM:SS"

        # Inicializar datos del tag si es la primera vez
        if tag_id not in self.tag_data:
            self.tag_data[tag_id] = {
                'start_ts': None, 'start_dt': None,
                'checkpoint_ts': {},   # {cp_num: "HH:MM:SS"}
                'finish_ts': None, 'finish_dt': None,
                'name': 'N/A', 'distance': 'N/A', 'bib': '-',
            }

        data = self.tag_data[tag_id]

        # Registrar timestamps (solo primera detección de cada punto)
        if 'start' in roles and data['start_ts'] is None:
            data['start_ts'] = ts_display
            data['start_dt'] = ts_dt

        if 'checkpoint' in roles:
            cp_num = self._port_to_cp_num(port)
            if cp_num is not None and cp_num not in data['checkpoint_ts']:
                data['checkpoint_ts'][cp_num] = ts_display

        if 'finish' in roles and data['finish_ts'] is None:
            data['finish_ts'] = ts_display
            data['finish_dt'] = ts_dt

        # Crear fila si no existe
        if tag_id in self.tag_rows:
            row = self.tag_rows[tag_id]
        else:
            row = self.detections_table.rowCount()
            self.detections_table.insertRow(row)
            self.tag_rows[tag_id] = row

        n_cp = self._n_cp()
        meta_col = self._col_meta()
        elapsed_col = self._col_elapsed()

        # Col 0: Tag
        self.detections_table.setItem(row, 0, QTableWidgetItem(tag_id))
        # Col 1: Dorsal
        self.detections_table.setItem(row, 1, QTableWidgetItem(data['bib']))
        # Col 2: Nombre
        self.detections_table.setItem(row, 2, QTableWidgetItem(data['name']))
        # Col 3: Distancia
        self.detections_table.setItem(row, 3, QTableWidgetItem(data['distance']))

        # Col 4: Largada
        start_item = QTableWidgetItem(data['start_ts'] or '—')
        if data['start_ts']:
            start_item.setForeground(QColor(0, 150, 0))
        self.detections_table.setItem(row, 4, start_item)

        # Col 5..4+n_cp: CPs
        for i in range(1, n_cp + 1):
            ts = data['checkpoint_ts'].get(i, '—')
            item = QTableWidgetItem(ts)
            if ts != '—':
                item.setForeground(QColor(0, 100, 200))
            self.detections_table.setItem(row, 4 + i, item)

        # Col meta_col: Meta
        finish_item = QTableWidgetItem(data['finish_ts'] or '—')
        if data['finish_ts']:
            finish_item.setForeground(QColor(200, 150, 0))
        self.detections_table.setItem(row, meta_col, finish_item)

        # Col elapsed_col: T. Acumulado
        if data['finish_dt'] and data['start_dt']:
            net = data['finish_dt'] - data['start_dt']
            secs = int(net.total_seconds())
            h, rem = divmod(secs, 3600)
            m, s = divmod(rem, 60)
            elapsed_text = f"{h:02d}:{m:02d}:{s:02d}"
            elapsed_item = QTableWidgetItem(elapsed_text)
            elapsed_item.setForeground(QColor(0, 180, 0))
        elif data['start_dt']:
            elapsed_item = QTableWidgetItem("00:00")
        else:
            elapsed_item = QTableWidgetItem('—')
        self.detections_table.setItem(row, elapsed_col, elapsed_item)

        # Color de fondo según rol
        if processed['color_code'] != 'none':
            rgb = self.tag_processor.get_color_rgb(processed['color_code'])
            color = QColor(*rgb)
            color.setAlpha(80)
            for col in range(self.detections_table.columnCount()):
                item = self.detections_table.item(row, col)
                if item:
                    item.setBackground(color)

        self.detections_table.scrollToItem(self.detections_table.item(row, 0))
    
    def update_statistics(self):
        """Actualizar estadísticas de detecciones"""
        unique_tags = len(self.detected_tags)
        finished = sum(1 for d in self.tag_data.values() if d.get('finish_ts'))
        running = sum(1 for d in self.tag_data.values() if d.get('start_ts') and not d.get('finish_ts'))
        self.stats_label.setText(
            f"Tags únicos: {unique_tags} | En carrera: {running} | Finalizados: {finished}"
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
            self._rebuild_columns()
            self.update_statistics()
            self.log("🗑️ Detecciones limpiadas")
    
    def closeEvent(self, event):
        """Al cerrar, detener scanning"""
        if self.is_scanning:
            self.stop_scanning()
        event.accept()