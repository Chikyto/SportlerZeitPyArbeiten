#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test pasivo del YR9011 - captura TODO lo que envía sin comandos
"""

import serial
import time

PORT = 'COM3'

# Todos los baudrates estándar
BAUDRATES = [
    300, 600, 1200, 2400, 4800, 9600, 14400, 19200, 28800,
    38400, 57600, 115200, 128000, 230400, 256000, 460800, 921600
]

def test_passive_listening(baudrate):
    """Escuchar pasivamente sin enviar comandos"""
    try:
        print(f"Probando {baudrate:>7} bps... ", end='', flush=True)

        ser = serial.Serial(
            port=PORT,
            baudrate=baudrate,
            timeout=0.1
        )

        # NO enviar comandos, solo escuchar
        time.sleep(0.2)

        # Revisar si hay datos
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            ser.close()

            print(f"✅ DATOS RECIBIDOS!")
            print(f"\n{'='*60}")
            print(f"BAUDRATE CORRECTO: {baudrate} bps")
            print(f"{'='*60}")
            print(f"Datos ({len(data)} bytes):")
            print(f"HEX:   {' '.join(f'{b:02X}' for b in data)}")
            print(f"ASCII: {''.join(chr(b) if 32 <= b < 127 else '.' for b in data)}")
            print(f"{'='*60}\n")
            return baudrate

        ser.close()
        print("Sin datos")
        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def continuous_listen(baudrate):
    """Modo de escucha continua en baudrate específico"""
    print(f"\n{'='*60}")
    print(f"MODO ESCUCHA CONTINUA - {baudrate} bps")
    print(f"Acerca chips al lector y observa los datos...")
    print(f"Presiona Ctrl+C para detener")
    print(f"{'='*60}\n")

    try:
        ser = serial.Serial(port=PORT, baudrate=baudrate, timeout=0.1)

        last_data_time = time.time()

        while True:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                timestamp = time.strftime('%H:%M:%S')

                print(f"[{timestamp}] Recibido ({len(data)} bytes):")
                print(f"   HEX:   {' '.join(f'{b:02X}' for b in data)}")
                print(f"   ASCII: {''.join(chr(b) if 32 <= b < 127 else '.' for b in data)}")

                # Intentar decodificar como EPC
                if len(data) >= 12:
                    # Buscar patrón de EPC (típicamente 12-24 bytes)
                    print(f"   Posible EPC: {''.join(f'{b:02X}' for b in data[-12:])}")

                print()
                last_data_time = time.time()

            # Indicador de "vivo" cada 3 segundos
            if time.time() - last_data_time > 3:
                print(".", end='', flush=True)
                last_data_time = time.time()

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\n🛑 Detenido")
        ser.close()


def main():
    print("=" * 60)
    print("TEST PASIVO YR9011 - ESCUCHA SIN COMANDOS")
    print("=" * 60)
    print()
    print("Este test NO envía comandos, solo escucha.")
    print("Acerca un chip al lector cuando empiece cada prueba.")
    print()
    input("Presiona Enter cuando estés listo...")
    print()

    print("📡 Probando todos los baudrates comunes...")
    print("   (Acerca y aleja chips durante las pruebas)")
    print()

    detected = None

    for baudrate in BAUDRATES:
        result = test_passive_listening(baudrate)
        if result:
            detected = result
            break
        time.sleep(0.1)

    if detected:
        print(f"\n✅ ¡BAUDRATE DETECTADO: {detected} bps!\n")
        print("Iniciando modo de escucha continua...")
        time.sleep(1)
        continuous_listen(detected)
    else:
        print("\n⚠️  No se detectaron datos en ningún baudrate.")
        print("\nPosibles causas:")
        print("  1. El lector necesita software de configuración previo")
        print("  2. Está en modo 'no-output' y necesita activarse")
        print("  3. Los datos se envían en ráfagas muy cortas")
        print("  4. Usa protocolo propietario no estándar")
        print()
        print("Probando escucha prolongada en 115200 bps...")
        print("(Acerca varios chips durante 30 segundos)")
        input("Presiona Enter para continuar...")

        try:
            ser = serial.Serial(PORT, 115200, timeout=0.1)
            start = time.time()

            while time.time() - start < 30:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    print(f"\n✅ DATOS: {' '.join(f'{b:02X}' for b in data)}")
                time.sleep(0.05)

            ser.close()
            print("\nNo se recibieron datos.")
        except KeyboardInterrupt:
            print("\n🛑 Detenido")


if __name__ == "__main__":
    main()
