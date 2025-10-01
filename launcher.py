#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanzador principal del sistema de cronometraje
launcher.py
"""

import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('timing_system.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Función principal del launcher"""
    logger.info("=" * 60)
    logger.info("SISTEMA DE CRONOMETRAJE RFID - LAUNCHER")
    logger.info("=" * 60)
    
    app = QApplication(sys.argv)
    
    try:
        from config import SystemConfig
        from src.gui.wizard import ConfigurationWizard
        
        config = SystemConfig()
        config_file = Path("timing_system_config.json")
        
        # Verificar si existe configuración
        if config_file.exists():
            logger.info("Configuración previa encontrada")
            
            reply = QMessageBox.question(
                None,
                "Configuración existente",
                "Se encontró una configuración previa.\n\n"
                "¿Desea usar la configuración existente y abrir la aplicación?\n\n"
                "Seleccione 'No' para reconfigurar el sistema.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Cargar configuración existente
                if config.load_from_file(str(config_file)):
                    logger.info("Configuración cargada exitosamente")
                    
                    # Lanzar aplicación principal directamente
                    return launch_main_application(config)
                else:
                    logger.warning("Error cargando configuración, ejecutando wizard")
        
        # Ejecutar wizard de configuración
        logger.info("Iniciando wizard de configuración")
        wizard = ConfigurationWizard(config)
        
        if wizard.exec() == wizard.DialogCode.Accepted:
            logger.info("Wizard completado exitosamente")
            
            # Lanzar aplicación principal
            return launch_main_application(wizard.config)
        else:
            logger.info("Configuración cancelada")
            return 1
    
    except Exception as e:
        logger.error(f"Error crítico: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Error crítico",
            f"Error crítico del sistema:\n{str(e)}"
        )
        return 1

def launch_main_application(config):
    """Lanza la aplicación principal de cronometraje"""
    logger.info("Lanzando aplicación principal...")
    
    try:
        # Importar tu ventana principal
        # Ajusta esta importación según tu estructura
        from src.gui.main_window import MainWindow

        
        # O si usas la interfaz con tabs:
        # from src.gui.tabbed_gui import TabbedGUI as MainWindow
        
        logger.info("Creando ventana principal...")
        main_window = MainWindow(config)
        main_window.show()
        
        logger.info("Aplicación principal iniciada")
        return main_window.exec()  # O app.exec() dependiendo de tu implementación
        
    except ImportError as e:
        logger.error(f"No se pudo importar la ventana principal: {e}")
        QMessageBox.critical(
            None,
            "Error de importación",
            "No se pudo iniciar la aplicación principal.\n"
            f"Error: {str(e)}\n\n"
            "Verifica que main_window.py o tabbed_gui.py existan en src/gui/"
        )
        return 1
    except Exception as e:
        logger.error(f"Error iniciando aplicación principal: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Error",
            f"Error iniciando la aplicación:\n{str(e)}"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())