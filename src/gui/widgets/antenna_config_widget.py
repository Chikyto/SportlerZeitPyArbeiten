from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QGroupBox, QLineEdit, QCheckBox, QGridLayout)
from PyQt6.QtCore import pyqtSignal

class AntennaConfigWidget(QWidget):
    """Widget para configuración de antenas - separado del archivo principal"""
    
    # Señal para comunicar cambios al widget principal
    config_applied = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.antenna_configs = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interfaz del widget"""
        layout = QVBoxLayout(self)
        
        # Información del setup
        info_group = QGroupBox("Configuración del Setup de Antenas")
        info_layout = QVBoxLayout(info_group)
        
        setup_info = QLabel(
            "Define el rol de cada antena según tu setup físico.\n"
            "Las antenas pueden cumplir múltiples roles (ej: Largada+Meta en circuitos cerrados).\n"
            "Puedes usar desde 1 hasta 8 antenas en cualquier configuración."
        )
        setup_info.setStyleSheet("font-style: italic; padding: 10px;")
        info_layout.addWidget(setup_info)
        
        layout.addWidget(info_group)
        
        # Configuración individual de antenas con GRID LAYOUT
        antennas_group = QGroupBox("Configuración Individual de Antenas")
        antennas_layout = QVBoxLayout(antennas_group)
        
        # Crear grid para alineación correcta
        self.antennas_grid = QGridLayout()
        
        # Headers
        headers = ["Antena", "Habilitada", "Largada", "Meta", "Checkpoint", "Nombre", "Descripción"]
        for col, header in enumerate(headers):
            header_label = QLabel(header)
            header_label.setStyleSheet("font-weight: bold; padding: 5px;")
            self.antennas_grid.addWidget(header_label, 0, col)
        
        # Configuración para cada antena (hasta 8)
        for antenna_id in range(8):
            row = antenna_id + 1  # +1 porque la fila 0 son los headers
            
            # Columna 0: ID de antena
            antenna_label = QLabel(f"Ant {antenna_id + 1}")
            self.antennas_grid.addWidget(antenna_label, row, 0)
            
            # Columna 1: Checkbox habilitada
            enabled_checkbox = QCheckBox()
            enabled_checkbox.setChecked(antenna_id < 4)  # Primeras 4 habilitadas por defecto
            enabled_checkbox.stateChanged.connect(lambda state, aid=antenna_id: self.on_antenna_enabled_changed(aid, state))
            self.antennas_grid.addWidget(enabled_checkbox, row, 1)
            
            # Columna 2: Checkbox Largada
            start_checkbox = QCheckBox()
            if antenna_id == 0:  # Antena 1 como largada por defecto
                start_checkbox.setChecked(True)
            start_checkbox.stateChanged.connect(self.validate_antenna_config)
            self.antennas_grid.addWidget(start_checkbox, row, 2)
            
            # Columna 3: Checkbox Meta
            finish_checkbox = QCheckBox()
            if antenna_id == 1:  # Antena 2 como meta por defecto
                finish_checkbox.setChecked(True)
            finish_checkbox.stateChanged.connect(self.validate_antenna_config)
            self.antennas_grid.addWidget(finish_checkbox, row, 3)
            
            # Columna 4: Checkbox Checkpoint
            checkpoint_checkbox = QCheckBox()
            checkpoint_checkbox.stateChanged.connect(self.validate_antenna_config)
            self.antennas_grid.addWidget(checkpoint_checkbox, row, 4)
            
            # Columna 5: Nombre
            name_input = QLineEdit()
            default_names = ["Largada", "Meta", f"Control {antenna_id-1}", f"Control {antenna_id-1}"]
            if antenna_id < 4:
                name_input.setText(default_names[antenna_id])
            else:
                name_input.setText(f"Antena {antenna_id + 1}")
            name_input.setMaximumWidth(150)
            self.antennas_grid.addWidget(name_input, row, 5)
            
            # Columna 6: Descripción
            desc_input = QLineEdit()
            default_descs = ["Línea de largada", "Línea de meta", "Punto de control", "Punto de control"]
            if antenna_id < 4:
                desc_input.setText(default_descs[antenna_id])
            else:
                desc_input.setText("Sin configurar")
            self.antennas_grid.addWidget(desc_input, row, 6)
            
            # Guardar referencias
            self.antenna_configs[antenna_id] = {
                'enabled': enabled_checkbox,
                'start': start_checkbox,
                'finish': finish_checkbox,
                'checkpoint': checkpoint_checkbox,
                'name': name_input,
                'description': desc_input
            }
        
        antennas_layout.addLayout(self.antennas_grid)
        layout.addWidget(antennas_group)
        
        # Configuraciones predefinidas
        presets_group = QGroupBox("Configuraciones Predefinidas")
        presets_layout = QVBoxLayout(presets_group)
        
        presets_buttons_layout = QHBoxLayout()
        
        self.preset_simple_btn = QPushButton("Setup Simple")
        self.preset_simple_btn.clicked.connect(self.apply_simple_preset)
        presets_buttons_layout.addWidget(self.preset_simple_btn)
        
        self.preset_circuit_btn = QPushButton("Circuito Cerrado")
        self.preset_circuit_btn.clicked.connect(self.apply_circuit_preset)
        presets_buttons_layout.addWidget(self.preset_circuit_btn)
        
        self.preset_finish_line_btn = QPushButton("Arco de Meta")
        self.preset_finish_line_btn.clicked.connect(self.apply_finish_line_preset)
        presets_buttons_layout.addWidget(self.preset_finish_line_btn)
        
        self.preset_start_finish_btn = QPushButton("Arco Largada+Meta")
        self.preset_start_finish_btn.clicked.connect(self.apply_start_finish_preset)
        presets_buttons_layout.addWidget(self.preset_start_finish_btn)

        self.preset_laps_btn = QPushButton("🔄 Vueltas (1 Antena)")
        self.preset_laps_btn.clicked.connect(self.apply_laps_preset)
        self.preset_laps_btn.setToolTip("Carrera por vueltas: 1 antena para largada + vueltas + meta (ej: 7km/hora)")
        self.preset_laps_btn.setStyleSheet("background-color: #f59e0b; color: white; font-weight: bold;")
        presets_buttons_layout.addWidget(self.preset_laps_btn)

        presets_layout.addLayout(presets_buttons_layout)
        
        # Descripción del preset seleccionado
        self.preset_description = QLabel("Selecciona un preset para configuración automática")
        self.preset_description.setStyleSheet("font-style: italic; color: gray; padding: 5px;")
        presets_layout.addWidget(self.preset_description)
        
        layout.addWidget(presets_group)
        
        # Validación y estado
        validation_group = QGroupBox("Estado de Configuración")
        validation_layout = QVBoxLayout(validation_group)
        
        self.config_status = QLabel("Configuración válida")
        self.config_status.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
        validation_layout.addWidget(self.config_status)
        
        # Botón para aplicar configuración
        apply_layout = QHBoxLayout()
        
        self.apply_config_btn = QPushButton("Aplicar Configuración")
        self.apply_config_btn.clicked.connect(self.apply_antenna_config)
        self.apply_config_btn.setStyleSheet("background-color: blue; color: white; font-weight: bold; padding: 8px;")
        apply_layout.addWidget(self.apply_config_btn)
        
        self.validate_config_btn = QPushButton("Validar Setup")
        self.validate_config_btn.clicked.connect(self.validate_antenna_config)
        apply_layout.addWidget(self.validate_config_btn)
        
        validation_layout.addLayout(apply_layout)
        layout.addWidget(validation_group)
        
        # Validación inicial
        self.validate_antenna_config()
        
    def on_antenna_enabled_changed(self, antenna_id, state):
        """Manejar cambio de estado de antena"""
        enabled = state == 2  # Qt.CheckState.Checked
        
        # Si se deshabilita, desmarcar todos los roles
        if not enabled:
            self.antenna_configs[antenna_id]['start'].setChecked(False)
            self.antenna_configs[antenna_id]['finish'].setChecked(False)
            self.antenna_configs[antenna_id]['checkpoint'].setChecked(False)
        
        self.validate_antenna_config()
    
    def apply_simple_preset(self):
        """Aplicar preset simple: Largada + Meta separadas"""
        self.preset_description.setText("Setup Simple: Antena 1 = Largada, Antena 2 = Meta")
        
        presets = [
            (True, True, False, False, "Largada", "Línea de largada"),
            (True, False, True, False, "Meta", "Línea de meta"),
            (False, False, False, False, "Antena 3", "Sin usar"),
            (False, False, False, False, "Antena 4", "Sin usar"),
        ]
        
        self._apply_preset(presets)
    
    def apply_circuit_preset(self):
        """Aplicar preset circuito cerrado: Misma antena para largada y meta"""
        self.preset_description.setText("Circuito Cerrado: Antena 1 = Largada+Meta, resto controles")
        
        presets = [
            (True, True, True, False, "Largada/Meta", "Línea de largada y meta"),
            (True, False, False, True, "Control 1", "Primer control"),
            (True, False, False, True, "Control 2", "Segundo control"),
            (False, False, False, False, "Antena 4", "Sin usar"),
        ]
        
        self._apply_preset(presets)
    
    def apply_finish_line_preset(self):
        """Aplicar preset arco de meta: 4 antenas solo como meta"""
        self.preset_description.setText("Arco de Meta: 4 antenas como línea de meta")
        
        presets = [
            (True, False, True, False, "Meta 1", "Posición 1 línea de meta"),
            (True, False, True, False, "Meta 2", "Posición 2 línea de meta"),
            (True, False, True, False, "Meta 3", "Posición 3 línea de meta"),
            (True, False, True, False, "Meta 4", "Posición 4 línea de meta")
        ]
        
        self._apply_preset(presets)
    
    def apply_start_finish_preset(self):
        """Aplicar preset arco largada+meta: 4 antenas para ambos roles"""
        self.preset_description.setText("Arco Largada+Meta: 4 antenas para largada Y meta")

        presets = [
            (True, True, True, False, "Largada/Meta 1", "Pos 1 - Largada y Meta"),
            (True, True, True, False, "Largada/Meta 2", "Pos 2 - Largada y Meta"),
            (True, True, True, False, "Largada/Meta 3", "Pos 3 - Largada y Meta"),
            (True, True, True, False, "Largada/Meta 4", "Pos 4 - Largada y Meta")
        ]

        self._apply_preset(presets)

    def apply_laps_preset(self):
        """
        Aplicar preset carrera por vueltas: 1 antena para largada+vueltas+meta

        Ideal para carreras de resistencia por tiempo (ej: 7km/hora durante 6 horas)
        donde los atletas pasan múltiples veces por la misma antena
        """
        self.preset_description.setText(
            "🔄 Vueltas: 1 antena para START + VUELTAS + META | "
            "Ideal para carreras por tiempo (ej: 7km/hora)"
        )

        presets = [
            (True, True, True, False, "Largada/Vueltas/Meta", "Arco único - Cuenta todas las pasadas"),
            (False, False, False, False, "Antena 2", "Sin usar"),
            (False, False, False, False, "Antena 3", "Sin usar"),
            (False, False, False, False, "Antena 4", "Sin usar"),
        ]

        self._apply_preset(presets)
    
    def _apply_preset(self, presets):
        """Aplicar configuración preset"""
        for i, (enabled, start, finish, checkpoint, name, description) in enumerate(presets):
            if i < len(self.antenna_configs):
                self.antenna_configs[i]['enabled'].setChecked(enabled)
                self.antenna_configs[i]['start'].setChecked(start)
                self.antenna_configs[i]['finish'].setChecked(finish)
                self.antenna_configs[i]['checkpoint'].setChecked(checkpoint)
                self.antenna_configs[i]['name'].setText(name)
                self.antenna_configs[i]['description'].setText(description)
        
        # Deshabilitar antenas restantes
        for i in range(len(presets), 8):
            self.antenna_configs[i]['enabled'].setChecked(False)
            self.antenna_configs[i]['start'].setChecked(False)
            self.antenna_configs[i]['finish'].setChecked(False)
            self.antenna_configs[i]['checkpoint'].setChecked(False)
            self.antenna_configs[i]['name'].setText(f"Antena {i + 1}")
            self.antenna_configs[i]['description'].setText("Sin configurar")
        
        self.validate_antenna_config()
    
    def validate_antenna_config(self):
        """Validar configuración de antenas"""
        enabled_antennas = []
        start_antennas = []
        finish_antennas = []
        start_finish_antennas = []
        
        for antenna_id, config in self.antenna_configs.items():
            if config['enabled'].isChecked():
                enabled_antennas.append(antenna_id)
                
                is_start = config['start'].isChecked()
                is_finish = config['finish'].isChecked()
                
                if is_start:
                    start_antennas.append(antenna_id)
                if is_finish:
                    finish_antennas.append(antenna_id)
                if is_start and is_finish:
                    start_finish_antennas.append(antenna_id)
        
        # Validaciones
        errors = []
        
        if len(enabled_antennas) == 0:
            errors.append("Debe haber al menos una antena habilitada")
        
        if len(start_antennas) == 0:
            errors.append("Debe haber al menos una antena de largada")
        
        if len(finish_antennas) == 0:
            errors.append("Debe haber al menos una antena de meta")
        
        # Mostrar estado
        if errors:
            self.config_status.setText("⚠️ " + "; ".join(errors))
            self.config_status.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
            self.apply_config_btn.setEnabled(False)
        else:
            status_parts = [f"✓ {len(enabled_antennas)} antenas"]
            if len(start_finish_antennas) > 0:
                status_parts.append(f"{len(start_finish_antennas)} largada+meta")
            
            self.config_status.setText("; ".join(status_parts))
            self.config_status.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
            self.apply_config_btn.setEnabled(True)
    
    def apply_antenna_config(self):
        """Aplicar configuración de antenas al sistema"""
        config_data = {}
        
        for antenna_id, config in self.antenna_configs.items():
            if config['enabled'].isChecked():
                config_data[antenna_id] = {
                    'enabled': True,
                    'start': config['start'].isChecked(),
                    'finish': config['finish'].isChecked(),
                    'checkpoint': config['checkpoint'].isChecked(),
                    'name': config['name'].text(),
                    'description': config['description'].text()
                }
        
        # Emitir señal con la configuración
        self.config_applied.emit(config_data)

    def load_from_wizard_config(self, wizard_config):
        """Cargar configuración desde el wizard"""
        print(f"\n{'='*60}")
        print(f"DEBUG: load_from_wizard_config iniciado")
        print(f"{'='*60}")
        
        for antenna_id in range(8):
            if antenna_id not in self.antenna_configs:
                continue
                
            controls = self.antenna_configs[antenna_id]
            
            # Bloquear señales temporalmente
            for control in controls.values():
                if hasattr(control, 'blockSignals'):
                    control.blockSignals(True)
            
            if antenna_id in wizard_config:
                config = wizard_config[antenna_id]
                
                print(f"\nAntena {antenna_id}:")
                print(f"  Config: {config}")
                
                # Forzar estado de checkboxes usando setCheckState
                from PyQt6.QtCore import Qt
                
                enabled = config.get('enabled', False)
                start = config.get('start', False)
                finish = config.get('finish', False)
                checkpoint = config.get('checkpoint', False)
                
                print(f"  Valores a aplicar: E={enabled}, S={start}, F={finish}, C={checkpoint}")
                
                # Aplicar estados
                controls['enabled'].setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
                controls['start'].setCheckState(Qt.CheckState.Checked if start else Qt.CheckState.Unchecked)
                controls['finish'].setCheckState(Qt.CheckState.Checked if finish else Qt.CheckState.Unchecked)
                controls['checkpoint'].setCheckState(Qt.CheckState.Checked if checkpoint else Qt.CheckState.Unchecked)
                
                # Textos
                controls['name'].setText(config.get('name', f'Antena {antenna_id + 1}'))
                controls['description'].setText(config.get('description', 'Sin configurar'))
                
                print(f"  Estados aplicados: E={controls['enabled'].isChecked()}, "
                    f"S={controls['start'].isChecked()}, "
                    f"F={controls['finish'].isChecked()}, "
                    f"C={controls['checkpoint'].isChecked()}")
            else:
                # Desmarcar antenas no configuradas
                from PyQt6.QtCore import Qt
                controls['enabled'].setCheckState(Qt.CheckState.Unchecked)
                controls['start'].setCheckState(Qt.CheckState.Unchecked)
                controls['finish'].setCheckState(Qt.CheckState.Unchecked)
                controls['checkpoint'].setCheckState(Qt.CheckState.Unchecked)
            
            # Desbloquear señales
            for control in controls.values():
                if hasattr(control, 'blockSignals'):
                    control.blockSignals(False)
        
        # Forzar actualización visual
        self.update()
        self.repaint()
        
        # Agregar botón de editar si no existe
        if not hasattr(self, 'edit_antenna_config_btn'):
            self.add_edit_button()
        
        # Validar después de cargar todo
        self.validate_antenna_config()
        
        self.is_wizard_configured = True
        print(f"\n{'='*60}")
        print("DEBUG: load_from_wizard_config completado")
        print(f"{'='*60}\n")


    def add_edit_button(self):
        """Agregar botón para editar configuración en la parte superior"""
        from PyQt6.QtWidgets import QFrame
        
        # Crear frame para el banner
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border: 2px solid #4caf50;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        banner_layout = QHBoxLayout(banner)
        
        # Label de estado
        self.antenna_config_status = QLabel("⚙️ Configuración cargada desde el wizard")
        self.antenna_config_status.setStyleSheet("color: #2e7d32; font-weight: bold;")
        banner_layout.addWidget(self.antenna_config_status)
        
        banner_layout.addStretch()
        
        # Botón de editar
        self.edit_antenna_config_btn = QPushButton("✏️ Editar Configuración")
        self.edit_antenna_config_btn.clicked.connect(self.toggle_antenna_edit_mode)
        self.edit_antenna_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        banner_layout.addWidget(self.edit_antenna_config_btn)
        
        # Insertar banner al principio del layout
        self.layout().insertWidget(0, banner)


    def toggle_antenna_edit_mode(self):
        """Alternar modo de edición de antenas"""
        if not hasattr(self, 'antenna_edit_mode'):
            self.antenna_edit_mode = False
        
        self.antenna_edit_mode = not self.antenna_edit_mode
        
        if self.antenna_edit_mode:
            # Habilitar edición
            self.edit_antenna_config_btn.setText("💾 Guardar Cambios")
            self.edit_antenna_config_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f57c00;
                    color: white;
                    font-weight: bold;
                    padding: 8px 15px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #ef6c00;
                }
            """)
            self.antenna_config_status.setText("✏️ Modo edición activado")
            self.antenna_config_status.setStyleSheet("color: #f57c00; font-weight: bold;")
            
            # Habilitar todos los controles
            self.enable_all_controls(True)
        else:
            # Deshabilitar edición
            self.edit_antenna_config_btn.setText("✏️ Editar Configuración")
            self.edit_antenna_config_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1976d2;
                    color: white;
                    font-weight: bold;
                    padding: 8px 15px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
            self.antenna_config_status.setText("⚙️ Configuración guardada")
            self.antenna_config_status.setStyleSheet("color: #2e7d32; font-weight: bold;")
            
            # Deshabilitar controles
            self.enable_all_controls(False)
            
            # Emitir señal de configuración actualizada
            self.apply_antenna_config()


    def enable_all_controls(self, enabled):
        """Habilitar/deshabilitar todos los controles de edición"""
        for antenna_id, controls in self.antenna_configs.items():
            # Campos de texto
            controls['name'].setReadOnly(not enabled)
            controls['description'].setReadOnly(not enabled)
            
            # Checkboxes
            controls['enabled'].setEnabled(enabled)
            
            # Roles solo si la antena está habilitada
            is_enabled = controls['enabled'].isChecked()
            controls['start'].setEnabled(enabled and is_enabled)
            controls['finish'].setEnabled(enabled and is_enabled)
            controls['checkpoint'].setEnabled(enabled and is_enabled)


    def get_current_config(self):
        """Obtener configuración actual"""
        config_data = {}
        
        for antenna_id, config in self.antenna_configs.items():
            config_data[antenna_id] = {
                'enabled': config['enabled'].isChecked(),
                'start': config['start'].isChecked(),
                'finish': config['finish'].isChecked(),
                'checkpoint': config['checkpoint'].isChecked(),
                'name': config['name'].text(),
                'description': config['description'].text()
            }
        
        return config_data