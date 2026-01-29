#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del driver YR9011 integrado con el código verificado
"""

import sys
import time
from PyQt6.QtWidgets import QApplication
from src.core.yr9011_usb_scanner import YR9011USBScanner


def test_yr9011_integrated():
    """Test del driver integrado"""
    print("=" * 60)
    print("TEST YR9011 - DRIVER INTEGRADO")
    print("=" * 60)
    print()
    print("Usando código verificado de test_cgpt.py")
    print("Protocolo: 0xA0 [Len][Address][Cmd][Data][Check]")
    print("Baudrate: 115200 bps")
    print("Address: 0x01")
    print()

    # Crear aplicación Qt
    app = QApplication(sys.argv)

    # Crear scanner
    scanner = YR9011USBScanner(port='COM3')

    # Callback para tags detectados
    def on_tag_detected(tag_data):
        chip_id = tag_data['tag_id']
        timestamp = tag_data['timestamp']
        print(f"\n🎯 TAG DETECTADO!")
        print(f"   EPC: {chip_id}")
        print(f"   Hora: {timestamp.strftime('%H:%M:%S')}")
        print(f"   Lector: {tag_data['reader']}")
        print()

    scanner.tag_detected.connect(on_tag_detected)

    # Conectar
    print("📡 Conectando a COM3...")
    if not scanner.connect():
        print("❌ No se pudo conectar")
        print()
        print("Verifica:")
        print("  • Que el YR9011 esté conectado al puerto COM3")
        print("  • Que no esté siendo usado por otra aplicación")
        print("  • Que los drivers CP210x estén instalados")
        return

    print("✅ Conectado e inicializado")
    print()

    # Test de lectura single
    print("=" * 60)
    print("🔍 TEST 1: Lectura Single Tag")
    print("   Acerca un chip al lector (5 segundos)...")
    print("=" * 60)
    print()

    epc = scanner.read_single_tag(timeout=5)
    if epc:
        print(f"   ✅ Tag leído: {epc}")
    else:
        print("   ⏱️  Timeout - No se detectó tag")
    print()

    # Modo continuo
    print("=" * 60)
    print("🔴 TEST 2: LECTURA CONTINUA")
    print("   Acerca chips al lector...")
    print("   Presiona Ctrl+C para detener")
    print("=" * 60)
    print()

    scanner.start_continuous_reading()

    try:
        while True:
            app.processEvents()
            time.sleep(0.1)

    except KeyboardInterrupt:
        print()
        print("🛑 Deteniendo...")
        scanner.stop_continuous_reading()
        scanner.disconnect()
        print("✅ Test completado")


if __name__ == "__main__":
    test_yr9011_integrated()
