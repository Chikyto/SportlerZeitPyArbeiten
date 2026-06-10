"""
Tab de configuración unificado - Conexión + Antenas del Wizard
"""
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QTextEdit, QCheckBox, QWidget,
    QFileDialog,
)
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QColor
from datetime import datetime
from .base_tab import BaseTab
import json
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

        # === SECCIÓN 3: BACKEND CLOUD ===
        cloud_group = QGroupBox("☁️ Resultados Públicos / Backend Cloud")
        cloud_layout = QVBoxLayout(cloud_group)

        # Fila de estado + acciones
        status_layout = QHBoxLayout()
        self.cloud_status_label = QLabel("⚪ Sin configurar")
        self.cloud_status_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        status_layout.addWidget(self.cloud_status_label)
        status_layout.addStretch()

        import_btn = QPushButton("📂 Importar config (.szconfig)")
        import_btn.clicked.connect(self.import_szconfig)
        import_btn.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold; padding: 6px 12px;")
        status_layout.addWidget(import_btn)

        test_cloud_btn = QPushButton("🧪 Probar conexión")
        test_cloud_btn.clicked.connect(self.test_cloud_connection)
        test_cloud_btn.setMaximumWidth(140)
        status_layout.addWidget(test_cloud_btn)

        cloud_layout.addLayout(status_layout)

        # Campos (read-only, se rellenan al importar)
        fields_layout = QHBoxLayout()

        fields_layout.addWidget(QLabel("URL:"))
        self.cloud_url_input = QLineEdit()
        self.cloud_url_input.setReadOnly(True)
        self.cloud_url_input.setPlaceholderText("Se carga al importar el .szconfig")
        self.cloud_url_input.setStyleSheet("color: #555;")
        fields_layout.addWidget(self.cloud_url_input, 3)

        fields_layout.addWidget(QLabel("Evento:"))
        self.cloud_event_input = QLineEdit()
        self.cloud_event_input.setReadOnly(True)
        self.cloud_event_input.setMaximumWidth(160)
        fields_layout.addWidget(self.cloud_event_input, 1)

        fields_layout.addWidget(QLabel("Agente:"))
        self.cloud_agent_input = QLineEdit()
        self.cloud_agent_input.setReadOnly(True)
        self.cloud_agent_input.setMaximumWidth(160)
        fields_layout.addWidget(self.cloud_agent_input, 1)

        cloud_layout.addLayout(fields_layout)

        # Fila de sincronización de atletas
        sync_layout = QHBoxLayout()
        sync_info = QLabel("Live tracking: los atletas deben estar registrados en la plataforma web.")
        sync_info.setStyleSheet("color: #555; font-size: 11px;")
        sync_layout.addWidget(sync_info)
        sync_layout.addStretch()
        self.sync_athletes_btn = QPushButton("☁️ Sincronizar atletas")
        self.sync_athletes_btn.clicked.connect(self.sync_athletes_to_backend)
        self.sync_athletes_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 6px 14px;")
        self.sync_athletes_btn.setToolTip("Sube atletas locales al backend para live tracking — upsert por dorsal")
        sync_layout.addWidget(self.sync_athletes_btn)
        cloud_layout.addLayout(sync_layout)

        self.layout.addWidget(cloud_group)

        # Cargar config cloud guardada (si existe)
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
        raw = self.wizard_config.get('antennas', {})
        # Filtrar solo claves que son puertos numéricos válidos
        antennas = {}
        for k, v in raw.items():
            try:
                antennas[str(int(k))] = v
            except (ValueError, TypeError):
                pass

        if not antennas:
            self.log("⚠️ No hay antenas configuradas")
            self.antennas_table.setRowCount(0)
            return

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
            self.log("❌ No hay configuración disponible")
            QMessageBox.warning(
                self,
                "Error",
                "No hay configuración disponible.\n\nEjecute el wizard de configuración primero."
            )
            return

        try:
            # Asegurar que existe la clave 'antennas'
            if 'antennas' not in self.wizard_config:
                self.wizard_config['antennas'] = {}

            # Leer checkboxes y actualizar config
            updated = 0
            for row in range(self.antennas_table.rowCount()):
                # Obtener el número de puerto real desde la columna 0
                port_item = self.antennas_table.item(row, 0)
                if not port_item:
                    continue

                # Extraer número de puerto del texto "Puerto N"
                port_text = port_item.text()
                port_num = int(port_text.split()[-1])
                port_str = str(port_num)

                # Leer checkboxes
                enabled_widget = self.antennas_table.cellWidget(row, 1)
                if not enabled_widget:
                    continue

                enabled = enabled_widget.layout().itemAt(0).widget().isChecked()

                if enabled:
                    start_widget = self.antennas_table.cellWidget(row, 2)
                    start = start_widget.layout().itemAt(0).widget().isChecked()

                    finish_widget = self.antennas_table.cellWidget(row, 3)
                    finish = finish_widget.layout().itemAt(0).widget().isChecked()

                    checkpoint_widget = self.antennas_table.cellWidget(row, 4)
                    checkpoint = checkpoint_widget.layout().itemAt(0).widget().isChecked()

                    # Actualizar o crear config de esta antena
                    if port_str not in self.wizard_config['antennas']:
                        self.wizard_config['antennas'][port_str] = {}

                    self.wizard_config['antennas'][port_str].update({
                        'enabled': True,
                        'start': start,
                        'finish': finish,
                        'checkpoint': checkpoint,
                        'name': f'Antena {port_num}'
                    })
                    updated += 1
                else:
                    # Si está desmarcada, deshabilitar la antena en la config
                    if port_str in self.wizard_config['antennas']:
                        self.wizard_config['antennas'][port_str]['enabled'] = False

            # Guardar
            self.save_config()
            self.log(f"✅ Configuración aplicada: {updated} antenas actualizadas")

            main_window = self.window()
            if hasattr(main_window, 'tab_manager'):
                main_window.tab_manager.apply_config_to_all_tabs(self.wizard_config)


            QMessageBox.information(self, "OK", f"Configuración aplicada: {updated} antenas.")
            

        except Exception as e:
            self.log(f"❌ Error aplicando configuración: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al aplicar configuración:\n\n{e}"
            )
            import traceback
            traceback.print_exc()
    
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
            QMessageBox.warning(
                self,
                "Error",
                "Scanner no disponible.\n\nVerifique la conexión con el lector RFID."
            )
            return

        try:
            self.log("🔄 Re-escaneando antenas físicas...")

            # Verificar que el método existe
            if not hasattr(self.scanner, 'detect_connected_antennas'):
                self.log("❌ El scanner no soporta detección de antenas")
                QMessageBox.warning(
                    self,
                    "Función no disponible",
                    "El scanner actual no soporta detección automática de antenas."
                )
                return

            detected = self.scanner.detect_connected_antennas()
            self.log(f"✅ Detectadas {len(detected)} antenas: {detected}")

            # Actualizar el wizard_config con las antenas detectadas
            if not self.wizard_config:
                self.wizard_config = {'connection': {}, 'antennas': {}}

            # Asegurar que existe la clave 'antennas'
            if 'antennas' not in self.wizard_config:
                self.wizard_config['antennas'] = {}

            # Crear/actualizar entradas para antenas detectadas
            for port in detected:
                port_str = str(port)
                if port_str not in self.wizard_config['antennas']:
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

            main_window = self.window()
            if hasattr(main_window, 'tab_manager'):
                main_window.tab_manager.apply_config_to_all_tabs(self.wizard_config)

            QMessageBox.information(
                self,
                "Re-escaneo Completado",
                f"Se detectaron {len(detected)} antenas.\n\n"
                f"Puertos: {', '.join(map(str, detected))}\n\n"
                "Configure los roles y haga clic en 'Aplicar Cambios'."
            )

        except Exception as e:
            self.log(f"❌ Error en re-escaneo: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al re-escanear antenas:\n\n{e}"
            )
            import traceback
            traceback.print_exc()
    
    def rerun_wizard(self):
        """Re-ejecutar el wizard sin reiniciar"""
        reply = QMessageBox.question(
            self,
            "Re-ejecutar Wizard",
            "¿Desea reconfigurar el sistema?\n\n"
            "Se abrirá el wizard de configuración.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        main_window = self.window()

        # 1. Desconectar scanner para liberar el socket del lector
        scanner = getattr(main_window, 'scanner', None)
        if scanner and hasattr(scanner, 'disconnect'):
            try:
                scanner.disconnect()
                self.log("🔌 Scanner desconectado para re-configuración")
            except Exception as e:
                self.log(f"⚠️ No se pudo desconectar scanner: {e}")

        try:
            # 2. Cargar config guardada para pre-poblar el wizard con el IP correcto
            from config.system_config import SystemConfig
            saved_config = SystemConfig()
            saved_config.load_from_file('timing_system_config.json')

            # 3. Abrir wizard con la config actual (IP correcta)
            from src.gui.wizard.auto_wizard import AutoConfigurationWizard
            wizard = AutoConfigurationWizard(config=saved_config)

            if wizard.exec():
                new_config = wizard.get_configuration()

                with open('timing_system_config.json', 'w') as f:
                    json.dump(new_config, f, indent=2)

                self.log("✅ Nueva configuración guardada")
                self.wizard_config = new_config
                self.load_config_data()

                if hasattr(main_window, 'wizard_config'):
                    main_window.wizard_config = new_config
                if hasattr(main_window, 'setup_scanner'):
                    main_window.setup_scanner()
                if hasattr(main_window, 'tab_manager'):
                    main_window.tab_manager.apply_config_to_all_tabs(new_config)

                QMessageBox.information(
                    self,
                    "Configuración Actualizada",
                    "La nueva configuración ha sido aplicada."
                )
            else:
                self.log("⚠️ Wizard cancelado — reconectando scanner anterior...")
                # Reconectar con la config que había antes
                if hasattr(main_window, 'setup_scanner'):
                    main_window.setup_scanner()

        except Exception as e:
            self.log(f"❌ Error ejecutando wizard: {e}")
            import traceback
            traceback.print_exc()
            # Intentar reconectar aunque haya fallado
            if hasattr(main_window, 'setup_scanner'):
                main_window.setup_scanner()
    
    def import_szconfig(self):
        """Importar archivo .szconfig generado desde el front web"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar configuración de timing",
            "",
            "Sportler-Zeit Config (*.szconfig);;JSON (*.json);;Todos los archivos (*)"
        )
        if not path:
            return

        try:
            import json
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            required = ['api_url', 'event_id', 'token']
            missing = [k for k in required if not config.get(k)]
            if missing:
                QMessageBox.warning(self, "Archivo inválido",
                    f"El archivo no contiene los campos requeridos: {', '.join(missing)}")
                return

            # Guardar en timing_system_config.json
            self._save_cloud_config(config)

            # Actualizar UI
            self._apply_cloud_config_to_ui(config)

            self.log(f"✅ Config importada: {config['api_url']} | evento: {config['event_id']} | agente: {config.get('agent_name', '-')}")

            QMessageBox.information(self, "Config importada",
                f"Conexión configurada correctamente.\n\n"
                f"URL: {config['api_url']}\n"
                f"Evento: {config['event_id']}\n"
                f"Agente: {config.get('agent_name', '-')}\n\n"
                "Usá 'Probar conexión' para verificar.")

        except Exception as e:
            logger.error(f"Error importando .szconfig: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo leer el archivo:\n{e}")

    def sync_athletes_to_backend(self):
        """Subir atletas locales al backend para el live tracking"""
        import json, os, requests as req

        # 1. Leer config
        config_path = 'config/api_config.json'
        if not os.path.exists(config_path):
            QMessageBox.warning(self, "Sin configuración",
                "No hay configuración de backend.\n\n"
                "Importá un archivo .szconfig primero.")
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer api_config.json:\n{e}")
            return

        # Soporta estructura plana {api_url,...} o anidada {cloud: {...}} (szconfig importado)
        cloud = cfg.get('cloud', cfg)
        api_url  = cloud.get('api_url', '').rstrip('/').removesuffix('/api/v1')
        api_key  = cloud.get('api_key', '')
        event_id = cloud.get('event_id', '')

        if not api_url or not event_id:
            QMessageBox.warning(self, "Configuración incompleta",
                "Falta api_url o event_id en api_config.json.\n\n"
                "Importá un archivo .szconfig válido.")
            return

        # 2. Obtener atletas del race_manager (via main_window)
        from PyQt6.QtWidgets import QApplication
        main_window = None
        for w in QApplication.topLevelWidgets():
            if hasattr(w, 'race_manager'):
                main_window = w
                break

        if not main_window or not main_window.race_manager:
            QMessageBox.warning(self, "Sin datos", "No hay atletas cargados en el sistema.")
            return

        race_manager = main_window.race_manager
        all_distances = race_manager.get_all_distances()
        if not all_distances:
            QMessageBox.warning(self, "Sin atletas",
                "No hay atletas cargados.\n\nImportá atletas primero desde CSV o Web.")
            return

        # 3. Serializar atletas
        athletes_payload = []
        for dist in all_distances:
            for athlete in dist.participants:
                athletes_payload.append({
                    'bib_number':  athlete.bib_number,
                    'name':        athlete.name,
                    'distance_id': dist.distance_id,
                    'distance':    dist.name,
                    'gender':      athlete.gender or '',
                    'birth_date':  athlete.birth_date.isoformat() if athlete.birth_date else '',
                    'chip_id':     athlete.tag_id or '',
                    'team':        athlete.team or '',
                })

        if not athletes_payload:
            QMessageBox.warning(self, "Sin atletas", "No hay atletas para sincronizar.")
            return

        # 4. Confirmar
        reply = QMessageBox.question(self, "Sincronizar atletas",
            f"Se van a subir {len(athletes_payload)} atletas al backend.\n\n"
            f"URL: {api_url}\nEvento: {event_id}\n\n"
            f"¿Continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes)

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 5. POST al backend
        try:
            self.sync_athletes_btn.setEnabled(False)
            self.sync_athletes_btn.setText("Subiendo...")

            headers = {'Content-Type': 'application/json'}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

            url = f"{api_url}/api/v1/timing/events/{event_id}/athletes"
            resp = req.post(url, json={'athletes': athletes_payload}, headers=headers, timeout=30)

            if resp.status_code in (200, 201):
                data = resp.json()
                created = data.get('created', '?')
                updated = data.get('updated', '?')
                self.log(f"✅ Atletas sincronizados: {created} creados, {updated} actualizados")
                QMessageBox.information(self, "Sincronización exitosa",
                    f"✅ Atletas subidos al backend:\n\n"
                    f"• Creados: {created}\n"
                    f"• Actualizados: {updated}\n\n"
                    "El live tracking ya puede mostrar nombres y dorsales.")
            else:
                self.log(f"⚠️ Backend retornó {resp.status_code}: {resp.text[:200]}")
                QMessageBox.warning(self, "Respuesta inesperada",
                    f"El backend respondió con código {resp.status_code}.\n\n"
                    f"Detalle: {resp.text[:300]}")

        except req.exceptions.ConnectionError:
            QMessageBox.critical(self, "Sin conexión",
                "No se pudo conectar al backend.\n\nVerificá que el servicio esté disponible.")
            self.log("❌ Error de conexión al sincronizar atletas")
        except req.exceptions.Timeout:
            QMessageBox.critical(self, "Timeout", "La conexión tardó demasiado.\n\nIntentá de nuevo.")
            self.log("❌ Timeout al sincronizar atletas")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al sincronizar:\n{e}")
            self.log(f"❌ Error sincronizando atletas: {e}")
        finally:
            self.sync_athletes_btn.setEnabled(True)
            self.sync_athletes_btn.setText("☁️ Sincronizar atletas")

    def test_cloud_connection(self):
        """Probar conexión con el backend"""
        api_url = self.cloud_url_input.text().strip()
        token = self._get_saved_token()

        if not api_url or not token:
            QMessageBox.warning(self, "Sin config", "Primero importá un archivo .szconfig.")
            return

        try:
            import requests
            headers = {'Authorization': f'Bearer {token}'}
            # Usamos el health check del backend
            base_url = api_url.rstrip('/').replace('/api/v1', '')
            resp = requests.get(f"{base_url}/health", headers=headers, timeout=15)

            if resp.status_code in (200, 404):
                # 404 también es "backend respondió", puede que no tenga /health
                self.cloud_status_label.setText("🟢 Conectado")
                self.cloud_status_label.setStyleSheet("font-weight: bold; font-size: 13px; color: green;")
                self.log(f"✅ Backend responde: {resp.status_code}")
                QMessageBox.information(self, "Conexión OK", "El backend está accesible.")
            else:
                self.cloud_status_label.setText(f"🔴 Error {resp.status_code}")
                self.cloud_status_label.setStyleSheet("font-weight: bold; font-size: 13px; color: red;")
                self.log(f"⚠️ Backend retornó: {resp.status_code}")

        except Exception as e:
            self.cloud_status_label.setText("🔴 Sin conexión")
            self.cloud_status_label.setStyleSheet("font-weight: bold; font-size: 13px; color: red;")
            self.log(f"❌ Error de conexión: {e}")
            QMessageBox.warning(self, "Sin conexión", f"No se pudo conectar al backend:\n{e}")

    def _save_cloud_config(self, config: dict):
        """Guardar config cloud en config/api_config.json"""
        import json, os
        config_path = 'config/api_config.json'
        existing = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception:
                pass

        existing['cloud'] = {
            'api_url': config['api_url'],
            'event_id': config['event_id'],
            'agent_name': config.get('agent_name', ''),
            'api_key': config['token'],
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    def _load_cloud_config_from_file(self):
        """Cargar cloud config guardado al iniciar"""
        import json, os
        try:
            path = 'config/api_config.json'
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

    def _apply_cloud_config_to_ui(self, config: dict):
        """Actualizar widgets con la config cloud"""
        self.cloud_url_input.setText(config.get('api_url', ''))
        self.cloud_event_input.setText(config.get('event_id', ''))
        self.cloud_agent_input.setText(config.get('agent_name', ''))
        self.cloud_status_label.setText("🟡 Configurado (sin verificar)")
        self.cloud_status_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #b45309;")

    def _get_saved_token(self) -> str:
        """Obtener token guardado de la config"""
        import json, os
        try:
            with open('config/api_config.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('api_key', '')
        except Exception:
            return data.get('cloud', {}).get('api_key', '') or data.get('api_key', '')

    def get_timestamp(self):
        """Timestamp formateado"""
        return datetime.now().strftime('%H:%M:%S')