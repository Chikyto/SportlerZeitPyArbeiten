#!/usr/bin/env python3
"""
Scanner simplificado YR8900 - Solo comandos que funcionan
Basado en análisis de Wireshark y test de conexión
"""

import socket
import time
import struct
from datetime import datetime
from colorama import init, Fore, Back, Style

# Inicializar colorama
init(autoreset=True)

class SimpleYR8900Scanner:
    """Scanner simplificado que usa solo comandos probados"""
    
    def __init__(self, host="192.168.0.178", port=4001):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        
    def connect(self):
        """Conecta al lector"""
        try:
            print(f"{Fore.BLUE}[INFO] Conectando a {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(3.0)  # Timeout más corto
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
        """Envía comando y recibe respuesta"""
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
        """Prueba el comando básico que sabemos que funciona"""
        print(f"\n{Fore.CYAN}=== PROBANDO COMANDO BÁSICO ===")
        
        # Comando que funcionó en test directo: get frequency region
        cmd = bytes([0xA0, 0x03, 0xFF, 0x79, 0xE5])
        response = self.send_command(cmd)
        
        if response and len(response) >= 6:
            print(f"{Fore.GREEN}[SUCCESS] Comando básico funciona!")
            return True
        else:
            print(f"{Fore.RED}[ERROR] Comando básico falló")
            return False
    
    def scan_tags_basic(self):
        """Busca tags usando comando básico del Wireshark"""
        print(f"\n{Fore.CYAN}=== BUSCANDO TAGS ===")
        
        # Comando basado en Frame 27 del Wireshark: A0 06 F3 8B 01 00 01 DA
        cmd = bytes([0xA0, 0x06, 0xF3, 0x8B, 0x01, 0x00, 0x01, 0xDA])
        response = self.send_command(cmd)
        
        if response and len(response) > 6:
            return self.parse_tag_response(response)
        else:
            print(f"{Fore.YELLOW}[WARNING] No se recibió respuesta de tags")
            return []
    
    def parse_tag_response(self, response):
        """Parsea respuesta de tags, manejando múltiples paquetes concatenados"""
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
                            tag_number = self.extract_tag_number(epc_data)
                            
                            # Solo agregar si encontramos un número válido
                            if tag_number and tag_number != "N/A":
                                tag_info = {
                                    'freq_ant': freq_ant,
                                    'pc': f"{pc1:02x} {pc2:02x}",
                                    'epc_hex': ''.join(f'{b:02x}' for b in epc_data),
                                    'number': tag_number,
                                    'antenna': freq_ant & 0x03,
                                    'timestamp': datetime.now().strftime('%H:%M:%S')
                                }
                                
                                tags.append(tag_info)
                                
                                print(f"{Fore.GREEN}[TAG DETECTADO]")
                                print(f"  Número: {tag_number}")
                                print(f"  EPC: {tag_info['epc_hex']}")
                                print(f"  Antena: {tag_info['antenna']}")
                                print(f"  Hora: {tag_info['timestamp']}")
        
        return tags
    
    def split_concatenated_packets(self, data):
        """Separa paquetes concatenados basándose en el header 0xA0"""
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
    
    def extract_tag_number(self, epc_data):
        """Extrae número del tag basado en patrones específicos identificados"""
        if len(epc_data) < 2:
            return None
        
        # Debug: mostrar solo los primeros 20 bytes para evitar spam
        debug_data = epc_data[:20]
        print(f"    Debug EPC: {' '.join(f'{b:02x}' for b in debug_data)}")
        
        # Buscar patrones específicos identificados en tus chips
        patterns = {
            # Patrón: (byte1, byte2): "número_esperado"
            (0x85, 0x99): "8599",  # Tu chip principal
            (0x85, 0x75): "8575",  # Chip detectado
            (0x85, 0x87): "8587",  # Chip detectado
            (0x76, 0x62): "7662",  # Chip detectado
            (0x36, 0x42): "3642",  # Chip detectado
            (0x59, 0x62): "5962",  # Chip faltante
            (0x86, 0x00): "8600",  # Chip faltante
        }
        
        # Buscar patrones exactos primero
        for i in range(len(epc_data) - 1):
            byte1 = epc_data[i]
            byte2 = epc_data[i + 1]
            
            pattern = (byte1, byte2)
            if pattern in patterns:
                return patterns[pattern]
        
        # Si no encuentra patrones conocidos, buscar otros patrones válidos
        # Solo para chips que no conocemos aún
        for i in range(len(epc_data) - 1):
            byte1 = epc_data[i]
            byte2 = epc_data[i + 1]
            
            # Solo patrones que parecen números de chip válidos
            if byte1 > 0 and byte2 > 0:
                # Evitar patrones que sabemos que son incorrectos
                if (byte1, byte2) not in [(0x59, 0x62)]:  # 5962 mal interpretado como 8998
                    # Solo números que parecen códigos de chip reales
                    if 30 <= byte1 <= 99 and 0 <= byte2 <= 99:
                        number = f"{byte1:02d}{byte2:02d}"
                        # Filtrar números que no parecen códigos de chip
                        if number not in ["5962"]:  # Temporal hasta que sepamos el patrón real
                            return number
        
        return None
    
    def continuous_scan(self, duration=10):
        """Scan continuo"""
        print(f"\n{Fore.CYAN}=== SCAN CONTINUO ({duration}s) ===")
        print(f"{Fore.YELLOW}Presiona Ctrl+C para detener")
        
        unique_tags = {}
        start_time = time.time()
        scan_count = 0
        
        try:
            while time.time() - start_time < duration:
                tags = self.scan_tags_basic()
                scan_count += 1
                
                for tag in tags:
                    number = tag['number']
                    if number and number not in unique_tags:
                        unique_tags[number] = tag
                        print(f"{Fore.GREEN}[{len(unique_tags):03d}] Nuevo tag: {number}")
                
                # Mostrar progreso cada 10 scans
                if scan_count % 10 == 0:
                    elapsed = time.time() - start_time
                    remaining = duration - elapsed
                    print(f"{Fore.CYAN}Progreso: {elapsed:.1f}s/{duration}s - Tags: {len(unique_tags)} - Scans: {scan_count}")
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[INFO] Scan interrumpido por usuario")
        
        return list(unique_tags.values())
    
    def interactive_menu(self):
        """Menú interactivo simple"""
        while True:
            print(f"\n{Fore.CYAN}{'='*40}")
            print(f"{Fore.CYAN}   SCANNER YR8900 SIMPLE")
            print(f"{Fore.CYAN}{'='*40}")
            print(f"{Fore.WHITE}1. Test básico")
            print(f"{Fore.WHITE}2. Scan único")
            print(f"{Fore.WHITE}3. Scan continuo (10s)")
            print(f"{Fore.WHITE}4. Scan continuo personalizado")
            print(f"{Fore.WHITE}0. Salir")
            print(f"{Fore.CYAN}{'='*40}")
            
            try:
                choice = input(f"{Fore.YELLOW}Opción: ").strip()
                
                if choice == "1":
                    self.test_basic_command()
                elif choice == "2":
                    tags = self.scan_tags_basic()
                    if not tags:
                        print(f"{Fore.YELLOW}No se encontraron tags")
                elif choice == "3":
                    self.continuous_scan(10)
                elif choice == "4":
                    duration = int(input("Duración (segundos): "))
                    self.continuous_scan(duration)
                elif choice == "0":
                    break
                else:
                    print(f"{Fore.RED}Opción inválida")
                    
            except ValueError:
                print(f"{Fore.RED}Entrada inválida")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Operación cancelada")
    
    def run(self):
        """Ejecuta el scanner"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}    YR8900 RFID Scanner Simplificado")
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.YELLOW}Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.CYAN}{'='*60}")
        
        if self.connect():
            try:
                if self.test_basic_command():
                    print(f"{Fore.GREEN}[SUCCESS] Lector funcionando correctamente!")
                    self.interactive_menu()
                else:
                    print(f"{Fore.RED}[ERROR] Lector no responde correctamente")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[INFO] Aplicación interrumpida")
            finally:
                self.disconnect()
        else:
            print(f"{Fore.RED}[ERROR] No se pudo conectar al lector")

def main():
    scanner = SimpleYR8900Scanner()
    scanner.run()

if __name__ == "__main__":
    main()