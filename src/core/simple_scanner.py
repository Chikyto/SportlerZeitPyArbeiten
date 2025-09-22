import socket
import time
from datetime import datetime
from colorama import init, Fore

from .config import RFID_HOST, RFID_PORT, RFID_TIMEOUT
from .tag_parser import TagParser

# Inicializar colorama
init(autoreset=True)

class SimpleScanner:
    """Scanner básico que mantiene tu código que funciona"""
    
    def __init__(self, host=RFID_HOST, port=RFID_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.parser = TagParser()
        
    def connect(self):
        """Conecta al lector - MANTIENE tu lógica exacta"""
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
        """Desconecta del lector"""
        if self.socket:
            self.socket.close()
            self.socket = None
            self.connected = False
            print(f"{Fore.BLUE}[INFO] Desconectado")
    
    def send_command(self, command_bytes):
        """Envía comando - MANTIENE tu lógica exacta"""
        if not self.connected:
            return None
            
        try:
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
    
    def test_basic_command(self):
        """Test básico - MANTIENE tu comando que funciona"""
        print(f"\n{Fore.CYAN}=== PROBANDO COMANDO BÁSICO ===")
        
        # Tu comando que funciona
        cmd = bytes([0xA0, 0x03, 0xFF, 0x79, 0xE5])
        response = self.send_command(cmd)
        
        if response and len(response) >= 6:
            print(f"{Fore.GREEN}[SUCCESS] Comando básico funciona!")
            return True
        else:
            print(f"{Fore.RED}[ERROR] Comando básico falló")
            return False
    
    def scan_single(self):
        """Un scan simple - MANTIENE tu comando que funciona"""
        cmd = bytes([0xA0, 0x06, 0xF3, 0x8B, 0x01, 0x00, 0x01, 0xDA])
        response = self.send_command(cmd)
        
        if response and len(response) > 6:
            # Aquí después agregamos el parsing
            print(f"{Fore.GREEN}[INFO] Respuesta recibida, largo: {len(response)}")
            return response
        else:
            print(f"{Fore.YELLOW}[WARNING] Sin respuesta de scan")
            return None
        
    def parse_scan_response(self, response):
        """Parsea la respuesta del scan para extraer tags - MANTIENE tu lógica"""
        if not response or len(response) < 10:
            return []
        
        tags = []
        # Tu lógica de parsing exacta
        if response[0] == 0xA0 and response[3] == 0x8B:
            expected_length = response[1]
            if len(response) >= expected_length + 2:
                freq_ant = response[4]
                pc1, pc2 = response[5], response[6]
                
                # EPC data: desde posición 7 hasta expected_length
                epc_end = expected_length + 1
                epc_data = response[7:epc_end]
                
                if len(epc_data) > 0:
                    # Usar tu parser
                    tag_number = self.parser.extract_tag_number(epc_data)
                    
                    if tag_number and tag_number != "N/A":
                        tag_info = {
                            'number': tag_number,
                            'epc_hex': ''.join(f'{b:02x}' for b in epc_data),
                            'antenna': freq_ant & 0x03,
                            'timestamp': datetime.now()
                        }
                        tags.append(tag_info)
                        
                        print(f"{Fore.GREEN}[TAG DETECTADO] {tag_number}")
        
        return tags
    
    def scan_with_parsing(self):
        """Scan que retorna los tags parseados"""
        response = self.scan_single()
        if response:
            return self.parse_scan_response(response)
        return []
    
    def split_concatenated_packets(self, data):
        """Separa paquetes concatenados - MANTIENE tu lógica exacta"""
        packets = []
        i = 0
        
        while i < len(data):
            # Buscar header 0xA0
            if data[i] == 0xA0 and i + 1 < len(data):
                length = data[i + 1]
                packet_end = i + length + 2  # +2 for header and checksum
                
                # Verificar que el paquete esté completo
                if packet_end <= len(data):
                    packet = data[i:packet_end]
                    packets.append(packet)
                    i = packet_end
                else:
                    # Paquete incompleto, tomar el resto
                    packet = data[i:]
                    if len(packet) >= 4:  # Mínimo viable
                        packets.append(packet)
                    break
            else:
                i += 1
        
        return packets
    
    def parse_scan_response_robust(self, response):
        """Parsing robusto - MANTIENE tu lógica completa que funciona"""
        tags = []
        
        # Separar múltiples paquetes concatenados
        packets = self.split_concatenated_packets(response)
        
        for packet in packets:
            if len(packet) >= 10:
                # Verificar header y comando
                if packet[0] == 0xA0 and packet[3] == 0x8B:
                    # Verificar longitud del paquete
                    expected_length = packet[1]
                    if len(packet) >= expected_length + 2:  # +2 for header and checksum
                        
                        # Extraer datos del tag
                        freq_ant = packet[4]
                        pc1 = packet[5]
                        pc2 = packet[6]
                        
                        # EPC data: desde posición 7 hasta expected_length
                        epc_end = expected_length + 1  # +1 porque length no incluye header
                        epc_data = packet[7:epc_end]
                        
                        # Solo procesar si hay datos EPC válidos
                        if len(epc_data) > 0:
                            # Buscar patrón de número en EPC
                            tag_number = self.parser.extract_tag_number(epc_data)
                            
                            # Solo agregar si encontramos un número válido
                            if tag_number and tag_number != "N/A":
                                tag_info = {
                                    'freq_ant': freq_ant,
                                    'pc': f"{pc1:02x} {pc2:02x}",
                                    'epc_hex': ''.join(f'{b:02x}' for b in epc_data),
                                    'number': tag_number,
                                    'antenna': freq_ant & 0x03,
                                    'timestamp': datetime.now()
                                }
                                
                                tags.append(tag_info)
                                
                                print(f"{Fore.GREEN}[TAG DETECTADO]")
                                print(f"  Número: {tag_number}")
                                print(f"  EPC: {tag_info['epc_hex']}")
                                print(f"  Antena: {tag_info['antenna']}")
                                print(f"  Hora: {tag_info['timestamp'].strftime('%H:%M:%S')}")
        
        return tags
    
    def continuous_scan_simple(self, duration=10):
        """Scan continuo simple - MANTIENE tu lógica que funciona"""
        print(f"\n{Fore.CYAN}=== SCAN CONTINUO ({duration}s) ===")
        
        unique_tags = {}
        start_time = time.time()
        scan_count = 0
        
        try:
            while time.time() - start_time < duration:
                # Usar el comando que funciona
                cmd = bytes([0xA0, 0x06, 0xF3, 0x8B, 0x01, 0x00, 0x01, 0xDA])
                response = self.send_command(cmd)
                
                if response and len(response) > 6:
                    tags = self.parse_scan_response_robust(response)
                    scan_count += 1
                    
                    for tag in tags:
                        number = tag['number']
                        if number and number not in unique_tags:
                            unique_tags[number] = tag
                            print(f"{Fore.GREEN}[{len(unique_tags):03d}] Nuevo tag: {number}")
                
                # Pequeña pausa entre scans
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[INFO] Scan interrumpido por usuario")
        
        return list(unique_tags.values())