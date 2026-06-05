"""
Tab de configuración unificado - Conexión + Antenas del Wizard
"""
import json
import os

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QTextEdit, QCheckBox, QWidget,
)
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QColor
from datetime import datetime
from .base_tab import BaseTab
import logging

logger = logging.getLogger(__name__)


class ConfigurationTab(BaseTab):
    """Tab unificado de configuración"""
    
    def __init__(self, scanner=None, signals=None, wizard_config=None, parent=None):
        # ⭐ DEBUG
        print(f"\n=== ConfigurationTab.__init__ ===")
        print(f"  scanner: {scanner is not None}")
        print(f"  signals: {signals is not None}")
        print(f"  wizard_config: {wizard_config is not None}")
        if wizard_config:
            print(f"  wizard_config keys: {wizard_config.keys()}")
            print(f"  antennas: {list(wizard_config.get('antennas', {}).keys())}")
        print("="*40 + "\n")
    
        self.scanner = scanner
        self.wizard_config = wizard_config
        self.edit_mode = False
        super().__init__(signals=signals, parent=parent)
    
    def setup_ui(self):
        """Configurar interfaz"""
        # === SECCIÓN 1: CONEXIÓN ===
        conn_group = QGroupBox("🔌 Conexión del Lector YR8900")
        conn_layout = QHBoxLayout(conn_group)
        
        conn_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit()
        self.host_input.setReadOnly(True)
        conn_layout.addWidget(self.host_input)
        
        conn_layout.addWidget(QLabel("Puerto:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setReadOnly(True)
        conn_layout.addWidget(self.port_input)
        
        # Botón editar
        self.edit_btn = QPushButton("✏️ Editar")
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        self.edit_btn.setMaximumWidth(80)
        conn_layout.addWidget(self.edit_btn)
        
        conn_layout.addStretch()
        
        # Botones de acción
        test_btn = QPushButton("🧪 Test")
        test_btn.clicked.connect(self.test_connection)
        test_btn.setMaximumWidth(80)
        conn_layout.addWidget(test_btn)
        
        self.layout.addWidget(conn_group)
        
        # === SECCIÓN 2: ANTENAS (Simple, solo checkboxes) ===
        antennas_group = QGroupBox("📡 Configuración de Antenas")
        antennas_layout = QVBoxLayout(antennas_group)
        
        # Instrucciones
        info_label = QLabel(
            "Define el rol de cada antena según tu setup físico.\n"
            "Las antenas pueden cumplir múltiples roles (ej: Largada+Meta en circuitos cerrados)."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-style: italic; margin-bottom: 10px;")
        antennas_layout.addWidget(info_label)
        
        # Tabla simplificada
        self.antennas_table = QTableWidget()
        self.antennas_table.setColumnCount(5)
        self.antennas_table.setHorizontalHeaderLabels([
            "Antena", "Habilitada", "Largada", "Meta", "Checkpoint"
        ])
        self.antennas_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.antennas_table.verticalHeader().setVisible(False)
        antennas_layout.addWidget(self.antennas_table)
        
        # Botones de acción
        actions_layout = QHBoxLayout()
        
        rescan_btn = QPushButton("🔄 Re-escanear")
        rescan_btn.clicked.connect(self.rescan_antennas)
        actions_layout.addWidget(rescan_btn)
        
        apply_btn = QPushButton("✅ Aplicar Cambios")
        apply_btn.clicked.connect(self.apply_antenna_config)
        actions_layout.addWidget(apply_btn)
        
        reconfig_btn = QPushButton("🔧 Re-ejecutar Wizard")
        reconfig_btn.clicked.connect(self.rerun_wizard)
        actions_layout.addWidget(reconfig_btn)
        
        actions_layout.addStretch()
        antennas_layout.addLayout(actions_layout)
        
        self.layout.addWidget(antennas_group)
        
        # === SECCIÓN 3: INTEGRACIÓN CLOUD ===
        cloud_group = QGroupBox("☁️ Integración Cloud Backend")
        cloud_layout = QVBoxLayout(cloud_group)

        # Estado
        self.cloud_status_label = QLabel("⚪ No configurado")
        self.cloud_status_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        cloud_layout.addWidget(self.cloud_status_label)

        # URL del backend (sin /api/v1)
        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("URL Backend:"))
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://tu-backend.run.app")
        url_row.addWidget(self.api_url_input)
        cloud_layout.addLayout(url_row)

        # Event ID
        event_row = QHBoxLayout()
        event_row.addWidget(QLabel("Event ID:"))
        self.event_id_input = QLineEdit()
        self.event_id_input.setPlaceholderText("hbcMynoxLHeG5dc5IxAZ")
        event_row.addWidget(self.event_id_input)
        cloud_layout.addLayout(event_row)

        # Nombre del agente
        agent_row = QHBoxLayout()
        agent_row.addWidget(QLabel("Nombre Agente:"))
        self.agent_name_input = QLineEdit()
        self.agent_name_input.setPlaceholderText("Equipo de cronometraje")
        agent_row.addWidget(self.agent_name_input)
        cloud_layout.addLayout(agent_row)

        # Token
        token_row = QHBoxLayout()
        token_row.addWidget(QLabel("Token (agt_...):"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("agt_...")
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        token_row.addWidget(self.token_input)
        cloud_layout.addLayout(token_row)

        # Botones
        cloud_btns = QHBoxLayout()
        save_cloud_btn = QPushButton("💾 Guardar Config Cloud")
        save_cloud_btn.clicked.connect(self._save_cloud_config)
        cloud_btns.addWidget(save_cloud_btn)

        test_cloud_btn = QPushButton("🧪 Verificar Conexión")
        test_cloud_btn.clicked.connect(self._test_cloud_connection)
        cloud_btns.addWidget(test_cloud_btn)

        cloud_btns.addStretch()
        cloud_layout.addLayout(cloud_btns)

        self.layout.addWidget(cloud_group)

        # Cargar config cloud guardada
        self._load_cloud_config_from_file()

        # === LOG ===
        log_group = QGroupBox("📋 Log de Actividad")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        self.layout.addWidget(log_group)
        
        # Cargar datos iniciales
        self.load_config_data()
    
    def load_config_data(self):
        """Cargar datos de la configuración del wizard"""
        if not self.wizard_config:
            self.log("⚠️ No hay configuración del wizard")
            return
        
        # Cargar conexión
        conn = self.wizard_config.get('connection', {})
        self.host_input.setText(conn.get('host', '192.168.0.178'))
        self.port_input.setValue(conn.get('port', 4001))
        
        # Cargar antenas DEL WIZARD (no crear 8 filas vacías)
        antennas = self.wizard_config.get('antennas', {})
        antennas = {str(k): v for k, v in antennas.items()}

        if not antennas:
            self.log("⚠️ No hay antenas configuradas")
            self.antennas_table.setRowCount(0)
            return
        
        # ⭐ CAMBIO CLAVE: Crear solo las filas de antenas que EXISTEN en el config
        antenna_ports = sorted([int(p) for p in antennas.keys()])
        self.antennas_table.setRowCount(len(antenna_ports))
        
        for row, port_num in enumerate(antenna_ports):
            port_str = str(port_num)
            config = antennas[port_str]
            
            enabled = config.get('enabled', False)
            
            # Columna 0: Número de puerto (no editable)
            ant_label = QTableWidgetItem(f"Puerto {port_num}")
            ant_label.setFlags(ant_label.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.antennas_table.setItem(row, 0, ant_label)
            
            # Columna 1: Checkbox Habilitada
            enabled_check = QCheckBox()
            enabled_check.setChecked(enabled)
            enabled_check.setEnabled(True)  # Siempre editable
            widget_enabled = QWidget()
            layout_enabled = QHBoxLayout(widget_enabled)
            layout_enabled.addWidget(enabled_check)
            layout_enabled.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_enabled.setContentsMargins(0, 0, 0, 0)
            self.antennas_table.setCellWidget(row, 1, widget_enabled)
            
            # Columna 2: Checkbox Largada
            start_check = QCheckBox()
            start_check.setChecked(config.get('start', False))
            start_check.setEnabled(enabled)
            widget_start = QWidget()
            layout_start = QHBoxLayout(widget_start)
            layout_start.addWidget(start_check)
            layout_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_start.setContentsMargins(0, 0, 0, 0)
            self.antennas_table.setCellWidget(row, 2, widget_start)
            
            # Conectar enabled checkbox para habilitar/deshabilitar roles
            enabled_check.stateChanged.connect(
                lambda state, r=row: self.on_antenna_enabled_changed(r, state)
            )
            
            # Columna 3: Checkbox Meta
            finish_check = QCheckBox()
            finish_check.setChecked(config.get('finish', False))
            finish_check.setEnabled(enabled)
            widget_finish = QWidget()
            layout_finish = QHBoxLayout(widget_finish)
            layout_finish.addWidget(finish_check)
            layout_finish.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_finish.setContentsMargins(0, 0, 0, 0)
            self.antennas_table.setCellWidget(row, 3, widget_finish)
            
            # Columna 4: Checkbox Checkpoint
            checkpoint_check = QCheckBox()
            checkpoint_check.setChecked(config.get('checkpoint', False))
            checkpoint_check.setEnabled(enabled)
            widget_checkpoint = QWidget()
            layout_checkpoint = QHBoxLayout(widget_checkpoint)
            layout_checkpoint.addWidget(checkpoint_check)
            layout_checkpoint.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_checkpoint.setContentsMargins(0, 0, 0, 0)
            self.antennas_table.setCellWidget(row, 4, widget_checkpoint)
            
            # Color de fondo según configuración
            if enabled:
                if config.get('start'):
                    color = QColor(144, 238, 144, 100)  # Verde
                elif config.get('finish'):
                    color = QColor(255, 215, 0, 100)  # Dorado
                elif config.get('checkpoint'):
                    color = QColor(173, 216, 230, 100)  # Azul
                else:
                    color = None
                
                if color:
                    self.antennas_table.item(row, 0).setBackground(color)
        
        enabled_count = sum(1 for c in antennas.values() if c.get('enabled', False))
        self.log(f"✓ Configuración cargada: {enabled_count} antenas en puertos {antenna_ports}")

    def on_antenna_enabled_changed(self, row, state):
        """Habilita/deshabilita checkboxes de roles cuando se cambia el estado de habilitada"""
        enabled = (state == Qt.CheckState.Checked.value)
        
        # Habilitar/deshabilitar los checkboxes de roles
        for col in [2, 3, 4]:  # Largada, Meta, Checkpoint
            widget = self.antennas_table.cellWidget(row, col)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                checkbox.setEnabled(enabled)

    def toggle_edit_mode(self):
        """Alternar modo de edición de conexión"""
        self.edit_mode = not self.edit_mode
        
        if self.edit_mode:
            self.host_input.setReadOnly(False)
            self.port_input.setReadOnly(False)
            self.host_input.setStyleSheet("background-color: #fff9e6;")
            self.port_input.setStyleSheet("background-color: #fff9e6;")
            self.edit_btn.setText("💾 Guardar")
            self.log("✏️ Modo edición de conexión activado")
        else:
            self.host_input.setReadOnly(True)
            self.port_input.setReadOnly(True)
            self.host_input.setStyleSheet("")
            self.port_input.setStyleSheet("")
            self.edit_btn.setText("✏️ Editar")
            
            # Actualizar config
            if self.wizard_config:
                self.wizard_config['connection']['host'] = self.host_input.text()
                self.wizard_config['connection']['port'] = self.port_input.value()
                
                # Guardar en archivo
                self.save_config()
            
            self.log("💾 Configuración de conexión guardada")
    
    def apply_antenna_config(self):
        """Aplicar cambios en configuración de antenas"""
        if not self.wizard_config:
            return
        
        # Leer checkboxes y actualizar config
        updated = 0
        antennas = self.wizard_config.get('antennas', {})
        antenna_ports = sorted([int(p) for p in antennas.keys()])
        for row, port_num in enumerate(antenna_ports):
            port_str = str(port_num)
            
            # Leer checkboxes
            enabled_widget = self.antennas_table.cellWidget(row, 1)
            enabled = enabled_widget.layout().itemAt(0).widget().isChecked()
            
            if enabled:
                start_widget = self.antennas_table.cellWidget(row, 2)
                start = start_widget.layout().itemAt(0).widget().isChecked()
                
                finish_widget = self.antennas_table.cellWidget(row, 3)
                finish = finish_widget.layout().itemAt(0).widget().isChecked()
                
                checkpoint_widget = self.antennas_table.cellWidget(row, 4)
                checkpoint = checkpoint_widget.layout().itemAt(0).widget().isChecked()
                
                # Actualizar o crear config de esta antena
                if port_str not in self.wizard_config.get('antennas', {}):
                    self.wizard_config['antennas'][port_str] = {}
                
                self.wizard_config['antennas'][port_str].update({
                    'enabled': True,
                    'start': start,
                    'finish': finish,
                    'checkpoint': checkpoint,
                    'name': f'Antena {port_num}'
                })
                updated += 1
        
        # Guardar
        self.save_config()
        self.log(f"✅ Configuración aplicada: {updated} antenas actualizadas")
        
        QMessageBox.information(
            self,
            "Configuración Aplicada",
            f"Se actualizó la configuración de {updated} antenas.\n\n"
            "Reinicie la aplicación para aplicar los cambios."
        )
    
    def save_config(self):
        """Guardar configuración en archivo"""
        try:
            import json
            with open('timing_system_config.json', 'w') as f:
                json.dump(self.wizard_config, f, indent=2)
            self.log("💾 Archivo guardado")
        except Exception as e:
            self.log(f"❌ Error guardando: {e}")
    
    def test_connection(self):
        """Test de conexión"""
        if not self.scanner:
            self.log("❌ Scanner no disponible")
            return
        
        self.log("🧪 Probando conexión...")
        if hasattr(self.scanner, 'test_original_command'):
            if self.scanner.test_original_command():
                self.log("✅ Test exitoso")
            else:
                self.log("❌ Test falló")
    
    def rescan_antennas(self):
        """Re-escanear antenas físicas"""
        if not self.scanner:
            self.log("❌ Scanner no disponible")
            return
        
        self.log("🔄 Re-escaneando antenas físicas...")
        detected = self.scanner.detect_connected_antennas()
        self.log(f"✅ Detectadas {len(detected)} antenas: {detected}")
        
        # Actualizar el wizard_config con las antenas detectadas
        if not self.wizard_config:
            self.wizard_config = {'connection': {}, 'antennas': {}}
        
        # Crear/actualizar entradas para antenas detectadas
        for port in detected:
            port_str = str(port)
            if port_str not in self.wizard_config.get('antennas', {}):
                self.wizard_config['antennas'][port_str] = {
                    'enabled': True,
                    'name': f'Antena {port}',
                    'start': False,
                    'finish': False,
                    'checkpoint': False
                }
            else:
                # Marcar como habilitada si ya existe
                self.wizard_config['antennas'][port_str]['enabled'] = True
        
        # Recargar la tabla con las antenas actualizadas
        self.load_config_data()
        
        QMessageBox.information(
            self,
            "Re-escaneo Completado",
            f"Se detectaron {len(detected)} antenas.\n\n"
            f"Puertos: {', '.join(map(str, detected))}\n\n"
            "Configure los roles y haga clic en 'Aplicar Cambios'."
        )
    
    def rerun_wizard(self):
        """Re-ejecutar el wizard sin reiniciar"""
        reply = QMessageBox.question(
            self,
            "Re-ejecutar Wizard",
            "¿Desea reconfigurar el sistema?\n\n"
            "Se abrirá el wizard de configuración.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Importar wizard
                from src.gui.wizard.configuration_wizard import ConfigurationWizard
                
                # Ejecutar wizard
                wizard = ConfigurationWizard()
                if wizard.exec():
                    # Obtener nueva config
                    new_config = wizard.get_configuration()
                    
                    # Guardar
                    import json
                    with open('timing_system_config.json', 'w') as f:
                        json.dump(new_config, f, indent=2)
                    
                    self.log("✅ Nueva configuración guardada")
                    
                    # Actualizar la config actual
                    self.wizard_config = new_config
                    
                    # Recargar datos en el tab
                    self.load_config_data()
                    
                    # Actualizar scanner en MainWindow
                    main_window = self.window()
                    if hasattr(main_window, 'wizard_config'):
                        main_window.wizard_config = new_config
                    if hasattr(main_window, 'setup_scanner'):
                        main_window.setup_scanner()
                    
                    QMessageBox.information(
                        self,
                        "Configuración Actualizada",
                        "La nueva configuración ha sido aplicada.\n\n"
                        "Reinicie la aplicación para aplicar todos los cambios."
                    )
                else:
                    self.log("⚠️ Wizard cancelado")
                    
            except Exception as e:
                self.log(f"❌ Error ejecutando wizard: {e}")
                import traceback
                traceback.print_exc()
    
    # ========================================================================
    # Cloud Backend Integration
    # ========================================================================

    def _save_cloud_config(self):
        """Guardar configuración cloud bajo sub-key 'cloud' en api_config.json."""
        path = 'config/api_config.json'
        try:
            data = {}
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            base_url = self.api_url_input.text().strip().rstrip('/')
            data['cloud'] = {
                'api_url': base_url + '/api/v1',
                'event_id': self.event_id_input.text().strip(),
                'agent_name': self.agent_name_input.text().strip(),
                'api_key': self.token_input.text().strip(),
            }
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.cloud_status_label.setText("🟡 Configurado (sin verificar)")
            self.cloud_status_label.setStyleSheet(
                "font-weight: bold; font-size: 13px; color: orange;")
            self.log("☁️ Config cloud guardada en config/api_config.json")

            # Recargar en MainWindow si está disponible
            main_window = self.window()
            if hasattr(main_window, '_load_cloud_config'):
                main_window.cloud_config = main_window._load_cloud_config()
                self.log("✅ Config cloud recargada en MainWindow")
        except Exception as e:
            logger.warning(f"⚠️ Error guardando cloud config: {e}")
            self.log(f"❌ Error guardando cloud config: {e}")

    def _load_cloud_config_from_file(self):
        """Cargar config cloud desde archivo y mostrar en UI."""
        path = 'config/api_config.json'
        try:
            if not os.path.exists(path):
                return
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            cloud = data.get('cloud', {})
            if cloud.get('api_url') and cloud.get('api_key'):
                self._apply_cloud_config_to_ui(cloud)
                self.cloud_status_label.setText("🟡 Configurado (sin verificar)")
                self.cloud_status_label.setStyleSheet(
                    "font-weight: bold; font-size: 13px; color: orange;")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cargar cloud config: {e}")

    def _apply_cloud_config_to_ui(self, cloud: dict):
        """Poblar campos UI desde dict de cloud config."""
        api_url = cloud.get('api_url', '')
        # Strip /api/v1 for display
        if api_url.endswith('/api/v1'):
            api_url = api_url[:-7]
        self.api_url_input.setText(api_url)
        self.event_id_input.setText(cloud.get('event_id', ''))
        self.agent_name_input.setText(cloud.get('agent_name', ''))
        self.token_input.setText(cloud.get('api_key', ''))

    def _test_cloud_connection(self):
        """Verificar conexión con el backend cloud."""
        import threading
        import requests

        base_url = self.api_url_input.text().strip().rstrip('/')
        token = self.token_input.text().strip()
        event_id = self.event_id_input.text().strip()

        if not base_url or not token:
            QMessageBox.warning(self, "Faltan datos", "Ingrese URL y Token antes de verificar.")
            return

        self.cloud_status_label.setText("🔄 Verificando...")
        self.cloud_status_label.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: gray;")

        def _check():
            try:
                url = f"{base_url}/api/v1/timing/events/{event_id}/reads/summary"
                r = requests.get(url, timeout=5)
                ok = r.status_code in (200, 404)  # 404 = event not found but backend reachable
                return ok, r.status_code
            except Exception as e:
                return False, str(e)

        def _run():
            ok, code = _check()
            # Use QTimer.singleShot to update UI safely from main thread
            from PyQt6.QtCore import QTimer

            def _update():
                if ok:
                    self.cloud_status_label.setText("🟢 Conectado")
                    self.cloud_status_label.setStyleSheet(
                        "font-weight: bold; font-size: 13px; color: green;")
                    self.log(f"✅ Backend alcanzable (HTTP {code})")
                else:
                    self.cloud_status_label.setText("🔴 Sin conexión")
                    self.cloud_status_label.setStyleSheet(
                        "font-weight: bold; font-size: 13px; color: red;")
                    self.log(f"❌ No se pudo conectar: {code}")

            QTimer.singleShot(0, _update)

        threading.Thread(target=_run, daemon=True).start()

    # ========================================================================
    # Utilidades
    # ========================================================================

    def get_timestamp(self):
        """Timestamp formateado"""
        return datetime.now().strftime('%H:%M:%S')