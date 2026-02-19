"""
Scanner avanzado para YR8900 con control eficiente de múltiples antenas
Versión refactorizada - Integrado con YR8900Protocol
"""

import time
from datetime import datetime
from colorama import init, Fore
from .tag_parser import TagParser
from hardware.yr8900_protocol import YR8900Protocol, CommandCodes
from hardware.antenna_detection import AntennaDetector
from config import ReaderConfig
from .tag_parser import TagParser # Importar parser híbrido

init(autoreset=True)


class AdvancedYR8900Scanner:
    """Scanner avanzado con control completo del YR8900"""
    
    def __init__(self, host="192.168.0.178", port=4001):
        # Crear config y protocol
        self.config = ReaderConfig(host=host, port=port)
        self.protocol = YR8900Protocol(self.config)
        self.antenna_detector = AntennaDetector(self.protocol)
        
        self.parser = TagParser(debug=False)  # Usar parser híbrido

        self.connected = False
        self.parser = TagParser()
        self.current_antenna = None
        self.available_antennas = []
        
    # ========================================
    # CONEXIÓN Y COMUNICACIÓN
    # ========================================
    
    def connect(self):
        """Conectar al lector usando protocol"""
        try:
            print(f"{Fore.BLUE}[INFO] Conectando a {self.config.host}:{self.config.port}...")
            
            # Test de conexión
            result = self.protocol.send_command(CommandCodes.GET_FIRMWARE_VERSION)
            
            if not result.get("valid"):
                print(f"{Fore.RED}[ERROR] Error de conexión: {result.get('error')}")
                return False
            
            if result.get("data") and len(result["data"]) >= 2:
                major, minor = result["data"][0], result["data"][1]
                firmware = f"{major}.{minor}"
                print(f"{Fore.GREEN}[SUCCESS] Conectado - Firmware v{firmware}")
                self.connected = True
                return True
            
            return False
            
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Error de conexión: {e}")
            return False
    
    def disconnect(self):
        """Desconectar del lector"""
        self.connected = False
        print(f"{Fore.BLUE}[INFO] Desconectado")
    
    # ========================================
    # COMANDOS BÁSICOS DEL HARDWARE
    # ========================================
    
    def get_firmware_version(self):
        """Obtener versión del firmware"""
        result = self.protocol.send_command(CommandCodes.GET_FIRMWARE_VERSION)
        
        if result.get("valid") and result.get("data") and len(result["data"]) >= 2:
            major, minor = result["data"][0], result["data"][1]
            return f"{major}.{minor}"
        return None
    
    def get_reader_temperature(self):
        """Obtener temperatura del lector"""
        result = self.protocol.send_command(CommandCodes.GET_READER_TEMPERATURE)
        
        if result.get("valid") and result.get("data") and len(result["data"]) >= 2:
            sign = result["data"][0]
            temp = result["data"][1]
            return temp if sign == 0x01 else -temp
        return None
    
    def get_current_antenna(self):
        """Obtener antena actualmente configurada"""
        result = self.protocol.send_command(CommandCodes.GET_WORK_ANTENNA)
        
        if result.get("valid") and result.get("data"):
            antenna_port = result["data"][0] + 1  # Base 0 → Base 1
            self.current_antenna = antenna_port
            return antenna_port
        return None
    
    def set_work_antenna(self, antenna_id):
        """
        Configurar antena de trabajo
        
        Args:
            antenna_id: Puerto (0-7) o (1-8) - se detecta automáticamente
        """
        # Detectar si es base 0 o base 1
        if antenna_id >= 1:
            port = antenna_id  # Base 1 (1-8)
        else:
            port = antenna_id + 1  # Base 0 (0-7) → Base 1
        
        if not 1 <= port <= 8:
            print(f"{Fore.RED}Error: Puerto fuera de rango: {port} (debe ser 1-8)")
            return False
        
        try:
            print(f"{Fore.CYAN}DEBUG: Cambiando a puerto {port}...")
            
            result = self.protocol.send_command(
                CommandCodes.SET_WORK_ANTENNA,
                [port - 1]  # Convertir a base 0 para el protocolo
            )
            
            if result.get("valid"):
                self.current_antenna = port
                print(f"{Fore.GREEN}✓ Antena {port} activada")
                return True
            else:
                print(f"{Fore.RED}✗ Error activando antena {port}: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"{Fore.RED}Error: {e}")
            return False
    
    def get_output_power(self):
        """Obtener potencia de salida"""
        result = self.protocol.send_command(CommandCodes.GET_OUTPUT_POWER)
        
        if result.get("valid") and result.get("data"):
            return result["data"][0]
        return None
    
    def set_output_power(self, power_dbm):
        """Configurar potencia de salida (0-33 dBm)"""
        if not (0 <= power_dbm <= 33):
            print(f"{Fore.RED}Error: Potencia debe estar entre 0-33 dBm")
            return False
        
        result = self.protocol.send_command(
            CommandCodes.SET_OUTPUT_POWER,
            [power_dbm]
        )
        
        return result.get("valid", False)
    
    # ========================================
    # DETECCIÓN DE ANTENAS
    # ========================================
    
    def detect_connected_antennas(self):
        """Detecta qué antenas están físicamente conectadas usando return loss"""
        print(f"\n{Fore.CYAN}=== DETECTANDO ANTENAS CONECTADAS ===")
        
        results = self.antenna_detector.scan_all_ports()
        
        # Extraer puertos conectados
        connected = [port for port, (is_connected, _) in results.items() if is_connected]
        self.available_antennas = connected
        
        print(f"\n{Fore.GREEN}Antenas detectadas: {connected}")
        print(f"{Fore.GREEN}Total: {len(connected)}/8 antenas")
        
        return connected
    
    # ========================================
    # PARSING DE RESPUESTAS
    # ========================================
    
    def split_concatenated_packets(self, data):
        """Separa paquetes concatenados"""
        packets = []
        i = 0
        
        while i < len(data):
            if data[i] == 0xA0 and i + 1 < len(data):
                length = data[i + 1]
                packet_end = i + length + 2
                
                if packet_end <= len(data):
                    packet = data[i:packet_end]
                    packets.append(packet)
                    i = packet_end
                else:
                    packet = data[i:]
                    if len(packet) >= 4:
                        packets.append(packet)
                    break
            else:
                i += 1
        
        return packets
    
    def parse_scan_response_robust(self, response):
        """Parsing robusto con soporte para múltiples paquetes"""
        tags = []
        packets = self.split_concatenated_packets(response)
        
        for packet in packets:
            if len(packet) >= 10:
                if packet[0] == 0xA0 and packet[3] == 0x8B:
                    expected_length = packet[1]
                    if len(packet) >= expected_length + 2:
                        freq_ant = packet[4]
                        pc1 = packet[5]
                        pc2 = packet[6]
                        epc_end = expected_length + 1
                        epc_data = packet[7:epc_end]
                        
                        if len(epc_data) > 0:
                            # DEBUG: Mostrar bytes raw del EPC
                            epc_hex = ' '.join(f'{b:02x}' for b in epc_data)
                            print(f"{Fore.CYAN}DEBUG TCP/IP - EPC raw: [{epc_hex}]")

                            tag_number = self.parser.extract_tag_number(epc_data)
                            print(f"{Fore.CYAN}DEBUG TCP/IP - extract_tag_number() → '{tag_number}'")

                            # Normalizar ID para consistencia con USB scanner
                            if tag_number:
                                tag_number_before = tag_number
                                tag_number = self.parser.normalize_tag_id(tag_number)
                                print(f"{Fore.CYAN}DEBUG TCP/IP - normalize_tag_id() '{tag_number_before}' → '{tag_number}'")

                            if tag_number and tag_number != "N/A":
                                # ⭐ CRÍTICO: freq_ant ya contiene el puerto correcto
                                # NO hacer & 0x03 porque eso da valores 0-3
                                # El hardware reporta directamente el índice de antena usado
                                
                                # El freq_ant contiene: [frecuencia en bits altos][antena en bits bajos]
                                # Extraer solo los 2 bits bajos para la antena (0-3 en base 0)
                                antenna_index = freq_ant & 0x03  # Esto da 0,1,2,3
                                
                                # ⭐ PERO el scanner usa set_work_antenna(port) donde port es 1-8
                                # Cuando hacemos set_work_antenna(2), el lector usa índice 1 (base 0)
                                # Entonces: índice 1 → puerto 2
                                antenna_port = antenna_index + 1  # Convertir a base 1
                                
                                # ⭐ WAIT - Esto no coincide con tu debug
                                # Tu debug dice "antena 2" pero DetectionTab recibe "1"
                                # Significa que el problema está en OTRO lado
                                
                                # ⭐ SOLUCIÓN: Usar el puerto que SABEMOS que se activó
                                # Si acabamos de hacer set_work_antenna(2), el tag es del puerto 2
                                antenna_port = self.current_antenna  # ⭐ USAR ESTE
                                
                                tag_info = {
                                    'freq_ant': freq_ant,
                                    'pc': f"{pc1:02x} {pc2:02x}",
                                    'epc_hex': ''.join(f'{b:02x}' for b in epc_data),
                                    'number': tag_number,
                                    'antenna': antenna_port,  # ⭐ Usar current_antenna
                                    'timestamp': datetime.now()
                                }
                                
                                # Debug
                                print(f"  ✓ Tag: {tag_number} en antena {antenna_port}")
                                
                                tags.append(tag_info)
        
        return tags
    
    # ========================================
    # MÉTODOS DE SCANNING
    # ========================================
    
    def scan_single_antenna(self, antenna_id=None):
        """
        Scan en una antena específica
        
        Args:
            antenna_id: Puerto a escanear (1-8) o None para usar antena actual
        """
        if not self.connected:
            print("ERROR: No conectado")
            return []
        
        # Cambiar a la antena especificada
        if antenna_id is not None:
            if not self.set_work_antenna(antenna_id):
                print(f"ERROR: No se pudo activar antena {antenna_id}")
                return []
            time.sleep(0.1)  # Pausa para estabilización
        
        try:
            # Usar el comando INVENTORY del protocolo
            result = self.protocol.send_command(
                CommandCodes.INVENTORY,
                [0x01, 0x00, 0x01],  # Parámetros estándar
                timeout=2.0
            )
            
            if not result.get("valid"):
                print(f"DEBUG: No hay respuesta válida")
                return []
            
            # Obtener datos raw de la respuesta
            raw_response = bytes.fromhex(result.get("raw", ""))
            
            if len(raw_response) > 12:
                tags = self.parse_scan_response_robust(raw_response)
                
                for tag in tags:
                    print(f"  ✓ Tag: {tag['number']} en antena {antenna_id or self.current_antenna}")
                
                return tags
            
            return []
            
        except Exception as e:
            print(f"ERROR escaneando: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def continuous_scan_multi_antenna(self, duration=10):
        """Scan continuo alternando entre antenas"""
        if not self.available_antennas:
            print(f"{Fore.YELLOW}[WARNING] No hay antenas detectadas. Detectando...")
            self.detect_connected_antennas()
            
            if not self.available_antennas:
                print(f"{Fore.RED}[ERROR] No se detectaron antenas")
                return []
        
        unique_tags = {}
        start_time = time.time()
        scan_count = 0
        
        print(f"\n{Fore.CYAN}=== SCAN CONTINUO MULTI-ANTENA ===")
        print(f"{Fore.CYAN}Antenas activas: {self.available_antennas}")
        print(f"{Fore.CYAN}Duración: {duration}s")
        print(f"{Fore.YELLOW}Presiona Ctrl+C para detener\n")
        
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
                        print(f"{Fore.GREEN}[{len(unique_tags):03d}] Nuevo tag: {tag_number} (antena {antenna_id})")
                
                time.sleep(0.3)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[INFO] Scan interrumpido")
        
        return list(unique_tags.values())
    
    # ========================================
    # MÉTODOS DE COMPATIBILIDAD CON GUI
    # ========================================
    
    def scan_with_parsing(self):
        """Scan simple con parsing - Compatibilidad con GUI"""
        return self.scan_single_antenna()
    
    def continuous_scan_simple(self, duration):
        """Scan continuo simple - Compatibilidad con GUI"""
        return self.continuous_scan_multi_antenna(duration)
    
    def test_original_command(self):
        """Test básico de comandos - Para debugging"""
        result = self.protocol.send_command(CommandCodes.GET_FREQUENCY_REGION)
        return result.get("valid", False)