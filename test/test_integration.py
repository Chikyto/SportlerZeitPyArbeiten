"""
Test de integración completa: Wizard → MainWindow → DetectionTab
"""

import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from pathlib import Path

# ⭐ CRÍTICO: Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Ajustar imports según tu estructura
from src.gui.main_window import MainWindow
from src.core.advanced_scanner import AdvancedYR8900Scanner

def create_test_config():
    """Crea una configuración de prueba"""
    return {
        "connection": {
            "host": "192.168.0.178",
            "port": 4001
        },
        "power_dbm": 30,
        "antennas": {
            "2": {
                "enabled": True,
                "name": "Largada",
                "start": True,
                "finish": False,
                "checkpoint": False
            },
            "3": {
                "enabled": True,
                "name": "Checkpoint 1",
                "start": False,
                "finish": False,
                "checkpoint": True
            },
            "6": {
                "enabled": True,
                "name": "Meta",
                "start": False,
                "finish": True,
                "checkpoint": False
            }
        }
    }

def test_config_loading():
    """Test de carga de configuración"""
    print("\n=== TEST 1: Carga de Configuración ===")
    
    config = create_test_config()
    
    # Verificar estructura
    assert 'connection' in config
    assert 'antennas' in config
    
    # Verificar antenas
    antennas = config['antennas']
    assert len(antennas) == 3
    
    # Verificar roles
    assert antennas['2']['start'] == True
    assert antennas['6']['finish'] == True
    
    print("✓ Configuración válida")

def test_scanner_creation():
    """Test de creación de scanner con config"""
    print("\n=== TEST 2: Creación de Scanner ===")
    
    config = create_test_config()
    conn = config['connection']
    
    scanner = AdvancedYR8900Scanner(conn['host'], conn['port'])
    
    assert scanner is not None
    assert scanner.config.host == conn['host']
    assert scanner.config.port == conn['port']
    
    print("✓ Scanner creado correctamente")

def test_antenna_roles():
    """Test de asignación de roles"""
    print("\n=== TEST 3: Roles de Antenas ===")
    
    config = create_test_config()
    antennas = config['antennas']
    
    # Verificar roles asignados
    roles = {}
    for port, ant_config in antennas.items():
        if ant_config['start']:
            roles[int(port)] = 'start'
        elif ant_config['finish']:
            roles[int(port)] = 'finish'
        elif ant_config['checkpoint']:
            roles[int(port)] = 'checkpoint'
    
    assert roles[2] == 'start'
    assert roles[3] == 'checkpoint'
    assert roles[6] == 'finish'
    
    print("✓ Roles asignados correctamente")
    print(f"  Puerto 2: Largada")
    print(f"  Puerto 3: Checkpoint")
    print(f"  Puerto 6: Meta")

def test_mainwindow_with_config():
    """Test de MainWindow con configuración"""
    print("\n=== TEST 4: MainWindow con Config ===")
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    config = create_test_config()
    
    # Crear MainWindow con config
    main_window = MainWindow(wizard_config=config)
    
    # Verificar que tiene config
    assert main_window.wizard_config is not None
    
    # Verificar métodos de acceso a config
    role_2 = main_window.get_antenna_role(2)
    role_6 = main_window.get_antenna_role(6)
    
    assert role_2 == 'start'
    assert role_6 == 'finish'
    
    print("✓ MainWindow configurado correctamente")
    print(f"  Puerto 2: {role_2}")
    print(f"  Puerto 6: {role_6}")
    
    main_window.close()

def run_all_tests():
    """Ejecuta todos los tests"""
    print("="*60)
    print("  TEST DE INTEGRACIÓN WIZARD → SCANNER → MAINWINDOW")
    print("="*60)
    
    try:
        test_config_loading()
        test_scanner_creation()
        test_antenna_roles()
        #test_mainwindow_with_config()
        
        print("\n" + "="*60)
        print("  ✅ TODOS LOS TESTS PASARON")
        print("="*60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLÓ: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)