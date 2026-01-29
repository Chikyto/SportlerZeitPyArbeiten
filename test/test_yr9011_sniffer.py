#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sniffer para capturar comunicación entre software INVELION y YR9011
Actúa como proxy entre el software y el lector
"""

import serial
import time
import sys
from datetime import datetime

# Configuración
REAL_PORT = 'COM3'  # Puerto real del lector
BAUDRATE = 115200

def hex_dump(data, direction=""):
    """Mostrar datos en formato hexadecimal"""
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    hex_str = ' '.join(f'{b:02X}' for b in data)

    if direction == "→":
        print(f"[{timestamp}] HOST → LECTOR ({len(data)} bytes)")
    else:
        print(f"[{timestamp}] LECTOR → HOST ({len(data)} bytes)")

    print(f"   HEX: {hex_str}")

    # Mostrar interpretación si es formato 0xA0
    if len(data) >= 5 and data[0] == 0xA0:
        length = data[1]
        address = data[2]
        cmd = data[3]
        print(f"   → Header: 0xA0, Len: {length}, Addr: 0x{address:02X}, Cmd: 0x{cmd:02X}")

        if len(data) > 4:
            payload = data[4:-1]
            checksum = data[-1]
            if payload:
                print(f"   → Data: {' '.join(f'{b:02X}' for b in payload)}")
            print(f"   → Checksum: 0x{checksum:02X}")

    print()


def passive_monitor():
    """
    Modo monitor pasivo - solo escucha sin interferir
    Usa esto MIENTRAS el software del fabricante está corriendo
    """
    print("=" * 70)
    print("MONITOR PASIVO - Capturando tráfico de COM3")
    print("=" * 70)
    print()
    print("⚠️  INSTRUCCIONES:")
    print("   1. Este script va a ESCUCHAR el puerto COM3")
    print("   2. Abrí el software INVELION Demo")
    print("   3. Hacé click en 'Inventory' en el software")
    print("   4. Este script capturará los comandos")
    print()
    print("⚠️  LIMITACIÓN: El monitor pasivo puede no capturar todo")
    print("   Si no ves datos, usa la Alternativa 2 (abajo)")
    print()
    input("Presiona Enter para comenzar el monitoreo...")
    print()
    print("🟢 MONITOREANDO... (Presiona Ctrl+C para detener)")
    print()

    try:
        ser = serial.Serial(REAL_PORT, BAUDRATE, timeout=0.1)

        while True:
            # Leer datos que lleguen
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                hex_dump(data, "←")

            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n🛑 Monitoreo detenido")
        ser.close()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nLa captura pasiva no funciona si el puerto está en uso.")
        print("Usa un Serial Port Monitor externo (ver instrucciones abajo)")


def main():
    print("=" * 70)
    print("CAPTURADOR DE PROTOCOLO YR9011")
    print("=" * 70)
    print()

    print("📋 MÉTODOS DE CAPTURA:")
    print()
    print("1️⃣  MÉTODO RECOMENDADO: Free Serial Port Monitor")
    print("   • Descarga: https://freeserialportmonitor.com/")
    print("   • Configura: COM3, 115200 bps")
    print("   • Inicia captura")
    print("   • Usa software INVELION Demo")
    print("   • Copia los comandos que capture")
    print()
    print("2️⃣  MÉTODO ALTERNATIVO: Este script (modo pasivo)")
    print("   • Solo funciona si puede compartir el puerto")
    print("   • Puede no capturar todo")
    print()
    print("3️⃣  MÉTODO MANUAL: Observación en el software")
    print("   • El software INVELION tiene 'Serial Port Monitor'")
    print("   • ¿Ves alguna ventana de log o debug?")
    print()

    choice = input("¿Quieres probar el modo pasivo? (s/n): ").lower()

    if choice == 's':
        passive_monitor()
    else:
        print()
        print("=" * 70)
        print("ANÁLISIS BASADO EN LO QUE SABEMOS:")
        print("=" * 70)
        print()
        print("El software INVELION funciona, así que sabemos que:")
        print("  ✓ Baudrate: 115200 bps")
        print("  ✓ Puerto: COM3")
        print("  ✓ Protocolo: 0xA0 (según docs)")
        print()
        print("Los comandos más probables que usa son:")
        print("  • 0x89 - Real-time inventory")
        print("  • 0x80 - Buffer inventory + 0x91 para leer buffer")
        print()
        print("Próximo paso:")
        print("  1. Instala Free Serial Port Monitor")
        print("  2. Captura el tráfico")
        print("  3. Pásame los bytes exactos que envía")
        print()


if __name__ == "__main__":
    main()
