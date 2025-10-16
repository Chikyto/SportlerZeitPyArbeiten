#!/usr/bin/env python3
"""
Analizador profundo para encontrar dónde está el ID real en el EPC
"""

def find_id_in_epc(epc_hex: str, expected_id: int):
    """
    Buscar el ID esperado en TODAS las posibles combinaciones de bytes
    """
    print("\n" + "=" * 80)
    print(f"📡 EPC: {epc_hex}")
    print(f"🎯 ID Esperado: {expected_id} (0x{expected_id:04X})")
    print("=" * 80)
    
    # Convertir a bytes
    epc_clean = epc_hex.replace(" ", "")
    epc_bytes = bytes.fromhex(epc_clean)
    
    print(f"\n📊 Estructura del EPC ({len(epc_bytes)} bytes):")
    print("   Pos:  " + " ".join(f"{i:2d}" for i in range(len(epc_bytes))))
    print("   Hex:  " + " ".join(f"{b:02X}" for b in epc_bytes))
    print("   Dec:  " + " ".join(f"{b:3d}" for b in epc_bytes))
    
    print(f"\n🔍 Buscando {expected_id} (0x{expected_id:04X}) en todas las posiciones...")
    
    matches = []
    
    # Probar cada posible combinación de 2 bytes consecutivos
    for i in range(len(epc_bytes) - 1):
        # Big endian (byte alto primero)
        value_be = (epc_bytes[i] << 8) | epc_bytes[i+1]
        
        # Little endian (byte bajo primero)
        value_le = (epc_bytes[i+1] << 8) | epc_bytes[i]
        
        if value_be == expected_id:
            matches.append({
                'position': i,
                'bytes': f"{epc_bytes[i]:02X} {epc_bytes[i+1]:02X}",
                'endian': 'big',
                'method': f"bytes[{i}:{i+2}] big-endian"
            })
            print(f"   ✅ Posición {i}-{i+1}: 0x{epc_bytes[i]:02X}{epc_bytes[i+1]:02X} = {value_be} (big-endian)")
        
        if value_le == expected_id:
            matches.append({
                'position': i,
                'bytes': f"{epc_bytes[i]:02X} {epc_bytes[i+1]:02X}",
                'endian': 'little',
                'method': f"bytes[{i}:{i+2}] little-endian"
            })
            print(f"   ✅ Posición {i}-{i+1}: 0x{epc_bytes[i+1]:02X}{epc_bytes[i]:02X} = {value_le} (little-endian)")
    
    # Probar combinaciones de 3 bytes
    for i in range(len(epc_bytes) - 2):
        value = (epc_bytes[i] << 16) | (epc_bytes[i+1] << 8) | epc_bytes[i+2]
        if value == expected_id:
            matches.append({
                'position': i,
                'bytes': f"{epc_bytes[i]:02X} {epc_bytes[i+1]:02X} {epc_bytes[i+2]:02X}",
                'endian': 'big',
                'method': f"bytes[{i}:{i+3}] 3-byte"
            })
            print(f"   ✅ Posición {i}-{i+2}: 0x{epc_bytes[i]:02X}{epc_bytes[i+1]:02X}{epc_bytes[i+2]:02X} = {value} (3-byte)")
    
    # Probar byte individual (si el ID cabe en 1 byte)
    if expected_id < 256:
        for i in range(len(epc_bytes)):
            if epc_bytes[i] == expected_id:
                matches.append({
                    'position': i,
                    'bytes': f"{epc_bytes[i]:02X}",
                    'endian': 'n/a',
                    'method': f"byte[{i}] single"
                })
                print(f"   ✅ Posición {i}: 0x{epc_bytes[i]:02X} = {epc_bytes[i]} (single byte)")
    
    if not matches:
        print(f"   ❌ No se encontró {expected_id} en ninguna posición")
        
        # Mostrar valores cercanos
        print(f"\n   🔎 Valores cercanos a {expected_id}:")
        for i in range(len(epc_bytes) - 1):
            value = (epc_bytes[i] << 8) | epc_bytes[i+1]
            diff = abs(value - expected_id)
            if diff < 100:
                print(f"      Pos {i}-{i+1}: {value} (diff: {diff})")
    
    return matches


