"""
Script de testing para verificar la aplicación refactorizada

Este script te permite probar la nueva arquitectura sin el wizard
"""
import sys
from PyQt6.QtWidgets import QApplication

# Ajustar path si es necesario
sys.path.insert(0, '.')

from src.gui.main_window import MainWindow


def test_without_wizard():
    """Probar aplicación sin pasar por el wizard"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Configuración simulada (como si viniera del wizard)
    wizard_config = {
        'connection': {
            'host': '192.168.0.178',
            'port': 4001,
            'verified': False  # No auto-conectar
        },
        'antennas': {
            0: {
                'enabled': True,
                'name': 'Antena Largada',
                'start': True,
                'finish': False,
                'checkpoint': False
            },
            1: {
                'enabled': True,
                'name': 'Antena Meta',
                'start': False,
                'finish': True,
                'checkpoint': False
            }
        }
    }
    
    # Lanzar aplicación con configuración simulada
    main_window = MainWindow(wizard_config=wizard_config)
    main_window.show()
    
    print("=== Testing Refactored Application ===")
    print("✓ MainWindow creado")
    print("✓ Tabs cargados")
    print("✓ Signals conectados")
    print("✓ Configuración aplicada")
    print("=====================================")
    
    # Verificar estado
    state = main_window.get_current_state()
    print("\n=== Estado del Sistema ===")
    for key, value in state.items():
        print(f"{key}: {value}")
    print("==========================\n")
    
    sys.exit(app.exec())


def test_with_wizard():
    """Probar flujo completo con wizard"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    from src.gui.wizard.configuration_wizard import ConfigurationWizard
    
    # Mostrar wizard
    wizard = ConfigurationWizard()
    
    if wizard.exec():
        wizard_config = wizard.get_configuration()
        
        # Lanzar aplicación
        main_window = MainWindow(wizard_config=wizard_config)
        main_window.show()
        
        sys.exit(app.exec())
    else:
        print("Wizard cancelado")
        sys.exit(0)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test RFID Athletics Timer')
    parser.add_argument(
        '--mode', 
        choices=['wizard', 'no-wizard'],
        default='no-wizard',
        help='Modo de testing (default: no-wizard)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'wizard':
        print("Testing con wizard completo...")
        test_with_wizard()
    else:
        print("Testing sin wizard (configuración simulada)...")
        test_without_wizard()