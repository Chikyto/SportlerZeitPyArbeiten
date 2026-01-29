#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de generación de comandos YR9011
Verifica que los comandos se generen exactamente como en test_cgpt.py
"""

from src.core.yr9011_usb_scanner import YR9011USBScanner


def test_commands():
    """Test de comandos generados"""
    print("=" * 60)
    print("TEST GENERACIÓN DE COMANDOS YR9011")
    print("=" * 60)
    print()

    scanner = YR9011USBScanner()

    # Test Reset
    cmd_reset = scanner._build_command(0x70, b'\x00')
    print("Reset (0x70):")
    print(f"  HEX: {cmd_reset.hex(' ').upper()}")
    print(f"  Esperado: A0 05 01 70 00 .. (checksum)")
    print()

    # Test Host Mode
    cmd_host = scanner._build_command(0x75, b'\x01')
    print("Host Mode (0x75):")
    print(f"  HEX: {cmd_host.hex(' ').upper()}")
    print(f"  Esperado: A0 05 01 75 01 .. (checksum)")
    print()

    # Test RF ON
    cmd_rf = scanner._build_command(0x74, b'\x00')
    print("RF ON (0x74):")
    print(f"  HEX: {cmd_rf.hex(' ').upper()}")
    print(f"  Esperado: A0 05 01 74 00 .. (checksum)")
    print()

    # Test Power
    cmd_power = scanner._build_command(0x7A, b'\x00')
    print("Power (0x7A):")
    print(f"  HEX: {cmd_power.hex(' ').upper()}")
    print(f"  Esperado: A0 05 01 7A 00 .. (checksum)")
    print()

    # Test Inventory (ESPECIAL - length fijo 0x04)
    cmd_inv = scanner._build_command(0x89, b'\x01')
    print("Inventory (0x89) - ESPECIAL:")
    print(f"  HEX: {cmd_inv.hex(' ').upper()}")
    print(f"  Esperado: A0 04 01 89 01 .. (checksum)")
    print(f"  ⚠️  Length FIJO = 0x04 (no calculado)")
    print()

    # Verificar checksum
    print("=" * 60)
    print("VERIFICACIÓN DE CHECKSUM")
    print("=" * 60)
    print()

    test_data = bytes([0x04, 0x01, 0x89])
    fake = b"\x00"
    checksum = scanner._calculate_checksum(test_data + fake)
    print(f"Checksum de [04 01 89 00]: {checksum:02X}")
    print(f"Formula: (sum(data) + 0x42) & 0xFF")
    print(f"Cálculo: ({sum(test_data + fake)} + 0x42) & 0xFF = {checksum:02X}")
    print()

    print("✅ Test completado")
    print()
    print("Si estos comandos coinciden con los de test_cgpt.py,")
    print("el driver debería funcionar correctamente!")


if __name__ == "__main__":
    test_commands()