def analyze_pattern(test_cases):
    """Analizar patrón común entre varios chips"""
    print("\n" + "=" * 80)
    print("📊 ANÁLISIS DE PATRÓN COMÚN")
    print("=" * 80)
    
    all_matches = {}
    
    for epc, expected_id in test_cases:
        matches = find_id_in_epc(epc, expected_id)
        if matches:
            for match in matches:
                key = (match['position'], match['endian'])
                if key not in all_matches:
                    all_matches[key] = 0
                all_matches[key] += 1
    
    print("\n" + "=" * 80)
    print("🎯 RESUMEN DE COINCIDENCIAS")
    print("=" * 80)
    
    if all_matches:
        print(f"\n✅ Posiciones que coinciden en múltiples chips:")
        for (pos, endian), count in sorted(all_matches.items(), key=lambda x: -x[1]):
            print(f"   Posición {pos}-{pos+1} ({endian}-endian): {count}/{len(test_cases)} coincidencias")
        
        # Encontrar la posición más común
        best_match = max(all_matches.items(), key=lambda x: x[1])
        (best_pos, best_endian), best_count = best_match
        
        if best_count == len(test_cases):
            print(f"\n🎉 ¡PATRÓN ENCONTRADO!")
            print(f"   El ID siempre está en: bytes[{best_pos}:{best_pos+2}] ({best_endian}-endian)")
            return best_pos, best_endian
        else:
            print(f"\n⚠️  Patrón parcial encontrado:")
            print(f"   Mejor coincidencia: bytes[{best_pos}:{best_pos+2}] ({best_endian}-endian)")
            print(f"   Funciona en {best_count}/{len(test_cases)} casos")
            return best_pos, best_endian
    else:
        print(f"\n❌ No se encontró ningún patrón común")
        return None, None


def main():
    """Test con tus chips problemáticos"""
    print("=" * 80)
    print("🔍 ANÁLISIS PROFUNDO DE CHIPS E2 Y ESPECIALES")
    print("=" * 80)
    
    # Tus chips con IDs conocidos
    test_cases = [
        ("E2 00 20 19 73 05 00 91 12 00 40 89", 36991),
        ("00 00 00 00 73 05 02 07 12 60 B8 EB", 36958),
        ("E2 00 00 19 73 05 02 82 12 30 F6 15", 36989),
        ("E2 00 00 19 73 05 02 77 12 30 F3 66", 36988),
    ]
    
    # Analizar cada uno
    for epc, expected_id in test_cases:
        find_id_in_epc(epc, expected_id)
    
    # Buscar patrón común
    pos, endian = analyze_pattern(test_cases)
    
    if pos is not None:
        print("\n" + "=" * 80)
        print("💡 SOLUCIÓN PARA EL PARSER")
        print("=" * 80)
        print(f"""
Para estos chips especiales (con patrón 73 05):
- Buscar bytes en posición: [{pos}:{pos+2}]
- Usar {endian}-endian
- Ejemplo de código:
  
  if b'\\x73\\x05' in epc_bytes:  # Detectar chip especial
      tag_bytes = epc_bytes[{pos}:{pos+2}]
      tag_id = int.from_bytes(tag_bytes, byteorder='{endian}')
""")
    
    # Análisis adicional: verificar si 73 05 es un marcador
    print("\n" + "=" * 80)
    print("🔎 ANÁLISIS DEL PATRÓN 73 05")
    print("=" * 80)
    
    for epc, expected_id in test_cases:
        epc_clean = epc.replace(" ", "")
        epc_bytes = bytes.fromhex(epc_clean)
        
        # Buscar 73 05
        pattern = b'\x73\x05'
        if pattern in epc_bytes:
            pos_pattern = epc_bytes.index(pattern)
            print(f"\nChip {expected_id}:")
            print(f"  Patrón 73 05 en posición: {pos_pattern}")
            print(f"  Bytes después del patrón: {epc_bytes[pos_pattern+2:].hex(' ').upper()}")


if __name__ == "__main__":
    main()