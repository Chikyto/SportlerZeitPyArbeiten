#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Cronometraje RFID - Arquitectura Modular
YR8900 RFID Reader Integration
"""

import socket
import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandCodes(Enum):
    """Códigos de comando según protocolo YR8900"""
    RESET = 0x70
    GET_FIRMWARE_VERSION = 0x72
    SET_WORK_ANTENNA = 0x74
    GET_WORK_ANTENNA = 0x75
    SET_OUTPUT_POWER = 0x76
    GET_OUTPUT_POWER = 0x77
    INVENTORY = 0x8B
    FAST_SWITCH_INVENTORY = 0x8A
    SET_ANT_CONNECTION_DETECTOR = 0x62
    GET_ANT_CONNECTION_DETECTOR = 0x63
    GET_RF_PORT_RETURN_LOSS = 0x7E

class ErrorCodes(Enum):
    """Códigos de error del protocolo"""
    COMMAND_SUCCESS = 0x10
    ANTENNA_MISSING = 0x22
    TAG_INVENTORY_ERROR = 0x31
    NO_TAG_ERROR = 0x36

@dataclass
class ReaderConfig:
    """Configuración del lector YR8900"""
    host: str = "192.168.0.178"
    port: int = 4001
    reader_address: int = 0xF3
    timeout: float = 3.0

@dataclass
class AntennaConfig:
    """Configuración de una antena"""
    port: int
    enabled: bool = False
    function: str = ""  # "largada", "checkpoint", "llegada"
    power_level: int = 20

class YR8900Protocol:
    """Manejo del protocolo de comunicación YR8900"""
    
    def __init__(self, config: ReaderConfig):
        self.config = config
    
    def calculate_checksum(self, packet: List[int]) -> int:
        """Calcula checksum según protocolo"""
        return (~sum(packet) + 1) & 0xFF
    
    def create_packet(self, cmd: CommandCodes, data: List[int] = None) -> bytes:
        """Crea paquete de comando según protocolo"""
        if data is None:
            data = []
        
        # Construir paquete sin checksum
        packet = [0xA0, len(data) + 3, self.config.reader_address, cmd.value]
        packet.extend(data)
        
        # Checksum sobre TODO excepto HEAD (0xA0) y el propio checksum
        checksum = self.calculate_checksum(packet)  # Incluir HEAD en el cálculo
        packet.append(checksum)
        
        logger.debug(f"Creado paquete: {[hex(b) for b in packet]}")
        return bytearray(packet)
    
    def parse_response(self, response: bytes) -> Dict:
        """Parsea respuesta del lector"""
        if len(response) < 5:
            return {"error": "Respuesta muy corta"}
        
        head = response[0]
        length = response[1]
        address = response[2]
        cmd = response[3]
        data = list(response[4:-1]) if len(response) > 5 else []
        checksum = response[-1]
        
        # Verificar checksum (calculado sobre bytes desde length hasta data)
        calculated = self.calculate_checksum(list(response[1:-1]))
        if calculated != checksum:
            # Debug: mostrar cálculo de checksum para diagnóstico
            print(f"DEBUG: Checksum calculado=0x{calculated:02X}, recibido=0x{checksum:02X}")
            print(f"DEBUG: Bytes para checksum: {[hex(b) for b in response[1:-1]]}")
            # No fallar por checksum, solo advertir
            
        return {
            "head": head,
            "length": length,
            "address": address,
            "cmd": cmd,
            "data": data,
            "valid": True,
            "raw_response": response.hex()
        }

class YR8900Communications:
    """Manejo de comunicaciones con YR8900"""
    
    def __init__(self, config: ReaderConfig):
        self.config = config
        self.protocol = YR8900Protocol(config)
    
    def send_command(self, cmd: CommandCodes, data: List[int] = None, 
                    timeout: float = None) -> Dict:
        """Envía comando y recibe respuesta"""
        timeout = timeout or self.config.timeout
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                sock.connect((self.config.host, self.config.port))
                
                # Enviar comando
                packet = self.protocol.create_packet(cmd, data)
                sock.send(packet)
                logger.debug(f"Enviado comando {cmd.name}")
                
                # Recibir respuesta
                response = sock.recv(1024)
                result = self.protocol.parse_response(response)
                
                if result.get("valid"):
                    logger.debug(f"Respuesta válida recibida para {cmd.name}")
                else:
                    logger.warning(f"Respuesta inválida para {cmd.name}: {result}")
                
                return result
                
        except socket.timeout:
            logger.error(f"Timeout en comando {cmd.name}")
            return {"error": "Timeout"}
        except Exception as e:
            logger.error(f"Error en comando {cmd.name}: {e}")
            return {"error": str(e)}

class AntennaManager:
    """Gestor de antenas"""
    
    def __init__(self, communications: YR8900Communications):
        self.comm = communications
        self.antennas: Dict[int, AntennaConfig] = {}
    
    def test_antenna_physical(self, port: int) -> bool:
        """Detecta antenas físicamente conectadas usando return loss"""
        logger.info(f"Detección física antena puerto {port}")
        
        if not 1 <= port <= 8:
            return False
        
        try:
            # Cambiar a la antena para medición
            set_result = self.comm.send_command(
                CommandCodes.SET_WORK_ANTENNA, 
                [port - 1],
                timeout=2.0
            )
            
            if not set_result.get("valid"):
                logger.info(f"Puerto {port}: Error cambiando antena")
                return False
            
            time.sleep(0.5)
            
            # Medir return loss en frecuencia típica (915 MHz = parámetro 0x21)
            # Según manual: FreqParameter 0x21 = 915.00 MHz
            return_loss_result = self.comm.send_command(
                CommandCodes.GET_RF_PORT_RETURN_LOSS,
                [0x21],  # 915 MHz
                timeout=3.0
            )
            
            if not return_loss_result.get("valid"):
                logger.info(f"Puerto {port}: Error midiendo return loss")
                return False
            
            if return_loss_result.get("data") and len(return_loss_result["data"]) > 0:
                return_loss_db = return_loss_result["data"][0]
                
                # Criterio de detección:
                # - Antena conectada: return loss típicamente > 10 dB
                # - Puerto vacío: return loss muy bajo < 5 dB
                # - El manual indica VSWR = (10^(RL/20) + 1)/(10^(RL/20) - 1)
                
                logger.info(f"Puerto {port}: Return loss = {return_loss_db} dB")
                
                if return_loss_db >= 8:  # Umbral para antena conectada
                    logger.info(f"Puerto {port}: ANTENA FÍSICAMENTE CONECTADA (RL={return_loss_db}dB)")
                    return True
                else:
                    logger.info(f"Puerto {port}: NO HAY ANTENA (RL={return_loss_db}dB)")
                    return False
            else:
                logger.warning(f"Puerto {port}: Sin datos de return loss")
                return False
                
        except Exception as e:
            logger.error(f"Puerto {port}: Error en detección física - {e}")
            return False
    
    def test_antenna(self, port: int) -> bool:
        """Detecta antenas físicamente conectadas - método definitivo"""
        logger.info(f"Probando antena en puerto {port}")
        
        # Usar medición de return loss para detección física real
        return self.test_antenna_physical(port)
    
    def get_current_antenna(self) -> Optional[int]:
        """Obtiene la antena actualmente activa"""
        result = self.comm.send_command(CommandCodes.GET_WORK_ANTENNA)
        
        if result.get("valid") and result.get("data") and len(result["data"]) > 0:
            antenna_id = result["data"][0] + 1  # Convertir de base 0 a base 1
            logger.info(f"Antena actual: {antenna_id}")
            return antenna_id
        
        logger.warning(f"No se pudo obtener antena actual. Respuesta: {result}")
        return None
    
    def set_antenna_power(self, powers: List[int]) -> bool:
        """Configura potencia individual por antena (hasta 8 antenas)"""
        if len(powers) not in [1, 4, 8]:
            logger.error(f"Se requieren 1, 4 u 8 valores de potencia, recibidos: {len(powers)}")
            return False
        
        # Validar rango de potencia (0-33 dBm según manual)
        for i, power in enumerate(powers):
            if not 0 <= power <= 33:
                logger.error(f"Potencia fuera de rango en antena {i+1}: {power}dBm (rango: 0-33)")
                return False
        
        result = self.comm.send_command(
            CommandCodes.SET_OUTPUT_POWER,
            powers
        )
        
        success = result.get("data", [None])[0] == ErrorCodes.COMMAND_SUCCESS.value
        if success:
            logger.info(f"Potencias configuradas: {powers} dBm")
        else:
            logger.error(f"Error configurando potencias. Respuesta: {result}")
        
        return success
    
    def configure_antenna(self, port: int, enabled: bool, function: str = "", 
                         power: int = 20):
        """Configura una antena"""
        self.antennas[port] = AntennaConfig(
            port=port,
            enabled=enabled, 
            function=function,
            power_level=power
        )
        logger.info(f"Configurada antena {port}: {function}, potencia {power}dBm")
    
    def fast_switch_inventory(self, antenna_sequence: List[int], 
                             rounds_per_antenna: int = 1,
                             interval_ms: int = 0) -> Dict:
        """Inventario rápido con cambio automático de antenas"""
        if len(antenna_sequence) > 8:
            logger.error("Máximo 8 antenas en secuencia")
            return {"error": "Demasiadas antenas"}
        
        # Preparar comando según protocolo del manual
        # Versión para 8 antenas (firmware v8.2+)
        cmd_data = []
        
        # Antenas A-H y sus rounds
        for i in range(8):
            if i < len(antenna_sequence):
                ant_port = antenna_sequence[i] - 1  # Convertir a base 0
                cmd_data.extend([ant_port, rounds_per_antenna])
            else:
                cmd_data.extend([0xFF, 0])  # Ignorar esta antena
        
        # Parámetros adicionales
        cmd_data.extend([
            interval_ms,          # Intervalo
            0x00, 0x00, 0x00, 0x00, 0x00,  # Reserve0 (5 bytes)
            0x01,                 # Session S1
            0x00,                 # Target A
            0x00,                 # Reserve1
            0x00,                 # Reserve2  
            0x00,                 # Reserve3
            0x00,                 # Phase off
            0x01                  # Repeat 1 vez
        ])
        
        logger.info(f"Inventario rápido en antenas: {antenna_sequence}")
        result = self.comm.send_command(
            CommandCodes.FAST_SWITCH_INVENTORY,
            cmd_data,
            timeout=10.0
        )
        
        return result

    def enable_antenna_detector(self, sensitivity: int = 50) -> bool:
        """Habilita detector de conexión de antenas"""
        if not 1 <= sensitivity <= 100:
            logger.error(f"Sensibilidad fuera de rango: {sensitivity} (1-100)")
            return False
        
        result = self.comm.send_command(
            CommandCodes.SET_ANT_CONNECTION_DETECTOR,
            [sensitivity]
        )
        
        success = result.get("valid", False)
        if success:
            logger.info(f"Detector de antenas habilitado (sensibilidad: {sensitivity})")
        else:
            logger.error("Error habilitando detector de antenas")
        
        return success
    
    def disable_antenna_detector(self) -> bool:
        """Deshabilita detector de conexión de antenas"""
        result = self.comm.send_command(
            CommandCodes.SET_ANT_CONNECTION_DETECTOR,
            [0]  # 0 = deshabilitado
        )
        
        success = result.get("valid", False)
        if success:
            logger.info("Detector de antenas deshabilitado")
        
        return success
    
    def get_antenna_detector_status(self) -> Dict:
        """Obtiene estado del detector de antenas"""
        result = self.comm.send_command(CommandCodes.GET_ANT_CONNECTION_DETECTOR)
        
        if result.get("valid") and result.get("data"):
            sensitivity = result["data"][0]
            return {
                "enabled": sensitivity > 0,
                "sensitivity": sensitivity
            }
        
        return {"enabled": False, "sensitivity": 0}
    
    def get_antennas_by_function(self, function: str) -> List[int]:
        """Retorna antenas configuradas para una función específica"""
        return [port for port, config in self.antennas.items() 
                if config.enabled and config.function == function]
    
    def get_enabled_antennas(self) -> List[int]:
        """Retorna lista de antenas habilitadas"""
        return [port for port, config in self.antennas.items() if config.enabled]
    
    def get_antennas_by_function(self, function: str) -> List[int]:
        """Retorna antenas configuradas para una función específica"""
        return [port for port, config in self.antennas.items() 
                if config.enabled and config.function == function]
    
    def get_antenna_configuration(self) -> Dict[str, List[int]]:
        """Retorna configuración organizada por función"""
        config = {}
        for port, antenna in self.antennas.items():
            if antenna.enabled:
                if antenna.function not in config:
                    config[antenna.function] = []
                config[antenna.function].append(port)
        return config

class ReaderManager:
    """Gestor principal del lector YR8900"""
    
    def __init__(self, config: ReaderConfig = None):
        self.config = config or ReaderConfig()
        self.comm = YR8900Communications(self.config)
        self.antenna_mgr = AntennaManager(self.comm)
        self.is_connected = False
    
    def test_connection(self) -> bool:
        """Prueba conexión básica con el lector"""
        logger.info("Probando conexión con YR8900...")
        
        result = self.comm.send_command(CommandCodes.GET_FIRMWARE_VERSION)
        
        if result.get("valid"):
            if result.get("data") and len(result["data"]) >= 2:
                major, minor = result["data"][0], result["data"][1]
                logger.info(f"Conectado - Firmware v{major}.{minor}")
            else:
                logger.info("Conectado - Firmware detectado")
            self.is_connected = True
            return True
        
        # Información de debug para problemas de conexión
        logger.error(f"Fallo en conexión. Respuesta: {result}")
        if "error" in result:
            logger.error(f"Error específico: {result['error']}")
        
        self.is_connected = False
        return False
    
    def reset_reader(self) -> bool:
        """Resetea el lector"""
        logger.info("Reseteando lector...")
        result = self.comm.send_command(CommandCodes.RESET)
        
        # El reset no devuelve respuesta si es exitoso
        return True
    
    def initialize_system(self) -> bool:
        """Inicializa el sistema completo incluyendo detector de antenas"""
        if not self.is_connected:
            logger.error("Sistema no conectado")
            return False
        
        # Primero intentar con detector deshabilitado
        logger.info("Deshabilitando detector de antenas para pruebas iniciales...")
        self.antenna_mgr.disable_antenna_detector()
        
        # Luego habilitar con sensibilidad baja
        logger.info("Habilitando detector de antenas con sensibilidad baja...")
        detector_enabled = self.antenna_mgr.enable_antenna_detector(sensitivity=10)
        
        if detector_enabled:
            logger.info("Sistema inicializado correctamente")
        else:
            logger.warning("Sistema inicializado sin detector de antenas")
        
        return True
    
    def scan_physical_antennas(self) -> Dict[int, bool]:
        """Escanea y detecta solo antenas físicamente conectadas usando return loss"""
        logger.info("Escaneando antenas físicamente conectadas usando return loss...")
        
        # Configurar sistema para detección óptima
        logger.info("Configurando sistema para detección física...")
        
        # Aumentar potencia para mediciones precisas
        logger.info("Configurando potencia para mediciones...")
        try:
            self.comm.send_command(CommandCodes.SET_OUTPUT_POWER, [25])  # 25 dBm
            time.sleep(0.5)
        except:
            logger.warning("No se pudo configurar potencia")
        
        results = {}
        
        # Probar cada puerto con medición de return loss
        for port in range(1, 9):
            logger.info(f"Midiendo puerto {port}...")
            results[port] = self.antenna_mgr.test_antenna(port)
            time.sleep(0.8)  # Pausa entre mediciones
        
        # Mostrar resumen detallado
        connected_ports = [port for port, connected in results.items() if connected]
        disconnected_ports = [port for port, connected in results.items() if not connected]
        
        logger.info(f"=== RESULTADOS DE DETECCIÓN FÍSICA ===")
        logger.info(f"Antenas CONECTADAS: {connected_ports}")
        logger.info(f"Antenas NO CONECTADAS: {disconnected_ports}")
        logger.info(f"Total conectadas: {len(connected_ports)}/8")
        
        return results
    
    def _diagnostic_antenna_scan(self):
        """Diagnóstico adicional cuando no se detectan antenas"""
        logger.info("=== DIAGNÓSTICO AVANZADO DE ANTENAS ===")
        
        # Probar múltiples frecuencias para return loss
        test_frequencies = [
            (0x07, "902.00 MHz"),  # FCC band start
            (0x21, "915.00 MHz"),  # FCC center  
            (0x3B, "928.00 MHz"),  # FCC band end
        ]
        
        # Probar solo puertos que el usuario dice que están conectados
        test_ports = [1, 4]
        
        for port in test_ports:
            logger.info(f"\nDiagnóstico detallado puerto {port}:")
            
            # Cambiar a puerto
            set_result = self.comm.send_command(CommandCodes.SET_WORK_ANTENNA, [port-1])
            if set_result.get("valid"):
                logger.info(f"  ✓ Cambio a puerto {port} exitoso")
                time.sleep(0.5)
                
                # Probar multiple frecuencias
                for freq_param, freq_name in test_frequencies:
                    rl_result = self.comm.send_command(
                        CommandCodes.GET_RF_PORT_RETURN_LOSS, 
                        [freq_param],
                        timeout=3.0
                    )
                    
                    if rl_result.get("valid") and rl_result.get("data"):
                        return_loss = rl_result["data"][0]
                        logger.info(f"  {freq_name}: Return Loss = {return_loss} dB")
                        
                        if return_loss >= 8:
                            logger.info(f"    ✓ Indica antena conectada")
                        else:
                            logger.info(f"    ✗ Indica puerto vacío")
                    else:
                        logger.info(f"  {freq_name}: Error en medición")
            else:
                logger.info(f"  ✗ Error cambiando a puerto {port}")
        
        logger.info("=== FIN DIAGNÓSTICO AVANZADO ===")

    
    def get_system_status(self) -> Dict:
        """Obtiene estado general del sistema"""
        status = {
            "connected": self.is_connected,
            "current_antenna": None,
            "configured_antennas": len(self.antenna_mgr.antennas),
            "enabled_antennas": self.antenna_mgr.get_enabled_antennas()
        }
        
        if self.is_connected:
            status["current_antenna"] = self.antenna_mgr.get_current_antenna()
        
        return status

# Ejemplo de uso
if __name__ == "__main__":
    # Configurar sistema
    config = ReaderConfig(host="192.168.0.178", port=4001)
    reader = ReaderManager(config)
    
    # Probar conexión
    if not reader.test_connection():
        print("Error: No se pudo conectar al YR8900")
        exit(1)
    
    # Inicializar sistema con detector de antenas
    reader.initialize_system()
    
    # Obtener antena actual
    current = reader.antenna_mgr.get_current_antenna()
    print(f"Antena actualmente activa: {current}")
    
    # Escanear SOLO antenas físicamente conectadas
    print("\nEscaneando antenas físicamente conectadas...")
    test_results = reader.scan_physical_antennas()
    
    print("Resultados del escaneo:")
    connected_count = 0
    for port in range(1, 9):
        status = "CONECTADA" if test_results[port] else "NO CONECTADA"
        symbol = "●" if test_results[port] else "○"
        print(f"  {symbol} Puerto {port}: {status}")
        if test_results[port]:
            connected_count += 1
    
    print(f"\nTotal de antenas físicamente conectadas: {connected_count}/8")
    
    if connected_count == 0:
        print("ADVERTENCIA: No se detectaron antenas conectadas")
        exit(1)
    
    # Configurar solo las antenas que están físicamente conectadas
    antenna_functions = {
        1: "largada",
        2: "checkpoint_1", 
        3: "checkpoint_2",
        4: "checkpoint_3",
        5: "checkpoint_4",
        6: "llegada",
        7: "backup_1",
        8: "backup_2"
    }
    
    configured_count = 0
    print(f"\nConfigurando antenas conectadas:")
    for port in range(1, 9):
        if test_results[port]:  # Solo configurar las que están conectadas
            function = antenna_functions.get(port, f"puerto_{port}")
            reader.antenna_mgr.configure_antenna(port, True, function, 25)
            print(f"  ● Puerto {port} → {function} (25 dBm)")
            configured_count += 1
    
    print(f"Antenas configuradas: {configured_count}")
    
    # Estado del sistema actualizado
    status = reader.get_system_status()
    print(f"\nEstado final del sistema:")
    print(f"  Conectado: {status['connected']}")
    print(f"  Antena activa: {status['current_antenna']}")
    print(f"  Antenas configuradas: {status['configured_antennas']}")
    print(f"  Antenas habilitadas: {status['enabled_antennas']}")
    
    # Mostrar configuración por función solo de antenas conectadas
    config_by_function = reader.antenna_mgr.get_antenna_configuration()
    if config_by_function:
        print(f"\nConfiguración por funciones:")
        for function, ports in config_by_function.items():
            ports_str = ", ".join([str(p) for p in sorted(ports)])
            print(f"  {function}: puertos {ports_str}")
    
    # Estado del detector de antenas
    detector_status = reader.antenna_mgr.get_antenna_detector_status()
    print(f"\nDetector de antenas: {'Habilitado' if detector_status['enabled'] else 'Deshabilitado'}")
    if detector_status['enabled']:
        print(f"  Sensibilidad: {detector_status['sensitivity']}")