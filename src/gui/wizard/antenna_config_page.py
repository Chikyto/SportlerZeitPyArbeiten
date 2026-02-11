#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Página de configuración de funciones de antenas
src/gui/wizard/antenna_config_page.py
"""

import logging
from PyQt6.QtWidgets import (
    QWizardPage, QVBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QCheckBox, QHeaderView,
    QMessageBox, QWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt

# Importar desde las carpetas correctas
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import AntennaConfig, AntennaFunction

logger = logging.getLogger(__name__)

class AntennaConfigurationPage(QWizardPage):
    """Página de configuración de antenas con múltiples funciones"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.antenna_checkboxes = {}
        self.function_checkboxes = {}  # Ahora múltiples funciones por antena
        
        self.setTitle("Configuración de Antenas")
        self.setSubTitle("Asigna funciones a las antenas conectadas")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Descripción
        desc = QLabel(
            "Configure las funciones de las antenas detectadas.\n\n"
            "⚠️ IMPORTANTE: Normalmente cada antena debe tener UNA SOLA función.\n"
            "• Puerto 1: Largada\n"
            "• Puertos intermedios: Checkpoints\n"
            "• Último puerto: Llegada"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Tabla de configuración
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(6)
        self.config_table.setHorizontalHeaderLabels([
            "Puerto", "Estado", "Usar", "Largada", "Checkpoint", "Llegada"
        ])
        header = self.config_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.config_table)
        
        self.setLayout(layout)
    
    def initializePage(self):
        """Se llama al entrar a la página"""
        wizard = self.wizard()
        if not wizard:
            return
        
        # Obtener resultados de detección de la página anterior
        detection_page = wizard.page(1)
        if not detection_page or not hasattr(detection_page, 'detection_results'):
            return
        
        detection_results = detection_page.detection_results
        
        self.config_table.setRowCount(8)
        self.antenna_checkboxes = {}
        self.function_checkboxes = {}
        
        for port in range(1, 9):
            if port in detection_results:
                connected, return_loss = detection_results[port]
                
                # Puerto
                self.config_table.setItem(port-1, 0, QTableWidgetItem(f"Puerto {port}"))
                
                # Estado
                if connected:
                    status_item = QTableWidgetItem(f"Conectada ({return_loss} dB)")
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                else:
                    status_item = QTableWidgetItem("No conectada")
                    status_item.setForeground(Qt.GlobalColor.gray)
                
                self.config_table.setItem(port-1, 1, status_item)
                
                if connected:
                    # Checkbox "Usar"
                    use_checkbox = QCheckBox()
                    use_checkbox.setChecked(True)
                    use_checkbox.stateChanged.connect(
                        lambda state, p=port: self.on_use_changed(p, state)
                    )
                    self.antenna_checkboxes[port] = use_checkbox
                    
                    use_widget = QWidget()
                    use_layout = QHBoxLayout(use_widget)
                    use_layout.addWidget(use_checkbox)
                    use_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    use_layout.setContentsMargins(0, 0, 0, 0)
                    self.config_table.setCellWidget(port-1, 2, use_widget)
                    
                    # Checkboxes de funciones
                    self.function_checkboxes[port] = {}
                    
                    for col, function in enumerate(['largada', 'checkpoint', 'llegada'], start=3):
                        func_checkbox = QCheckBox()

                        # Configuración inteligente por defecto: UNA función por antena
                        if port == 1 and function == 'largada':
                            # Primera antena: solo largada
                            func_checkbox.setChecked(True)
                        elif port > 1 and function == 'checkpoint':
                            # Otras antenas por defecto como checkpoint
                            func_checkbox.setChecked(True)
                        
                        func_checkbox.stateChanged.connect(self.on_config_changed)
                        self.function_checkboxes[port][function] = func_checkbox
                        
                        func_widget = QWidget()
                        func_layout = QHBoxLayout(func_widget)
                        func_layout.addWidget(func_checkbox)
                        func_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        func_layout.setContentsMargins(0, 0, 0, 0)
                        self.config_table.setCellWidget(port-1, col, func_widget)
                else:
                    # Antena no conectada - deshabilitar todo
                    for col in range(2, 6):
                        self.config_table.setItem(port-1, col, QTableWidgetItem("-"))
        
        self.completeChanged.emit()
    
    def on_use_changed(self, port, state):
        """Habilita/deshabilita funciones según checkbox 'Usar'"""
        enabled = (state == Qt.CheckState.Checked.value)
        
        if port in self.function_checkboxes:
            for func_cb in self.function_checkboxes[port].values():
                func_cb.setEnabled(enabled)
                if not enabled:
                    func_cb.setChecked(False)
        
        self.on_config_changed()
    
    def on_config_changed(self):
        """Maneja cambios en la configuración"""
        self.completeChanged.emit()
    
    def isComplete(self):
        """Determina si la página está completa"""
        # Obtener antenas habilitadas
        enabled_antennas = [
            port for port, cb in self.antenna_checkboxes.items() if cb.isChecked()
        ]
        
        if not enabled_antennas:
            return False
        
        # Verificar que al menos haya una función de largada
        has_largada = False
        for port in enabled_antennas:
            if port in self.function_checkboxes:
                if self.function_checkboxes[port].get('largada', None):
                    if self.function_checkboxes[port]['largada'].isChecked():
                        has_largada = True
                        break
        
        return has_largada
    
    def validatePage(self):
        """Validación al intentar avanzar"""
        enabled_antennas = [
            port for port, cb in self.antenna_checkboxes.items() if cb.isChecked()
        ]
        
        if not enabled_antennas:
            QMessageBox.warning(self, "Sin antenas", "Debe habilitar al menos una antena")
            return False
        
        # Verificar funciones
        has_largada = False
        has_llegada = False
        
        for port in enabled_antennas:
            if port in self.function_checkboxes:
                if self.function_checkboxes[port]['largada'].isChecked():
                    has_largada = True
                if self.function_checkboxes[port]['llegada'].isChecked():
                    has_llegada = True
        
        if not has_largada:
            QMessageBox.warning(
                self, "Función requerida",
                "Debe configurar al menos una función de 'largada'"
            )
            return False
        
        if not has_llegada:
            reply = QMessageBox.question(
                self, "Advertencia",
                "No hay función de 'llegada' configurada.\n"
                "¿Desea continuar de todos modos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            return reply == QMessageBox.StandardButton.Yes
        
        return True
    
    def get_configuration(self):
        """Obtiene la configuración final de antenas con múltiples funciones"""
        antenna_configs = {}
        
        for port, checkbox in self.antenna_checkboxes.items():
            if checkbox.isChecked():
                # Obtener todas las funciones seleccionadas para esta antena
                functions = []
                if port in self.function_checkboxes:
                    for func_name, func_cb in self.function_checkboxes[port].items():
                        if func_cb.isChecked():
                            functions.append(func_name)
                
                # Crear descripción con todas las funciones
                func_str = " + ".join(functions) if functions else "sin función"
                
                # Por ahora guardamos la primera función en el objeto
                # pero la descripción tiene todas
                primary_function = functions[0] if functions else "checkpoint"
                
                antenna_configs[port] = AntennaConfig(
                    port=port,
                    enabled=True,
                    function=AntennaFunction(primary_function),
                    power_level=25,
                    description=f"Antena puerto {port}: {func_str}"
                )
                
                # Agregar metadata de funciones múltiples
                antenna_configs[port].multiple_functions = functions
        
        return antenna_configs