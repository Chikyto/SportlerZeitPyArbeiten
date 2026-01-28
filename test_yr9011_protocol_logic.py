#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de lógica del protocolo YR9011 sin dependencias
Verifica que las funciones de checksum y construcción sean correctas
"""


def checksum_yr9011(data: bytes) -> int:
    """Checksum YR9011: (sum + 0x42) & 0xFF"""
    return (sum(data) + 0x42) & 0xFF


def build_command(cmd: int, data: bytes = b'') -> bytes:
    """
    Construir comando YR9011

    Inventory (0x89) es especial con length fijo 0x04
    Otros comandos usan length = 1+1+len(data)+1
    """
    addr = 0x01

    # Inventory es especial
    if cmd == 0x89:
        length = 0x04
        body = bytes([length, addr, cmd]) + data
        fake = b"\x00"
        cs = checksum_yr9011(body + fake)
        return b"\xA0" + body + bytes([cs])

    # Otros comandos normales
    length = 1 + 1 + len(data) + 1
    body = bytes([length, addr, cmd]) + data + b"\x00"
    cs = checksum_yr9011(body)
    return b"\xA0" + body + bytes([cs])


def test_commands():
    """Test de comandos"""
    print("=" * 60)
    print("TEST PROTOCOLO YR9011")
    print("=" * 60)
    print()

    # Test Reset
    cmd = build_command(0x70, b'\x00')
    print("Reset (0x70, 0x00):")
    print(f"  {cmd.hex(' ').upper()}")
    print()

    # Test Host Mode
    cmd = build_command(0x75, b'\x01')
    print("Host Mode (0x75, 0x01):")
    print(f"  {cmd.hex(' ').upper()}")
    print()

    # Test RF ON
    cmd = build_command(0x74, b'\x00')
    print("RF ON (0x74, 0x00):")
    print(f"  {cmd.hex(' ').upper()}")
    print()

    # Test Power
    cmd = build_command(0x7A, b'\x00')
    print("Power (0x7A, 0x00):")
    print(f"  {cmd.hex(' ').upper()}")
    print()

    # Test Inventory - ESPECIAL
    cmd = build_command(0x89, b'\x01')
    print("Inventory (0x89, 0x01) - ESPECIAL:")
    print(f"  {cmd.hex(' ').upper()}")
    print(f"  Length = 0x04 FIJO")
    print()

    print("=" * 60)
    print("COMPARAR CON test_cgpt.py")
    print("=" * 60)
    print()
    print("Si los comandos coinciden, el driver está bien!")
    print()

    # Test checksum específico
    print("Test checksum para Inventory:")
    data = bytes([0x04, 0x01, 0x89, 0x00])
    cs = checksum_yr9011(data)
    print(f"  Data: {data.hex(' ').upper()}")
    print(f"  Checksum: {cs:02X}")
    print(f"  Cálculo: ({sum(data)} + 0x42) & 0xFF = {cs}")


if __name__ == "__main__":
    test_commands()
