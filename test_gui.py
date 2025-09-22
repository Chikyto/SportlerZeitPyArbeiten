#!/usr/bin/env python3
"""
Test simple de la GUI
"""

import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from PyQt6.QtWidgets import QApplication
from src.gui.simple_gui import SimpleGUI

def main():
    app = QApplication(sys.argv)
    
    window = SimpleGUI()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())