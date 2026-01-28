#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVELION YR9011 USB RFID Reader Driver - PROTOCOLO OFICIAL
src/core/yr9011_usb_scanner.py

Basado en: YR9010 UHF RFID Serial Interface Protocol User's Guide V 2.38
Protocolo: 0xA0 [Len][Address][Cmd][Data][Checksum]
Baudrate: 115200 bps (default)
"""

import serial
import serial.tools.list_ports
import logging
import time
from datetime import datetime
from typing import Optional, List, Dict
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class YR9011USBScanner(QObject):
    """
    Driver para lector INVELION YR9011 USB

    Protocolo oficial INVELION con comandos 0x80-0x89
    """

    # Señales PyQt
    tag_detected = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    # Configuración
    BAUDRATE = 115200
    TIMEOUT = 0.5
    ADDRESS = 0x01  # Dirección del lector (detectada por sniffing)

    def __init__(self, port: Optional[str] = None):
        super().__init__()
        self.port = port
        self.serial: Optional[serial.Serial] = None
        self.connected = False
        self.scanning = False

    @staticmethod
    def list_available_ports() -> List[Dict[str, str]]:
        """Listar puertos COM disponibles"""
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'port': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        return ports

    def _calculate_checksum(self, data: bytes) -> int:
        """
        Calcular checksum según protocolo INVELION
        Checksum = suma de todos los bytes excepto Head y Check
        """
        return sum(data) & 0xFF

    def _build_command(self, cmd: int, data: bytes = b'') -> bytes:
        """
        Construir comando según protocolo INVELION

        Formato: [Head=0xA0][Len][Address][Cmd][Data...][Check]
        Length = Address(1) + Cmd(1) + Checksum(1) + len(Data)
        """
        length = 3 + len(data)  # Address + Cmd + Checksum + Data
        packet = bytes([length, self.ADDRESS, cmd]) + data
        checksum = self._calculate_checksum(packet)
        return b'\xA0' + packet + bytes([checksum])

    def _parse_response(self, response: bytes) -> Optional[Dict]:
        """
        Parsear respuesta según protocolo INVELION

        Returns:
            Dict con {valid, cmd, data} o None si inválida
        """
        if len(response) < 5:
            return None

        if response[0] != 0xA0:
            return None

        length = response[1]
        address = response[2]
        cmd = response[3]

        # Verificar longitud
        expected_len = length + 3  # Head + Len + packet
        if len(response) < expected_len:
            return None

        # Extraer data y checksum
        data = response[4:4 + length - 2]  # Sin Address, Cmd, Check
        checksum_received = response[expected_len - 1]

        # Verificar checksum
        packet = response[1:expected_len - 1]  # Desde Len hasta antes de Check
        checksum_calculated = self._calculate_checksum(packet)

        if checksum_received != checksum_calculated:
            logger.warning(f"⚠️  Checksum inválido: esperado {checksum_calculated:02X}, recibido {checksum_received:02X}")
            return None

        return {
            'valid': True,
            'cmd': cmd,
            'address': address,
            'data': data
        }

    def connect(self) -> bool:
        """Conectar al lector"""
        try:
            if not self.port:
                logger.error("❌ No se especificó puerto")
                return False

            logger.info(f"📡 Conectando a {self.port} @ {self.BAUDRATE} bps...")

            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.BAUDRATE,
                timeout=self.TIMEOUT,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )

            # Limpiar buffers
            self.serial.reset_input_buffer()
            self.serial.reset_output_buffer()
            time.sleep(0.5)

            # Secuencia de inicialización del lector
            logger.info("⚙️  Inicializando lector...")

            # 1. Reset del lector
            self.serial.write(self._build_command(0x70))
            time.sleep(0.3)

            # 2. Inicializar antena
            self.serial.write(self._build_command(0x74, b'\x00'))
            time.sleep(0.3)

            # 3. Modo Host (CRÍTICO - sin esto no responde)
            self.serial.write(self._build_command(0x75, b'\x01'))
            time.sleep(0.3)

            # 4. Activar RF
            self.serial.write(self._build_command(0x74, b'\x10'))
            time.sleep(0.5)

            logger.info("📡 RF activado")

            # Verificar conexión con comando de versión
            version = self.get_firmware_version()
            if version:
                logger.info(f"✅ Conectado - Firmware: {version}")
                self.connected = True
                return True
            else:
                logger.warning("⚠️  Conectado pero sin respuesta de versión")
                # Aún así, considerarlo conectado si la inicialización fue exitosa
                self.connected = True
                return True

        except Exception as e:
            error_msg = f"Error conectando: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def disconnect(self):
        """Desconectar del lector"""
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False
        logger.info("📴 Desconectado")

    def get_firmware_version(self) -> Optional[str]:
        """
        Obtener versión del firmware
        Comando: 0x72 (cmd_get_firmware_version)
        """
        try:
            cmd = self._build_command(0x72)
            self.serial.write(cmd)
            time.sleep(0.1)

            if self.serial.in_waiting > 0:
                response = self.serial.read(self.serial.in_waiting)
                parsed = self._parse_response(response)

                if parsed and parsed['valid'] and len(parsed['data']) >= 2:
                    major = parsed['data'][0]
                    minor = parsed['data'][1]
                    return f"{major}.{minor}"

            return None

        except Exception as e:
            logger.debug(f"Error obteniendo versión: {e}")
            return None

    def read_single_tag(self, timeout: float = 2.0) -> Optional[str]:
        """
        Leer un solo tag usando inventario en tiempo real
        Comando: 0x89 (cmd_real_time_inventory)
        """
        if not self.connected or not self.serial:
            return None

        try:
            start_time = time.time()

            # Comando de inventario en tiempo real
            # 0x89 con parámetro 0x01 (single read)
            cmd = self._build_command(0x89, b'\x01')

            while (time.time() - start_time) < timeout:
                # Limpiar buffer
                self.serial.reset_input_buffer()

                # Enviar comando
                self.serial.write(cmd)
                time.sleep(0.1)

                # Leer respuesta
                if self.serial.in_waiting > 0:
                    response = self.serial.read(self.serial.in_waiting)
                    epc = self._parse_inventory_response(response)

                    if epc:
                        logger.info(f"✓ Tag leído: {epc}")
                        return epc

                time.sleep(0.1)

            logger.debug("Timeout esperando tag")
            return None

        except Exception as e:
            logger.error(f"Error leyendo tag: {e}")
            return None

    def _extract_frames(self, buffer: bytes) -> List[bytes]:
        """
        Extraer frames completos del buffer

        Busca todos los frames que comienzan con 0xA0 y tienen longitud válida
        """
        frames = []
        i = 0
        while i < len(buffer):
            # Buscar inicio de frame
            if buffer[i] != 0xA0:
                i += 1
                continue

            # Verificar que haya suficientes bytes para leer length
            if i + 2 >= len(buffer):
                break

            length = buffer[i + 1]
            total = length + 2  # length + header(0xA0) + length_byte

            # Verificar que el frame completo esté en el buffer
            if i + total > len(buffer):
                break

            # Extraer frame
            frame = buffer[i:i + total]
            frames.append(frame)
            i += total

        return frames

    def _parse_inventory_response(self, response: bytes) -> Optional[str]:
        """
        Parsear respuesta de inventario para extraer EPC

        Respuesta 0x89:
        [0xA0][Len][Address][0x89][RSSI][PC][EPC...][Check]

        Basado en código verificado que funciona con el lector
        """
        try:
            # Validaciones básicas
            if len(response) < 9:
                return None

            if response[0] != 0xA0:
                return None

            # Verificar que sea respuesta de inventario
            cmd = response[3]
            if cmd != 0x89:
                return None

            # Verificar checksum
            checksum_calc = self._calculate_checksum(response[1:-1])
            checksum_recv = response[-1]
            if checksum_calc != checksum_recv:
                logger.debug(f"Checksum inválido: esperado {checksum_calc:02X}, recibido {checksum_recv:02X}")
                return None

            # Extraer datos
            length = response[1]
            rssi = response[4]

            # Calcular longitud del EPC
            # Length = addr(1) + cmd(1) + rssi(1) + pc(1) + epc(...) + checksum(1)
            # epc_len = length - 5
            epc_len = length - 5

            if epc_len <= 0:
                return None

            epc_start = 6
            epc_end = epc_start + epc_len

            if len(response) < epc_end:
                return None

            epc_bytes = response[epc_start:epc_end]

            if not epc_bytes:
                return None

            epc_hex = ''.join(f'{b:02X}' for b in epc_bytes)

            logger.debug(f"Tag parseado: EPC={epc_hex}, RSSI={rssi}")

            return epc_hex

        except Exception as e:
            logger.debug(f"Error parseando respuesta: {e}")
            return None

    def start_continuous_reading(self):
        """Iniciar lectura continua"""
        if not self.connected:
            logger.warning("⚠️  No conectado")
            return

        self.scanning = True
        logger.info("🟢 Lectura continua iniciada")

        import threading
        thread = threading.Thread(target=self._continuous_read_loop, daemon=True)
        thread.start()

    def stop_continuous_reading(self):
        """Detener lectura continua"""
        self.scanning = False
        logger.info("🔴 Lectura continua detenida")

    def _continuous_read_loop(self):
        """
        Loop de lectura continua con buffer acumulativo

        Basado en código verificado que funciona
        """
        last_seen = {}  # {epc: timestamp}
        buffer = b""
        DEBOUNCE_TIME = 2.0
        SCAN_INTERVAL = 0.2

        # Comando de inventario
        cmd_inventory = self._build_command(0x89, b'\x01')

        while self.scanning and self.connected:
            try:
                # Enviar comando de inventario
                self.serial.write(cmd_inventory)
                time.sleep(SCAN_INTERVAL)

                # Leer datos disponibles
                if self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting)
                    buffer += data

                    # Extraer frames completos
                    frames = self._extract_frames(buffer)

                    for frame in frames:
                        # Parsear cada frame
                        epc = self._parse_inventory_response(frame)

                        if epc:
                            current_time = time.time()

                            # Debouncing - solo emitir si es nuevo o pasó suficiente tiempo
                            if epc in last_seen:
                                if current_time - last_seen[epc] < DEBOUNCE_TIME:
                                    continue

                            last_seen[epc] = current_time

                            # Emitir señal de tag detectado
                            tag_data = {
                                'tag_id': epc,
                                'epc': epc,
                                'timestamp': datetime.now(),
                                'reader': 'YR9011-USB',
                                'antenna_port': 1
                            }

                            self.tag_detected.emit(tag_data)
                            logger.info(f"📡 Tag detectado: {epc}")

                    # Limpiar buffer - mantener solo datos después del último frame procesado
                    if frames:
                        last_frame = frames[-1]
                        last_pos = buffer.rfind(last_frame)
                        if last_pos != -1:
                            buffer = buffer[last_pos + len(last_frame):]

                time.sleep(0.05)

            except Exception as e:
                logger.error(f"Error en loop de lectura: {e}")
                time.sleep(1)

    def __del__(self):
        """Limpieza"""
        self.disconnect()
