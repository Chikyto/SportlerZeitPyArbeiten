#!/usr/bin/env python3
"""
Test de la GUI con sistema de pestañas
"""

import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication
from src.gui.tabbed_gui import TabbedGUI

def main():
    app = QApplication(sys.argv)
    
    window = TabbedGUI()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())