#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para wizard modular
test_wizard_modular.py
"""

import sys
import logging
from pathlib import Path

# Agregar paths necesarios
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QMessageBox

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Prueba el wizard modular"""
    logger.info("=" * 60)
    logger.info("TEST WIZARD MODULAR")
    logger.info("=" * 60)
    
    app = QApplication(sys.argv)
    
    try:
        # Importar desde la ubicación correcta
        from src.gui.wizard import ConfigurationWizard
        from config import SystemConfig
        
        logger.info("✓ Importaciones exitosas")
        
        # Crear configuración
        config = SystemConfig()
        logger.info("✓ SystemConfig creado")
        
        # Crear wizard
        wizard = ConfigurationWizard(config)
        logger.info("✓ Wizard creado")
        
        # Mostrar wizard
        logger.info("Mostrando wizard...")
        result = wizard.exec()
        
        if result == wizard.DialogCode.Accepted:
            logger.info("✓ Wizard completado exitosamente")
            
            # Mostrar resumen
            QMessageBox.information(
                None,
                "Test exitoso",
                "El wizard se completó correctamente.\n\n"
                f"Antenas configuradas: {len(wizard.config.antennas)}"
            )
            
            # Mostrar configuración
            print("\n" + "=" * 60)
            print("CONFIGURACIÓN RESULTANTE")
            print("=" * 60)
            for port, antenna in wizard.config.antennas.items():
                if antenna.enabled:
                    print(f"Puerto {port}: {antenna.function.value} ({antenna.power_level}dBm)")
            
            return 0
        else:
            logger.info("Wizard cancelado")
            return 1
    
    except ImportError as e:
        logger.error(f"Error de importación: {e}")
        QMessageBox.critical(
            None,
            "Error de importación",
            f"No se pudieron importar los módulos necesarios:\n{str(e)}\n\n"
            "Verifica que la estructura de carpetas sea correcta."
        )
        return 1
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Error",
            f"Error ejecutando wizard:\n{str(e)}"
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())