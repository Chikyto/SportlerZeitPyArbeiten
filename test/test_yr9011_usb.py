#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para lector INVELION YR9011 USB
"""

import sys
import time
from PyQt6.QtWidgets import QApplication
from src.core.yr9011_usb_scanner import YR9011USBScanner


def test_yr9011():
    """Probar lector YR9011"""
    print("=" * 60)
    print("TEST LECTOR INVELION YR9011 USB")
    print("=" * 60)
    print()

    # Crear aplicación Qt (necesaria para señales)
    app = QApplication(sys.argv)

    # Crear scanner
    scanner = YR9011USBScanner()

    # Listar puertos disponibles
    print("📋 Puertos COM disponibles:")
    ports = scanner.list_available_ports()
    if not ports:
        print("   ⚠️  No se encontraron puertos COM")
        print()
        print("Verifica:")
        print("  • Que el lector YR9011 esté conectado al USB")
        print("  • Que los drivers estén instalados")
        print("  • Que el puerto no esté siendo usado")
        return

    for port_info in ports:
        print(f"   • {port_info['port']}: {port_info['description']}")
    print()

    # Conectar
    print("🔌 Intentando conectar...")
    if not scanner.connect():
        print("❌ No se pudo conectar")
        print()
        print("Si el puerto es correcto, intenta especificarlo manualmente:")
        print("   scanner = YR9011USBScanner(port='COM3')  # Windows")
        print("   scanner = YR9011USBScanner(port='/dev/ttyUSB0')  # Linux")
        return

    print("✅ Conectado exitosamente")
    print()

    # Obtener versión
    version = scanner.get_firmware_version()
    if version:
        print(f"📦 Firmware: v{version}")
    else:
        print("⚠️  No se pudo leer versión del firmware")
    print()

    # Configurar callback para tags detectados
    def on_tag_detected(tag_data):
        chip_id = tag_data['tag_id']
        timestamp = tag_data['timestamp']
        print(f"✓ TAG DETECTADO: {chip_id} @ {timestamp.strftime('%H:%M:%S')}")
        print()

    scanner.tag_detected.connect(on_tag_detected)

    # Iniciar lectura continua
    print("=" * 60)
    print("🔴 LECTURA CONTINUA ACTIVADA")
    print("   Acerca un chip RFID al lector...")
    print("   Presiona Ctrl+C para detener")
    print("=" * 60)
    print()

    scanner.start_continuous_reading()

    try:
        # Mantener el script corriendo
        while True:
            app.processEvents()
            time.sleep(0.1)

    except KeyboardInterrupt:
        print()
        print("🛑 Deteniendo lectura...")
        scanner.stop_continuous_reading()
        scanner.disconnect()
        print("✅ Desconectado")


if __name__ == "__main__":
    test_yr9011()
