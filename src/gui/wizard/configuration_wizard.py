#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wizard principal de configuración - Versión modular
src/gui/wizard/configuration_wizard.py
"""

import logging
from PyQt6.QtWidgets import QWizard, QMessageBox

# Importar desde las carpetas correctas
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import SystemConfig
from hardware import ReaderManager

# Importar páginas del wizard
from .connection_page import ConnectionPage
from .antenna_detection_page import AntennaDetectionPage
from .antenna_config_page import AntennaConfigurationPage
from .summary_page import SummaryPage

logger = logging.getLogger(__name__)

class ConfigurationWizard(QWizard):
    """Wizard de configuración del sistema - Versión modular"""
    
    def __init__(self, config: SystemConfig = None, parent=None):
        super().__init__(parent)
        
        # Configuración
        self.config = config or SystemConfig()
        
        # Reader manager
        self.reader_manager = ReaderManager(self.config.reader)
        
        # Configurar wizard
        self.setWindowTitle("Configuración - Sistema de Cronometraje RFID")
        self.resize(800, 600)
        
        # Estilo del wizard
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        
        # Agregar páginas
        self.addPage(ConnectionPage(self))
        self.addPage(AntennaDetectionPage(self))
        self.addPage(AntennaConfigurationPage(self))
        self.addPage(SummaryPage(self))
        
        logger.info("Wizard de configuración inicializado")
    
    def accept(self):
        """Se llama cuando se completa el wizard"""
        try:
            # Obtener configuración final
            config_page = self.page(2)  # Página de configuración
            if config_page and hasattr(config_page, 'get_configuration'):
                antenna_config = config_page.get_configuration()
                self.config.antennas = antenna_config
                
                # Guardar configuración automáticamente
                filename = "timing_system_config.json"
                if self.config.save_to_file(filename):
                    logger.info(f"Configuración guardada en {filename}")
                
                logger.info("Configuración del wizard completada")
                logger.info(f"Antenas configuradas: {len(antenna_config)}")
                
                for port, config in antenna_config.items():
                    functions = getattr(config, 'multiple_functions', [])
                    logger.info(f"  Puerto {port}: {', '.join(functions)}")
            
            super().accept()
            
        except Exception as e:
            logger.error(f"Error finalizando wizard: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al finalizar configuración:\n{str(e)}"
            )
    
    def reject(self):
        """Se llama cuando se cancela el wizard"""
        reply = QMessageBox.question(
            self,
            "Cancelar configuración",
            "¿Está seguro que desea cancelar la configuración?\n"
            "Se perderá el progreso actual.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("Wizard cancelado por el usuario")
            super().reject()

    def get_configuration(self):
        """Obtener configuración del wizard en formato compatible"""
        config = {
            'connection': {
                'host': getattr(self.config.reader, 'host', '192.168.0.178'),
                'port': getattr(self.config.reader, 'port', 4001),
                'verified': True
            },
            'antennas': {}
        }
        
        antenna_page = self.page(2)
        if antenna_page and hasattr(antenna_page, 'get_configuration'):
            antenna_configs = antenna_page.get_configuration()
            
            for port, antenna_config in antenna_configs.items():
                antenna_index = port - 1  # Convertir puerto 1-8 a índice 0-7
                functions = getattr(antenna_config, 'multiple_functions', [])
                description = getattr(antenna_config, 'description', f'Antena puerto {port}')
                
                if ':' in description:
                    name = description.split(':', 1)[1].strip()
                else:
                    name = f'Puerto {port}'
                
                # IMPORTANTE: usar antenna_index (int) como key, no string
                config['antennas'][antenna_index] = {  # <-- antenna_index, no str(antenna_index)
                    'enabled': True,
                    'name': name,
                    'description': description,
                    'start': 'largada' in functions,
                    'finish': 'llegada' in functions,
                    'checkpoint': 'checkpoint' in functions,
                    'power_level': getattr(antenna_config, 'power_level', 25),
                    'functions': functions
                }
        
        return config