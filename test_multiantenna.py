#!/usr/bin/env python3
"""
Test simple para verificar scan multi-antena
Versión integrada con YR8900Protocol
"""

import sys
import time
from colorama import init, Fore

# Importar scanner refactorizado
from src.core.advanced_scanner import AdvancedYR8900Scanner

init(autoreset=True)

def test_multiantena():
    """Test básico de múltiples antenas"""
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}   TEST MULTI-ANTENA YR8900")
    print(f"{Fore.CYAN}{'='*60}\n")
    
    scanner = AdvancedYR8900Scanner()
    
    # 1. Conectar
    if not scanner.connect():
        print(f"{Fore.RED}ERROR: No se pudo conectar")
        return
    
    try:
        # 2. Test básico
        print(f"\n{Fore.YELLOW}[Paso 1] Test de conexión...")
        if scanner.test_original_command():
            print(f"{Fore.GREEN}✓ Lector respondiendo correctamente")
        else:
            print(f"{Fore.RED}✗ Lector no responde")
            return
        
        # 3. Detectar antenas conectadas
        print(f"\n{Fore.YELLOW}[Paso 2] Detectando antenas conectadas...")
        connected_antennas = scanner.detect_connected_antennas()
        
        if not connected_antennas:
            print(f"{Fore.RED}ERROR: No se detectaron antenas conectadas")
            return
        
        # 4. Test individual de cada antena
        print(f"\n{Fore.YELLOW}[Paso 3] Probando cada antena individualmente...")
        print(f"{Fore.CYAN}Pon un tag cerca de cada antena cuando se lo indique\n")
        
        for ant_id in connected_antennas:
            print(f"\n{Fore.CYAN}--- ANTENA (Puerto {ant_id}) ---")
            print(f"{Fore.YELLOW}Acerca un tag a la antena puerto {ant_id} AHORA...")
            print(f"{Fore.YELLOW}Escaneando durante 3 segundos...\n")
            
            tags_found = set()
            start_time = time.time()
            
            while time.time() - start_time < 3:
                tags = scanner.scan_single_antenna(ant_id)
                for tag in tags:
                    tags_found.add(tag['number'])
                time.sleep(0.3)
            
            if tags_found:
                print(f"{Fore.GREEN}✓ Detectados {len(tags_found)} tags: {', '.join(tags_found)}")
            else:
                print(f"{Fore.YELLOW}✗ No se detectaron tags en esta antena")
        
        # 5. Scan continuo rotando antenas
        print(f"\n{Fore.YELLOW}[Paso 4] Scan continuo multi-antena...")
        print(f"{Fore.CYAN}Escaneando todas las antenas durante 10 segundos...")
        print(f"{Fore.CYAN}Mueve tags entre diferentes antenas para probar\n")
        
        all_detections = {}
        start_time = time.time()
        scan_count = 0
        
        while time.time() - start_time < 10:
            # Rotar entre antenas
            ant_id = connected_antennas[scan_count % len(connected_antennas)]
            tags = scanner.scan_single_antenna(ant_id)
            
            for tag in tags:
                tag_num = tag['number']
                if tag_num not in all_detections:
                    all_detections[tag_num] = []
                all_detections[tag_num].append(ant_id)
                print(f"{Fore.GREEN}[{len(all_detections):02d}] Tag {tag_num} → Puerto {ant_id}")
            
            scan_count += 1
            time.sleep(0.3)
        
        # 6. Resumen
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}   RESUMEN")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.WHITE}Antenas conectadas: {len(connected_antennas)}")
        print(f"{Fore.WHITE}Puertos: {connected_antennas}")
        print(f"{Fore.WHITE}Tags únicos detectados: {len(all_detections)}")
        print(f"{Fore.WHITE}Total de scans: {scan_count}\n")
        
        if all_detections:
            print(f"{Fore.CYAN}Detalle de tags:")
            for tag_num, antennas in all_detections.items():
                unique_antennas = set(antennas)
                print(f"  {Fore.WHITE}• Tag {tag_num}: detectado en puerto(s) {', '.join(map(str, unique_antennas))}")
        
        print(f"\n{Fore.GREEN}✓ Test completado exitosamente!")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrumpido por usuario")
    
    finally:
        scanner.disconnect()

if __name__ == "__main__":
    test_multiantena()