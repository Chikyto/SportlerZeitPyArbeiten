"""
Punto de entrada con wizard automático
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.gui.wizard.auto_wizard import AutoConfigurationWizard
from src.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Usar wizard automático
    wizard = AutoConfigurationWizard()
    
    if wizard.exec():
        wizard_config = wizard.get_configuration()
        
        print("=== Configuración Completada ===")
        print(f"Antenas configuradas: {len(wizard_config.get('antennas', {}))}")
        print("================================")
        
        main_window = MainWindow(wizard_config=wizard_config)
        main_window.show()
        
        sys.exit(app.exec())
    else:
        print("Configuración cancelada")
        sys.exit(0)


if __name__ == '__main__':
    main()