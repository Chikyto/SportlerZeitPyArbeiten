#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para YR9011 en COM3
"""

import sys
import time
import serial
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject

# Probar diferentes configuraciones
CONFIGS = [
    {'baudrate': 115200, 'name': '115200 bps (alta velocidad)'},
    {'baudrate': 57600, 'name': '57600 bps (velocidad media)'},
    {'baudrate': 9600, 'name': '9600 bps (velocidad baja)'},
]


def test_baudrate(port, baudrate):
    """Probar un baudrate específico"""
    try:
        print(f"   Probando {baudrate} bps...", end=' ')

        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=0.5,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE
        )

        # Limpiar buffers
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        time.sleep(0.1)

        # Comandos comunes de RFID readers
        commands = [
            (b'\xA0\x03\x01\x00\xA4', 'Versión A0'),
            (b'\xBB\x00\x03\x00\x01\x00\x04', 'Versión BB'),
            (b'\xFF\x00\x00\x00', 'Reset FF'),
        ]

        for cmd, cmd_name in commands:
            ser.write(cmd)
            time.sleep(0.2)

            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                ser.close()
                print(f"✅ RESPONDE!")
                print(f"      Comando: {cmd_name}")
                print(f"      Respuesta: {' '.join(f'{b:02X}' for b in response)}")
                return baudrate, response

        ser.close()
        print("No responde")
        return None, None

    except Exception as e:
        print(f"Error: {e}")
        return None, None


def test_continuous_read(port, baudrate):
    """Modo de lectura continua"""
    print(f"\n{'='*60}")
    print(f"🔴 LECTURA CONTINUA en {baudrate} bps")
    print(f"   Acerca un chip RFID al lector...")
    print(f"   Observando datos recibidos...")
    print(f"   Presiona Ctrl+C para detener")
    print(f"{'='*60}\n")

    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=0.1
        )

        ser.reset_input_buffer()

        # Intentar enviar comando de inventario continuo
        inventory_commands = [
            b'\xA0\x04\x01\x89\x01\x8F',  # INVELION inventory
            b'\xBB\x00\x27\x00\x03\x22\x00\x00\x22',  # Otro formato común
        ]

        for cmd in inventory_commands:
            print(f"Enviando comando de inventario: {' '.join(f'{b:02X}' for b in cmd)}")
            ser.write(cmd)
            time.sleep(0.1)

        print("\nEscuchando datos...\n")

        last_print = time.time()
        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                hex_str = ' '.join(f'{b:02X}' for b in data)
                ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)

                print(f"[{time.strftime('%H:%M:%S')}] Recibido ({len(data)} bytes):")
                print(f"   HEX:   {hex_str}")
                print(f"   ASCII: {ascii_str}")
                print()

            # Mostrar "." cada segundo para indicar que está vivo
            if time.time() - last_print > 1.0:
                print(".", end='', flush=True)
                last_print = time.time()

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\n🛑 Detenido por usuario")
        ser.close()


def main():
    PORT = 'COM3'

    print("=" * 60)
    print("DIAGNÓSTICO LECTOR YR9011 USB - COM3")
    print("=" * 60)
    print()

    # Paso 1: Encontrar baudrate correcto
    print("📡 PASO 1: Detectando baudrate...")
    print()

    working_baudrate = None
    for config in CONFIGS:
        baudrate, response = test_baudrate(PORT, config['baudrate'])
        if baudrate:
            working_baudrate = baudrate
            print(f"\n✅ BAUDRATE CORRECTO: {baudrate} bps\n")
            break

    if not working_baudrate:
        print("\n⚠️  No se detectó respuesta con ningún baudrate común.")
        print("\nProbando lectura continua con 115200 bps (más común)...")
        working_baudrate = 115200

    # Paso 2: Modo lectura continua
    try:
        test_continuous_read(PORT, working_baudrate)
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
