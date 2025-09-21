#!/usr/bin/env python3
"""
Script de configuración inicial para RFID Athletics Timer
Crea la estructura de directorios y archivos necesarios
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_step(step, message):
    """Imprime un paso del proceso de configuración"""
    print(f"\n[{step}] {message}")
    print("-" * 50)

def create_directory_structure():
    """Crea la estructura de directorios del proyecto"""
    print_step("1", "Creando estructura de directorios")
    
    directories = [
        "src",
        "src/core",
        "src/gui",
        "src/gui/widgets",
        "src/gui/resources",
        "src/gui/resources/icons",
        "src/gui/resources/styles",
        "src/data",
        "src/utils",
        "tests",
        "docs",
        "data",
        "data/databases",
        "data/exports", 
        "data/logs",
        "scripts"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}/")
        
        # Crear __init__.py en directorios de Python
        if directory.startswith("src") or directory == "tests":
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"    ✓ {init_file}")

def create_config_files():
    """Crea archivos de configuración básicos"""
    print_step("2", "Creando archivos de configuración")
    
    # .gitignore
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Project specific
data/databases/*.db
data/logs/*.log
data/exports/*
!data/databases/.gitkeep
!data/logs/.gitkeep
!data/exports/.gitkeep

# OS
.DS_Store
Thumbs.db

# PyQt
*.ui~
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    print("  ✓ .gitignore")
    
    # Crear archivos .gitkeep
    gitkeep_dirs = ["data/databases", "data/logs", "data/exports"]
    for dir_path in gitkeep_dirs:
        gitkeep_file = Path(dir_path) / ".gitkeep"
        gitkeep_file.touch()
        print(f"  ✓ {gitkeep_file}")

def create_main_entry_point():
    """Crea el archivo main.py de entrada"""
    print_step("3", "Creando archivo de entrada principal")
    
    main_content = '''#!/usr/bin/env python3
"""
RFID Athletics Timer - Punto de entrada principal
"""

import sys
import os
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """Función principal de la aplicación"""
    try:
        from gui.main_window import MainWindow
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        app.setApplicationName("RFID Athletics Timer")
        app.setApplicationVersion("1.0.0")
        
        # Configurar estilo
        app.setStyle('Fusion')
        
        window = MainWindow()
        window.show()
        
        return app.exec()
        
    except ImportError as e:
        print(f"Error: No se pudieron importar las dependencias necesarias.")
        print(f"Detalles: {e}")
        print("\\nAsegúrate de tener instaladas todas las dependencias:")
        print("pip install -r requirements.txt")
        return 1
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    with open("main.py", "w") as f:
        f.write(main_content)
    print("  ✓ main.py")

def create_basic_modules():
    """Crea módulos básicos del proyecto"""
    print_step("4", "Creando módulos básicos")
    
    # src/core/config.py
    config_content = '''"""
