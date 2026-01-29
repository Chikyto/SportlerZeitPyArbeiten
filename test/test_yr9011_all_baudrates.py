#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test exhaustivo de TODOS los baudrates con YR9011
"""

import serial
import time

PORT = 'COM3'

# Todos los baudrates posibles
BAUDRATES = [
    300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800,
    38400, 57600, 115200, 128000, 230400, 256000, 460800, 921600
]

def test_baudrate_with_commands(baudrate):
    """Probar baudrate con varios comandos"""
    try:
        ser = serial.Serial(PORT, baudrate, timeout=0.3)
        time.sleep(0.1)

        # Comandos a probar
        commands = [
            (b'\xA0\x02\x00\x72\x74', "0x72 Get Version"),
            (b'\xA0\x02\x00\x89\x8B', "0x89 Inventory"),
            (b'\xA0\x03\x00\x89\x01\x8D', "0x89 Inventory+param"),
            (b'\xBB\x00\x03\x00\x01\x00\x04', "Formato BB"),
            (b'\xFF\x00\x00\x00', "Reset FF"),
        ]

        for cmd, name in commands:
            ser.reset_input_buffer()
            ser.write(cmd)
            time.sleep(0.15)

            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                ser.close()

                print(f"\n{'='*60}")
                print(f"✅ RESPUESTA DETECTADA!")
                print(f"{'='*60}")
                print(f"Baudrate: {baudrate} bps")
                print(f"Comando: {name}")
                print(f"Enviado: {' '.join(f'{b:02X}' for b in cmd)}")
                print(f"Recibido: {' '.join(f'{b:02X}' for b in response)}")
                print(f"{'='*60}\n")
                return baudrate

        ser.close()
        return None

    except Exception as e:
        return None


def main():
    print("=" * 60)
    print("TEST EXHAUSTIVO - TODOS LOS BAUDRATES")
    print("=" * 60)
    print()
    print("Este test va a probar TODOS los baudrates posibles")
    print("con varios formatos de comandos diferentes.")
    print()
    print("⚠️  IMPORTANTE: Mantené un chip cerca del lector")
    print("   durante todo el test (por si necesita estar leyendo)")
    print()
    input("Presiona Enter para comenzar...")
    print()

    print("Probando comandos en cada baudrate...")
    print("(Esto puede tomar 1-2 minutos)")
    print()

    detected = []

    for i, baudrate in enumerate(BAUDRATES, 1):
        print(f"[{i:2d}/{len(BAUDRATES)}] {baudrate:>7} bps... ", end='', flush=True)

        result = test_baudrate_with_commands(baudrate)

        if result:
            detected.append(result)
            print(f"✅ RESPONDE!")
        else:
            print("sin respuesta")

        time.sleep(0.1)

    print()
    print("=" * 60)

    if detected:
        print(f"✅ BAUDRATES QUE RESPONDIERON: {detected}")
        print()
        print("Usa uno de estos baudrates en el driver.")
    else:
        print("❌ Ningún baudrate respondió.")
        print()
        print("Posibles causas:")
        print("  1. El lector necesita configuración con software del fabricante")
        print("  2. Está en modo que requiere inicialización especial")
        print("  3. Puerto COM incorrecto")
        print("  4. Cable o driver defectuoso")
        print()
        print("Solución:")
        print("  → Usa el software del fabricante para configurar el lector")
        print("  → Busca una opción tipo 'Serial Output Mode' o 'Communication Mode'")
        print("  → Asegúrate que esté en modo 'RS-232' o 'Serial' (no HID)")

    print("=" * 60)


if __name__ == "__main__":
    main()
