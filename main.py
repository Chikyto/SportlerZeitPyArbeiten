"""
Punto de entrada principal de la aplicación RFID Athletics Timer

Flujo:
1. Mostrar wizard de configuración inicial
2. Si el wizard se completa exitosamente, lanzar la aplicación principal
3. Si el wizard se cancela, salir de la aplicación
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.gui.wizard.configuration_wizard import ConfigurationWizard
from src.gui.main_window import MainWindow


def main():
    """Función principal de la aplicación"""
    app = QApplication(sys.argv)
    
    # Configurar estilo de la aplicación
    app.setStyle('Fusion')
    
    # Paso 1: Mostrar wizard de configuración
    wizard = ConfigurationWizard()
    
    if wizard.exec():
        # Wizard completado exitosamente
        wizard_config = wizard.get_configuration()
        
        print("=== Configuración del Wizard ===")
        print(f"Conexión verificada: {wizard_config.get('connection', {}).get('verified', False)}")
        print(f"Antenas configuradas: {len(wizard_config.get('antennas', {}))}")
        print("================================")
        
        # Paso 2: Lanzar aplicación principal con configuración
        main_window = MainWindow(wizard_config=wizard_config)
        main_window.show()
        
        # Ejecutar aplicación
        sys.exit(app.exec())
    else:
        # Wizard cancelado
        print("Configuración cancelada por el usuario")
        sys.exit(0)


if __name__ == '__main__':
    main()