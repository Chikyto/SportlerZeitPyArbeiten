#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test final del YR9011 con protocolo oficial INVELION
"""

import sys
import time
from PyQt6.QtWidgets import QApplication
from src.core.yr9011_usb_scanner import YR9011USBScanner


def test_yr9011_official_protocol():
    """Test con protocolo oficial"""
    print("=" * 60)
    print("TEST YR9011 - PROTOCOLO OFICIAL INVELION")
    print("=" * 60)
    print()
    print("Protocolo: 0xA0 [Len][Address][Cmd][Data][Check]")
    print("Baudrate: 115200 bps")
    print("Comando: 0x89 (Real-time Inventory)")
    print()

    # Crear aplicación Qt
    app = QApplication(sys.argv)

    # Crear scanner en COM3
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

    print("✅ Conectado")
    print()

    # Obtener firmware
    print("📦 Obteniendo información del lector...")
    version = scanner.get_firmware_version()
    if version:
        print(f"   Firmware: v{version}")
    else:
        print("   Firmware: (no disponible)")
    print()

    # Test de lectura single
    print("🔍 TEST 1: Lectura Single Tag")
    print("   Acerca un chip al lector (5 segundos)...")
    print()

    epc = scanner.read_single_tag(timeout=5)
    if epc:
        print(f"   ✅ Tag leído: {epc}")
    else:
        print("   ⏱️ Timeout - No se detectó tag")
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
        print("✅ Desconectado")


if __name__ == "__main__":
    test_yr9011_official_protocol()
