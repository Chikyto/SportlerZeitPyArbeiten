"""
Scanner avanzado para YR8900 con control eficiente de múltiples antenas
Incluye comandos adicionales del lector: temperatura, firmware, etc.
"""

import socket
import time
import struct
from datetime import datetime
from colorama import init, Fore
from .tag_parser import TagParser
from .config import RFID_HOST, RFID_PORT, RFID_TIMEOUT

init(autoreset=True)

class AdvancedYR8900Scanner:
    """Scanner avanzado con control completo del YR8900"""
    
    def __init__(self, host=RFID_HOST, port=RFID_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.parser = TagParser()
        self.current_antenna = 0
        self.available_antennas = [0, 1]  # Antenas conectadas (puertos 1 y 2)
        
    def connect(self):
        """Conectar al lector"""
        try:
            print(f"{Fore.BLUE}[INFO] Conectando a {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(RFID_TIMEOUT)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"{Fore.GREEN}[SUCCESS] Conectado exitosamente!")
            return True
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Error de conexión: {e}")
            return False
    
    def disconnect(self):
        """Desconectar del lector"""
        if self.socket:
            self.socket.close()
            self.socket = None
            self.connected = False
            print(f"{Fore.BLUE}[INFO] Desconectado")
    
    def send_command(self, command_bytes):
        """Enviar comando con checksum automático"""
        if not self.connected:
            return None
            
        try:
            # Calcular checksum si no está incluido
            if len(command_bytes) >= 2:
                expected_length = command_bytes[1]
                if len(command_bytes) == expected_length + 1:  # Falta checksum
                    checksum = sum(command_bytes[1:]) & 0xFF
                    command_bytes = command_bytes + bytes([checksum])
            
            print(f"{Fore.CYAN}Enviando: {' '.join(f'{b:02x}' for b in command_bytes)}")
            self.socket.send(command_bytes)
            
            response = self.socket.recv(1024)
            print(f"{Fore.CYAN}Recibido: {' '.join(f'{b:02x}' for b in response)}")
            return response
            
        except socket.timeout:
            print(f"{Fore.YELLOW}[WARNING] Timeout en comando")
            return None
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Error enviando comando: {e}")
            return None
    
    # ========================================
    # COMANDOS BÁSICOS DEL LECTOR
    # ========================================
    
    def get_firmware_version(self):
        """Obtener versión del firmware"""
        cmd = bytes([0xA0, 0x03, 0xFF, 0x72])
        response = self.send_command(cmd)
        
        if response and len(response) >= 6:
            # Parsear versión del firmware
            major = response[4]
            minor = response[5]
            version = f"{major}.{minor}"
            print(f"{Fore.GREEN}Versión del firmware: {version}")
            return version
        return None
    
    def get_reader_temperature(self):
        """Obtener temperatura del lector"""
        cmd = bytes([0xA0, 0x03, 0xFF, 0x7B])
        response = self.send_command(cmd)
        
        if response and len(response) >= 5:
            # Temperatura en grados Celsius
            temp = response[4]
            print(f"{Fore.GREEN}Temperatura del lector: {temp}°C")
            return temp
        return None
    
    def get_current_antenna(self):
        """Obtener antena actualmente configurada"""
        cmd = bytes([0xA0, 0x03, 0xF3, 0x75])
        response = self.send_command(cmd)
        
        if response and len(response) >= 5:
            antenna_id = response[4]
            print(f"{Fore.GREEN}Antena actual: {antenna_id}")
            return antenna_id
        return None
    
    def set_work_antenna(self, antenna_id):
        """Configurar antena de trabajo"""
        if antenna_id not in self.available_antennas:
            print(f"{Fore.YELLOW}[WARNING] Antena {antenna_id} no está en la lista de disponibles")
        
        cmd = bytes([0xA0, 0x04, 0xF3, 0x74, antenna_id])
        response = self.send_command(cmd)
        
        if response and len(response) >= 4:
            if response[3] == 0x10:  # Command success
                self.current_antenna = antenna_id
                print(f"{Fore.GREEN}Antena cambiada a: {antenna_id}")
                return True
            else:
                print(f"{Fore.RED}Error cambiando antena: {response[3]}")
        return False
    
    def get_output_power(self):
        """Obtener potencia de salida"""
        cmd = bytes([0xA0, 0x03, 0xFF, 0x77])
        response = self.send_command(cmd)
        
        if response and len(response) >= 5:
            power = response[4]
            print(f"{Fore.GREEN}Potencia actual: {power} dBm")
            return power
        return None
    
    def set_output_power(self, power_dbm):
        """Configurar potencia de salida (0-33 dBm)"""
        if not (0 <= power_dbm <= 33):
            print(f"{Fore.RED}Error: Potencia debe estar entre 0-33 dBm")
            return False
        
        cmd = bytes([0xA0, 0x04, 0xFF, 0x76, power_dbm])
        response = self.send_command(cmd)
        
        if response and len(response) >= 4:
            if response[3] == 0x10:  # Command success
                print(f"{Fore.GREEN}Potencia configurada a: {power_dbm} dBm")
                return True
            else:
                print(f"{Fore.RED}Error configurando potencia: {response[3]}")
        return False
    
    # ========================================
    # SCANNING EFICIENTE MULTI-ANTENA
    # ========================================
    
    def scan_single_antenna(self, antenna_id=None):
        """Scan en una antena específica"""
        if antenna_id is not None and antenna_id != self.current_antenna:
            if not self.set_work_antenna(antenna_id):
                return []
        
        # Comando de inventory estándar
        cmd = bytes([0xA0, 0x06, 0xF3, 0x8B, 0x01, 0x00, 0x01])
        response = self.send_command(cmd)
        
        if response and len(response) > 6:
            tags = self.parser.parse_tag_response(response)
            # Asegurar que todos los tags tengan la antena correcta
            for tag in tags:
                tag['antenna'] = self.current_antenna
            return tags
        return []
    
    def scan_all_antennas(self):
        """Scan eficiente en todas las antenas disponibles"""
        print(f"{Fore.CYAN}=== SCAN MULTI-ANTENA ({len(self.available_antennas)} antenas) ===")
        
        all_tags = {}
        
        for antenna_id in self.available_antennas:
            print(f"{Fore.YELLOW}Escaneando antena {antenna_id}...")
            tags = self.scan_single_antenna(antenna_id)
            
            for tag in tags:
                tag_number = tag['number']
                # Si el tag ya fue detectado, usar la primera detección
                if tag_number not in all_tags:
                    all_tags[tag_number] = tag
                    print(f"{Fore.GREEN}[TAG] {tag_number} detectado en antena {antenna_id}")
            
            # Pequeña pausa entre antenas para estabilidad
            time.sleep(0.1)
        
        return list(all_tags.values())
    
    def continuous_scan_multi_antenna(self, duration=10):
        """Scan continuo alternando entre antenas"""
        print(f"{Fore.CYAN}=== SCAN CONTINUO MULTI-ANTENA ({duration}s) ===")
        
        unique_tags = {}
        start_time = time.time()
        scan_count = 0
        
        try:
            while time.time() - start_time < duration:
                # Rotar entre antenas disponibles
                antenna_id = self.available_antennas[scan_count % len(self.available_antennas)]
                
                tags = self.scan_single_antenna(antenna_id)
                scan_count += 1
                
                for tag in tags:
                    tag_number = tag['number']
                    if tag_number not in unique_tags:
                        unique_tags[tag_number] = tag
                        print(f"{Fore.GREEN}[{len(unique_tags):03d}] Nuevo: {tag_number} (Ant {antenna_id})")
                
                # Pausa entre scans
                time.sleep(0.3)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[INFO] Scan interrumpido por usuario")
        
        print(f"{Fore.CYAN}Scan completado: {len(unique_tags)} tags únicos en {scan_count} scans")
        return list(unique_tags.values())
    
    # ========================================
    # COMANDOS DE DIAGNÓSTICO
    # ========================================
    
    def system_diagnostics(self):
        """Ejecutar diagnóstico completo del sistema"""
        print(f"\n{Fore.CYAN}=== DIAGNÓSTICO DEL SISTEMA YR8900 ===")
        
        results = {}
        
        # Información básica
        results['firmware'] = self.get_firmware_version()
        results['temperature'] = self.get_reader_temperature()
        results['current_antenna'] = self.get_current_antenna()
        results['output_power'] = self.get_output_power()
        
        # Test de conectividad de antenas
        results['antenna_tests'] = {}
        original_antenna = self.current_antenna
        
        for antenna_id in range(4):  # Test antenas 0-3
            print(f"\n{Fore.YELLOW}Probando antena {antenna_id}...")
            if self.set_work_antenna(antenna_id):
                # Hacer un scan rápido
                tags = self.scan_single_antenna(antenna_id)
                results['antenna_tests'][antenna_id] = {
                    'connected': True,
                    'tags_detected': len(tags)
                }
                print(f"  - Antena {antenna_id}: OK ({len(tags)} tags)")
            else:
                results['antenna_tests'][antenna_id] = {
                    'connected': False,
                    'tags_detected': 0
                }
                print(f"  - Antena {antenna_id}: ERROR")
        
        # Restaurar antena original
        self.set_work_antenna(original_antenna)
        
        # Resumen
        print(f"\n{Fore.CYAN}=== RESUMEN DIAGNÓSTICO ===")
        print(f"Firmware: {results['firmware']}")
        print(f"Temperatura: {results['temperature']}°C")
        print(f"Potencia: {results['output_power']} dBm")
        
        working_antennas = [ant_id for ant_id, test in results['antenna_tests'].items() 
                           if test['connected']]
        print(f"Antenas funcionando: {working_antennas}")
        
        return results
    
    def get_reader_info(self):
        """Obtener información completa del lector"""
        if not self.connected:
            return None
            
        info = {
            'host': self.host,
            'port': self.port,
            'connected': self.connected,
            'firmware': self.get_firmware_version(),
            'temperature': self.get_reader_temperature(),
            'current_antenna': self.get_current_antenna(),
            'output_power': self.get_output_power(),
            'available_antennas': self.available_antennas
        }
        
        return info
    
    def test_current_antenna_only(self):
        """Test solo con la antena actualmente activa"""
        print(f"\n{Fore.CYAN}=== TEST ANTENA ACTUAL ===")
        
        # Usar el comando que sabemos que funciona
        cmd = bytes([0xA0, 0x06, 0xF3, 0x8B, 0x01, 0x00, 0x01, 0xDA])
        response = self.send_command(cmd)
        
        if response and len(response) > 6:
            tags = self.parser.parse_tag_response(response)
            print(f"Tags detectados en antena actual: {len(tags)}")
            
            for tag in tags:
                freq_ant = tag.get('freq_ant', 0)
                antenna_reported = freq_ant & 0x03
                print(f"  - Chip {tag['number']} reporta antena: {antenna_reported}")
            
            return tags
        return []


        # Agregar al AdvancedYR8900Scanner
    def scan_with_parsing(self):
        """Compatibilidad con la GUI existente"""
        return self.scan_single_antenna()

    def continuous_scan_simple(self, duration):
        """Compatibilidad con la GUI existente"""
        return self.continuous_scan_multi_antenna(duration)
        
    def test_individual_antennas(self):
        """Test de antenas - versión adaptada"""
        print(f"\n{Fore.CYAN}=== DIAGNÓSTICO DE ANTENAS ===")
        
        # Primero test con antena actual
        self.test_current_antenna_only()
        
        # Los comandos 0x74/0x75 no funcionan en este lector
        print(f"\n{Fore.YELLOW}[INFO] Los comandos de cambio de antena no están soportados")
        print(f"[INFO] El lector usa configuración de hardware para antenas")
        """Test individual de cada antena"""
        print(f"\n{Fore.CYAN}=== TEST INDIVIDUAL DE ANTENAS ===")
        
        original_antenna = self.get_current_antenna()
        
        for antenna_id in [0, 1, 2, 3]:
            print(f"\n{Fore.YELLOW}Probando antena {antenna_id}:")
            
            # Intentar configurar antena
            if self.set_work_antenna(antenna_id):
                # Hacer scan simple
                tags = self.scan_single_antenna(antenna_id)
                print(f"  ✓ Antena {antenna_id}: {len(tags)} chips detectados")
                
                for tag in tags:
                    print(f"    - Chip {tag['number']}")
            else:
                print(f"  ✗ Antena {antenna_id}: Error de configuración")
            
            time.sleep(0.5)  # Pausa entre tests
        
        # Restaurar antena original si es posible
        if original_antenna is not None:
            self.set_work_antenna(original_antenna)