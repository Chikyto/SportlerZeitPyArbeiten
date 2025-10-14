"""
Test del parser universal - debe detectar CUALQUIER chip
"""
import sys
from pathlib import Path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

from src.core.tag_parser import TagParser

def test_universal_parser():
    print("\n=== TEST PARSER UNIVERSAL ===\n")
    
    parser = TagParser(debug=True)
    
    # Test 1: Chips conocidos (tus actuales)
    print("Test 1: Chips conocidos")
    known_chips = [
        bytes([0x85, 0x99, 0x00, 0x01, 0x02, 0x03]),  # 8599
        bytes([0x85, 0x75, 0x00, 0x01, 0x02, 0x03]),  # 8575
    ]
    
    for chip in known_chips:
        number = parser.extract_tag_number(chip)
        print(f"  → Detectado: {number}\n")
    
    # Test 2: Chips NUEVOS (nunca vistos antes)
    print("\nTest 2: Chips nuevos (sin estar en lista)")
    new_chips = [
        bytes([0x92, 0x45, 0x00, 0x01, 0x02, 0x03]),  # Nuevo chip 1
        bytes([0x73, 0x88, 0x00, 0x01, 0x02, 0x03]),  # Nuevo chip 2
        bytes([0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66]),  # EPC largo
    ]
    
    for i, chip in enumerate(new_chips, 1):
        number = parser.extract_tag_number(chip)
        print(f"  Chip nuevo {i} → Detectado: {number}\n")
        assert number is not None, f"Chip {i} debería ser detectado!"
    
    # Estadísticas
    stats = parser.get_stats()
    print(f"\n=== ESTADÍSTICAS ===")
    print(f"Total procesados: {stats['total']}")
    print(f"Válidos: {stats['valid']}")
    print(f"Inválidos: {stats['invalid']}")
    print(f"Tasa de éxito: {stats['valid']/stats['total']*100:.1f}%")
    
    print("\n✅ Test completado - Parser universal funciona!")

if __name__ == "__main__":
    test_universal_parser()