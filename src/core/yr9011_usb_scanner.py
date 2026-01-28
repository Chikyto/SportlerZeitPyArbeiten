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
        """
        length = 1 + 1 + len(data)  # Address + Cmd + Data
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
            time.sleep(0.1)

            # Verificar conexión con comando de versión
            version = self.get_firmware_version()
            if version:
                logger.info(f"✅ Conectado - Firmware: {version}")
                self.connected = True
                return True
            else:
                logger.warning("⚠️  Conectado pero sin respuesta de versión")
                # Aún así, considerarlo conectado
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

    def _parse_inventory_response(self, response: bytes) -> Optional[str]:
        """
        Parsear respuesta de inventario para extraer EPC

        Respuesta 0x89:
        [0xA0][Len][Address][0x89][Num][PC_H][PC_L][EPC...][RSSI][Check]
        """
        try:
            parsed = self._parse_response(response)

            if not parsed or not parsed['valid']:
                return None

            # Verificar que sea respuesta de inventario
            if parsed['cmd'] != 0x89:
                return None

            data = parsed['data']

            if len(data) < 4:
                return None

            # Estructura: [Num][PC_H][PC_L][EPC...][RSSI]
            num_tags = data[0]

            if num_tags == 0:
                return None

            pc_h = data[1]
            pc_l = data[2]

            # Calcular longitud del EPC desde PC
            # PC[15:11] = longitud en words (2 bytes)
            epc_length_words = (pc_h >> 3) & 0x1F
            epc_length_bytes = epc_length_words * 2

            if len(data) < (3 + epc_length_bytes):
                return None

            # Extraer EPC
            epc_bytes = data[3:3 + epc_length_bytes]
            epc_hex = ''.join(f'{b:02X}' for b in epc_bytes)

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
        """Loop de lectura continua"""
        last_tag = None
        last_tag_time = 0
        DEBOUNCE_TIME = 1.0

        while self.scanning and self.connected:
            try:
                epc = self.read_single_tag(timeout=0.5)

                if epc:
                    current_time = time.time()

                    # Debouncing
                    if epc != last_tag or (current_time - last_tag_time) > DEBOUNCE_TIME:
                        tag_data = {
                            'tag_id': epc,
                            'epc': epc,
                            'timestamp': datetime.now(),
                            'reader': 'YR9011-USB',
                            'antenna_port': 1
                        }

                        self.tag_detected.emit(tag_data)
                        logger.info(f"📡 Tag detectado: {epc}")

                        last_tag = epc
                        last_tag_time = current_time

                time.sleep(0.2)

            except Exception as e:
                logger.error(f"Error en loop de lectura: {e}")
                time.sleep(1)

    def __del__(self):
        """Limpieza"""
        self.disconnect()
