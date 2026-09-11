#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug detallado del protocolo YR9011
Muestra todo el tráfico byte por byte
"""

import serial
import time

PORT = 'COM3'
BAUDRATE = 115200

def calculate_checksum(data):
    """Checksum = suma de todos los bytes"""
    return sum(data) & 0xFF

def build_command(cmd, data=b''):
    """Construir comando INVELION"""
    address = 0x01
    length = 1 + 1 + len(data)  # Address + Cmd + Data
    packet = bytes([length, address, cmd]) + data
    checksum = calculate_checksum(packet)
    full_cmd = b'\xA0' + packet + bytes([checksum])
    return full_cmd

def parse_inventory_response(response):
    if len(response) < 7:
        return None

    if response[0] != 0xA0:
        return None

    length = response[1]
    cmd = response[3]

    if cmd != 0x89:
        return None

    rssi = response[4]
    pc = response[5]

    epc_length = length - 5  # len - addr - cmd - rssi - pc - checksum

    epc_start = 6
    epc_end = epc_start + epc_length

    epc = response[epc_start:epc_end]

    return {
        "rssi": rssi,
        "pc": pc,
        "epc": epc.hex().upper()
    }

def hex_dump(data, label=""):
    """Mostrar bytes en formato legible"""
    if label:
        print(f"{label}:")
    hex_str = ' '.join(f'{b:02X}' for b in data)
    print(f"   HEX: {hex_str}")
    print(f"   DEC: {' '.join(f'{b:3d}' for b in data)}")
    print(f"   LEN: {len(data)} bytes")

def test_command(ser, cmd_byte, data=b'', description=""):
    """Probar un comando y mostrar resultado"""
    print("=" * 60)
    print(f"COMANDO: 0x{cmd_byte:02X} - {description}")
    print("=" * 60)

    # Construir comando
    cmd = build_command(cmd_byte, data)

    # Mostrar lo que enviamos
    hex_dump(cmd, "ENVIANDO")

    # Limpiar buffer
    ser.reset_input_buffer()

    # Enviar
    ser.write(cmd)
    time.sleep(0.2)

    # Leer respuesta
    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting)
        hex_dump(response, "RESPUESTA")

        # Intentar parsear
        if len(response) >= 5 and response[0] == 0xA0:
            length = response[1]
            address = response[2]
            cmd_resp = response[3]

            print(f"\n   Parseado:")
            print(f"   - Header: 0x{response[0]:02X}")
            print(f"   - Length: {length}")
            print(f"   - Address: 0x{address:02X}")
            print(f"   - Cmd: 0x{cmd_resp:02X}")

            if len(response) > 4:
                data_bytes = response[4:-1]  # Sin checksum
                checksum = response[-1]
                print(f"   - Data: {' '.join(f'{b:02X}' for b in data_bytes)}")
                print(f"   - Checksum: 0x{checksum:02X}")

                # Verificar checksum
                calc_check = calculate_checksum(response[1:-1])
                if calc_check == checksum:
                    print(f"   ✓ Checksum válido")
                else:
                    print(f"   ✗ Checksum inválido (esperado: 0x{calc_check:02X})")
        else:
            print("   ⚠️ Respuesta con formato inesperado")

        print()
        return True
    else:
        print("   ⚠️ SIN RESPUESTA")
        print()
        return False


def main():
    print("=" * 60)
    print("DEBUG DETALLADO PROTOCOLO YR9011")
    print("=" * 60)
    print()

    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0.5)
        print(f"✅ Puerto {PORT} abierto a {BAUDRATE} bps")
        print()

        # Esperar un momento
        time.sleep(0.5)

        # 1. Reset reader
        test_command(ser, 0x70, description="Reset Reader")
        time.sleep(0.5)

        # 2. Get firmware version
        test_command(ser, 0x72, description="Get Firmware Version")

        # 3. Get reader address
        test_command(ser, 0x73, description="Get Reader Address")

        # 4. Varios comandos de inventario
        print("\n" + "=" * 60)
        print("PROBANDO COMANDOS DE INVENTARIO")
        print("=" * 60)
        print()

        # Inventario simple (0x80)
        test_command(ser, 0x80, description="Inventory (buffered)")

        # Real-time inventory (0x89) - sin parámetros
        test_command(ser, 0x89, description="Real-time Inventory (sin params)")

        # Real-time inventory (0x89) - con parámetro 0x01
        test_command(ser, 0x89, b'\x01', description="Real-time Inventory (param 0x01)")

        # Real-time inventory (0x89) - con parámetro 0x00
        test_command(ser, 0x89, b'\x00', description="Real-time Inventory (param 0x00)")

        # Fast switch (0x8A)
        test_command(ser, 0x8A, description="Fast Switch Ant Inventory")

        # Customized (0x8B)
        test_command(ser, 0x8B, description="Customized Session Target Inventory")

        # ISO18000-6B inventory (0xB0)
        test_command(ser, 0xB0, description="ISO18000-6B Inventory")

        print("\n" + "=" * 60)
        print("MODO ESCUCHA PASIVA")
        print("Acerca chips y observa si hay datos espontáneos...")
        print("Presiona Ctrl+C para detener")
        print("=" * 60)
        print()

        try:
            last_print = time.time()
            while True:
                if ser.in_waiting > 0:
                    data = ser.read(ser.in_waiting)
                    print(f"\n[{time.strftime('%H:%M:%S')}] DATOS RECIBIDOS:")
                    hex_dump(data, "")

                # Indicador de "vivo"
                if time.time() - last_print > 2:
                    print(".", end='', flush=True)
                    last_print = time.time()

                time.sleep(0.05)

        except KeyboardInterrupt:
            print("\n\n🛑 Detenido")

        ser.close()
        print("✅ Puerto cerrado")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
