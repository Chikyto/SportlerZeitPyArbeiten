#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wizard principal de configuración - Versión modular CORREGIDA
src/gui/wizard/configuration_wizard.py
"""

import logging
from PyQt6.QtWidgets import QWizard, QMessageBox
from PyQt6.QtCore import pyqtSignal

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config import SystemConfig
from hardware import ReaderManager

from .connection_page import ConnectionPage
from .antenna_detection_page import AntennaDetectionPage
from .antenna_config_page import AntennaConfigurationPage
from .summary_page import SummaryPage

logger = logging.getLogger(__name__)

class ConfigurationWizard(QWizard):
    """Wizard de configuración del sistema - Versión modular"""
    
    # 🔥 SEÑAL CRÍTICA: emite configuración al finalizar
    configuration_completed = pyqtSignal(dict)
    
    def __init__(self, config: SystemConfig = None, parent=None):
        super().__init__(parent)
        
        self.config = config or SystemConfig()
        self.reader_manager = ReaderManager(self.config.reader)
        
        self.setWindowTitle("Configuración - Sistema de Cronometraje RFID")
        self.resize(800, 600)
        
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
            # 1. Obtener configuración final
            config_page = self.page(2)
            if config_page and hasattr(config_page, 'get_configuration'):
                antenna_config = config_page.get_configuration()
                self.config.antennas = antenna_config
                
                # 2. Guardar configuración automáticamente
                filename = "timing_system_config.json"
                if self.config.save_to_file(filename):
                    logger.info(f"✅ Configuración guardada en {filename}")
                
                # Log de debug
                logger.info("✅ Configuración del wizard completada")
                logger.info(f"📡 Antenas configuradas: {len(antenna_config)}")
                for port, config in antenna_config.items():
                    functions = getattr(config, 'multiple_functions', [])
                    logger.info(f"  Puerto {port}: {', '.join(functions)}")
                
                # 3. 🔥 EMITIR SEÑAL con configuración completa
                full_config = self.get_configuration()
                logger.info(f"🔔 Emitiendo configuración: {list(full_config['antennas'].keys())}")
                self.configuration_completed.emit(full_config)
            
            super().accept()
            
        except Exception as e:
            logger.error(f"❌ Error finalizando wizard: {e}")
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
        """
        🔥 CRÍTICO: Obtener configuración en formato estandarizado
        Usar SIEMPRE puertos 1-8 como keys (no índices 0-7)
        """
        config = {
            'connection': {
                'host': getattr(self.config.reader, 'host', '192.168.0.178'),
                'port': getattr(self.config.reader, 'port', 4001),
                'verified': True
            },
            'power_dbm': 30,  # Potencia por defecto
            'antennas': {}
        }
        
        antenna_page = self.page(2)
        if antenna_page and hasattr(antenna_page, 'get_configuration'):
            antenna_configs = antenna_page.get_configuration()
            
            for port, antenna_config in antenna_configs.items():
                # 🔥 port ya es 1-8, NO convertir
                functions = getattr(antenna_config, 'multiple_functions', [])
                description = getattr(antenna_config, 'description', f'Antena puerto {port}')
                
                # Extraer nombre limpio
                if ':' in description:
                    name = description.split(':', 1)[1].strip()
                else:
                    name = f'Antena {port}'
                
                # 🔥 KEY = puerto (1-8), NO índice (0-7)
                config['antennas'][port] = {
                    'enabled': True,
                    'name': name,
                    'description': description,
                    'start': 'largada' in functions,
                    'finish': 'llegada' in functions,
                    'checkpoint': 'checkpoint' in functions,
                    'power_level': getattr(antenna_config, 'power_level', 25),
                    'functions': functions
                }
        
        logger.info(f"📡 Configuración generada con puertos: {list(config['antennas'].keys())}")
        return config