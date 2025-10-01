#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Página final con resumen de configuración
src/gui/wizard/summary_page.py
"""

import logging
from PyQt6.QtWidgets import (
    QWizardPage, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QGroupBox, QMessageBox
)
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)

class SummaryPage(QWizardPage):
    """Página final con resumen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setTitle("Configuración Completa")
        self.setSubTitle("Resumen y finalización")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("¡Sistema configurado correctamente!")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # Resumen
        summary_group = QGroupBox("Resumen de Configuración")
        summary_layout = QVBoxLayout()
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Botón guardar
        self.save_button = QPushButton("Guardar Configuración")
        self.save_button.clicked.connect(self.save_config)
        layout.addWidget(self.save_button)
        
        self.setLayout(layout)
    
    def initializePage(self):
        """Se llama al entrar a la página"""
        summary = self.create_summary()
        self.summary_text.setPlainText(summary)
    
    def create_summary(self):
        """Crea el resumen de configuración"""
        wizard = self.wizard()
        if not wizard:
            return "Error: No se pudo acceder al wizard"
        
        lines = []
        lines.append("=" * 60)
        lines.append("CONFIGURACIÓN DEL SISTEMA DE CRONOMETRAJE RFID")
        lines.append("=" * 60)
        lines.append("")
        
        # Información del reader
        if hasattr(wizard, 'reader_manager'):
            rm = wizard.reader_manager
            lines.append("LECTOR YR8900:")
            lines.append(f"  • Dirección IP: {rm.config.host}:{rm.config.port}")
            lines.append(f"  • Firmware: v{rm.firmware_version}")
            lines.append(f"  • Estado: Conectado y operativo")
            lines.append("")
        
        # Antenas configuradas
        config_page = wizard.page(2)
        if config_page and hasattr(config_page, 'get_configuration'):
            antenna_configs = config_page.get_configuration()
            
            lines.append(f"ANTENAS CONFIGURADAS ({len(antenna_configs)}):")
            
            # Mostrar cada antena con sus funciones
            for port in sorted(antenna_configs.keys()):
                config = antenna_configs[port]
                functions = getattr(config, 'multiple_functions', [config.function.value])
                func_str = " + ".join(functions)
                lines.append(f"  • Puerto {port}: {func_str}")
        
        lines.append("")
        lines.append("=" * 60)
        lines.append("El sistema está listo para iniciar el cronometraje")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def save_config(self):
        """Guarda la configuración"""
        wizard = self.wizard()
        if not wizard:
            return
        
        try:
            config_page = wizard.page(2)
            if not config_page:
                raise Exception("No se pudo acceder a la página de configuración")
            
            antenna_config = config_page.get_configuration()
            wizard.config.antennas = antenna_config
            
            filename = "timing_system_config.json"
            if wizard.config.save_to_file(filename):
                QMessageBox.information(
                    self,
                    "Configuración guardada",
                    f"La configuración se guardó exitosamente en:\n{filename}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Error al guardar la configuración"
                )
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al guardar configuración:\n{str(e)}"
            )