Configuración del sistema RFID Athletics Timer
"""

import os
from pathlib import Path

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Configuración del lector RFID
RFID_HOST = "192.168.0.178"
RFID_PORT = 4001
RFID_TIMEOUT = 3.0

# Configuración de scanning
SCAN_INTERVAL = 500  # milliseconds
DUPLICATE_THRESHOLD = 2.0  # seconds

# Configuración de la base de datos
DATABASE_PATH = PROJECT_ROOT / "data" / "databases" / "athletics.db"

# Configuración de logging
LOG_LEVEL = "INFO"
LOG_PATH = PROJECT_ROOT / "data" / "logs"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Configuración de exportación
EXPORT_PATH = PROJECT_ROOT / "data" / "exports"

# Configuración de la aplicación
APP_NAME = "RFID Athletics Timer"
APP_VERSION = "1.0.0"
WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"

# Patrones de chips conocidos
KNOWN_TAG_PATTERNS = {
    (0x85, 0x99): "8599",
    (0x85, 0x75): "8575", 
    (0x85, 0x87): "8587",
    (0x76, 0x62): "7662",
    (0x36, 0x42): "3642",
    (0x59, 0x62): "5962",
    (0x86, 0x00): "8600",
}
'''
    
    config_file = Path("src/core/config.py")
    with open(config_file, "w") as f:
        f.write(config_content)
    print(f"  ✓ {config_file}")

def check_python_version():
    """Verifica la versión de Python"""
    print_step("5", "Verificando versión de Python")
    
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 8):
        print("  ⚠️  ADVERTENCIA: Se recomienda Python 3.8 o superior")
        return False
    else:
        print("  ✓ Versión de Python compatible")
        return True

def check_virtual_environment():
    """Verifica si está en un entorno virtual"""
    print_step("6", "Verificando entorno virtual")
    
    in_venv = (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )
    
    if in_venv:
        print("  ✓ Ejecutándose en entorno virtual")
        return True
    else:
        print("  ⚠️  No se detectó entorno virtual")
        print("  Se recomienda usar un entorno virtual:")
        if platform.system() == "Windows":
            print("    python -m venv venv")
            print("    venv\\Scripts\\activate")
        else:
            print("    python3 -m venv venv") 
            print("    source venv/bin/activate")
        return False

def install_dependencies():
    """Instala las dependencias si están en un entorno virtual"""
    print_step("7", "Instalando dependencias")
    
    if not Path("requirements.txt").exists():
        print("  ⚠️  Archivo requirements.txt no encontrado")
        return False
    
    try:
        # Verificar si pip está disponible
        subprocess.run([sys.executable, "-m", "pip", "--version"], 
                      check=True, capture_output=True)
        
        # Instalar dependencias
        print("  Instalando dependencias...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✓ Dependencias instaladas correctamente")
            return True
        else:
            print(f"  ⚠️  Error instalando dependencias: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError:
        print("  ⚠️  pip no está disponible")
        return False
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return False

def test_pyqt_installation():
    """Prueba la instalación de PyQt6"""
    print_step("8", "Verificando instalación de PyQt6")
    
    try:
        import PyQt6.QtWidgets
        print("  ✓ PyQt6 instalado correctamente")
        return True
    except ImportError:
        print("  ⚠️  PyQt6 no está instalado o no funciona")
        print("  Instala PyQt6 manualmente:")
        print("    pip install PyQt6")
        return False

def create_test_files():
    """Crea archivos de test básicos"""
    print_step("9", "Creando archivos de test")
    
    test_content = '''"""
Test básico para verificar la configuración del proyecto
"""

import unittest
import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

class TestProjectSetup(unittest.TestCase):
    """Tests de configuración del proyecto"""
    
    def test_imports(self):
        """Verifica que los módulos se puedan importar"""
        try:
            from core import config
            from utils import constants
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Error importando módulos: {e}")
    
    def test_directories_exist(self):
        """Verifica que los directorios principales existan"""
        project_root = Path(__file__).parent.parent
        
        required_dirs = [
            "src", "src/core", "src/gui", "src/data", "src/utils",
            "data", "data/databases", "data/logs", "data/exports"
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            self.assertTrue(dir_path.exists(), f"Directorio {dir_name} no existe")

if __name__ == "__main__":
    unittest.main()
'''
    
    test_file = Path("tests/test_setup.py")
    with open(test_file, "w") as f:
        f.write(test_content)
    print(f"  ✓ {test_file}")

def main():
    """Función principal del script de configuración"""
    print("=" * 60)
    print("  RFID ATHLETICS TIMER - CONFIGURACIÓN INICIAL")
    print("=" * 60)
    
    # Verificar que estamos en el directorio correcto
    if not Path("requirements.txt").exists():
        print("\n❌ Error: Ejecuta este script desde el directorio raíz del proyecto")
        print("   (donde está el archivo requirements.txt)")
        sys.exit(1)
    
    # Pasos de configuración
    steps_completed = 0
    total_steps = 9
    
    try:
        create_directory_structure()
        steps_completed += 1
        
        create_config_files()
        steps_completed += 1
        
        create_main_entry_point()
        steps_completed += 1
        
        create_basic_modules()
        steps_completed += 1
        
        if check_python_version():
            steps_completed += 1
        
        if check_virtual_environment():
            steps_completed += 1
        
        if install_dependencies():
            steps_completed += 1
        
        if test_pyqt_installation():
            steps_completed += 1
            
        create_test_files()
        steps_completed += 1
        
    except KeyboardInterrupt:
        print("\n\n❌ Configuración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error durante la configuración: {e}")
        sys.exit(1)
    
    # Resumen final
    print("\n" + "=" * 60)
    print("  RESUMEN DE CONFIGURACIÓN")
    print("=" * 60)
    print(f"Pasos completados: {steps_completed}/{total_steps}")
    
    if steps_completed == total_steps:
        print("\n✅ ¡Configuración completada exitosamente!")
        print("\nPróximos pasos:")
        print("1. python main.py          # Ejecutar la aplicación")
        print("2. python -m pytest tests/ # Ejecutar tests")
        print("3. Consultar docs/README.md para más información")
    else:
        print(f"\n⚠️  Configuración parcial ({steps_completed}/{total_steps} pasos)")
        print("Revisa los mensajes anteriores para resolver problemas pendientes")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()