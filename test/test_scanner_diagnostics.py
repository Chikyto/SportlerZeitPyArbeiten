"""
Tests y diagnósticos del scanner RFID YR8900
"""
import time
from colorama import Fore
from src.core.advanced_scanner import AdvancedYR8900Scanner


class ScannerDiagnostics:
    """Herramientas de diagnóstico para el scanner"""
    
    def __init__(self, scanner: AdvancedYR8900Scanner):
        self.scanner = scanner
    
    def test_firmware_version(self):
        """Test de versión de firmware"""
        print(f"\n{Fore.CYAN}=== TEST: Firmware Version ===")
        version = self.scanner.get_firmware_version()
        
        if version:
            print(f"{Fore.GREEN}✓ Firmware: v{version}")
            return True
        else:
            print(f"{Fore.RED}✗ No se pudo obtener versión")
            return False
    
    def test_temperature(self):
        """Test de temperatura"""
        print(f"\n{Fore.CYAN}=== TEST: Temperature ===")
        temp = self.scanner.get_reader_temperature()
        
        if temp:
            print(f"{Fore.GREEN}✓ Temperatura: {temp}°C")
            if temp > 60:
                print(f"{Fore.YELLOW}⚠ Advertencia: Temperatura alta")
            return True
        else:
            print(f"{Fore.RED}✗ No se pudo obtener temperatura")
            return False
    
    def test_antenna_switching(self):
        """Test de cambio de antenas"""
        print(f"\n{Fore.CYAN}=== TEST: Antenna Switching ===")
        
        original_antenna = self.scanner.get_current_antenna()
        print(f"Antena actual: {original_antenna}")
        
        results = {}
        for antenna_id in range(4):
            success = self.scanner.set_work_antenna(antenna_id)
            results[antenna_id] = success
            
            if success:
                print(f"{Fore.GREEN}✓ Antena {antenna_id}: OK")
            else:
                print(f"{Fore.YELLOW}✗ Antena {antenna_id}: No disponible")
            
            time.sleep(0.2)
        
        # Restaurar antena original
        if original_antenna is not None:
            self.scanner.set_work_antenna(original_antenna)
        
        return results
    
    def test_power_settings(self):
        """Test de configuración de potencia"""
        print(f"\n{Fore.CYAN}=== TEST: Power Settings ===")
        
        original_power = self.scanner.get_output_power()
        print(f"Potencia actual: {original_power} dBm")
        
        # Test cambio de potencia
        test_powers = [15, 20, 25]
        results = {}
        
        for power in test_powers:
            success = self.scanner.set_output_power(power)
            results[power] = success
            
            if success:
                actual = self.scanner.get_output_power()
                print(f"{Fore.GREEN}✓ Potencia {power} dBm: OK (actual: {actual})")
            else:
                print(f"{Fore.RED}✗ Error configurando {power} dBm")
        
        # Restaurar potencia original
        if original_power:
            self.scanner.set_output_power(original_power)
        
        return results
    
    def test_tag_detection(self, duration=5):
        """Test de detección de tags"""
        print(f"\n{Fore.CYAN}=== TEST: Tag Detection ({duration}s) ===")
        
        tags = self.scanner.continuous_scan_multi_antenna(duration)
        
        if tags:
            print(f"{Fore.GREEN}✓ {len(tags)} tag(s) detectado(s)")
            for i, tag in enumerate(tags, 1):
                print(f"  {i}. {tag['number']} (Antena {tag['antenna']})")
            return True
        else:
            print(f"{Fore.YELLOW}⚠ No se detectaron tags")
            return False
    
    def run_full_diagnostics(self):
        """Ejecutar diagnóstico completo"""
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.CYAN}DIAGNÓSTICO COMPLETO DEL SISTEMA")
        print(f"{Fore.CYAN}{'='*50}")
        
        results = {
            'firmware': self.test_firmware_version(),
            'temperature': self.test_temperature(),
            'antennas': self.test_antenna_switching(),
            'power': self.test_power_settings(),
            'detection': self.test_tag_detection()
        }
        
        # Resumen
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.CYAN}RESUMEN")
        print(f"{Fore.CYAN}{'='*50}")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"Tests pasados: {passed}/{total}")
        
        if passed == total:
            print(f"{Fore.GREEN}✓ Todos los tests pasaron")
        else:
            print(f"{Fore.YELLOW}⚠ Algunos tests fallaron")
        
        return results


# Script ejecutable
if __name__ == "__main__":
    scanner = AdvancedYR8900Scanner()
    
    if scanner.connect():
        diagnostics = ScannerDiagnostics(scanner)
        diagnostics.run_full_diagnostics()
        scanner.disconnect()
    else:
        print(f"{Fore.RED}No se pudo conectar al scanner")