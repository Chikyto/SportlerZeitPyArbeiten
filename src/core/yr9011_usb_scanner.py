#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INVELION YR9011 USB RFID Reader Driver
src/core/yr9011_usb_scanner.py

Scanner USB para asignación de chips en lugar de retiro de kits.
Compatible con INVELION YR9011 - lector UHF RFID de escritorio (10-80cm)

El YR9011 se comunica por USB usando protocolo serial.
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

    Este lector es ideal para:
    - Asignación de chips en lugar de retiro de kits
    - Operación standalone sin red
    - Lectura de corto alcance (10-80cm)

    Señales:
        tag_detected: Emite dict con {tag_id, timestamp}
        error_occurred: Emite str con mensaje de error
    """

    # Señales PyQt
    tag_detected = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    # Configuración del protocolo
    BAUDRATE = 115200  # Baudrate típico para YR9011
    TIMEOUT = 1.0

    # Códigos de comando (basados en protocolo INVELION)
    CMD_GET_VERSION = b'\xA0\x03\x01\x00\xA4'
    CMD_INVENTORY = b'\xA0\x04\x01\x89\x01\x8F'  # Inventario simple

    def __init__(self, port: Optional[str] = None):
        """
        Inicializar scanner USB

        Args:
            port: Puerto COM (ej: 'COM3' en Windows, '/dev/ttyUSB0' en Linux)
                  Si es None, intenta detectar automáticamente
        """
        super().__init__()
        self.port = port
        self.serial: Optional[serial.Serial] = None
        self.connected = False
        self.scanning = False

    @staticmethod
    def list_available_ports() -> List[Dict[str, str]]:
        """
        Listar puertos COM disponibles

        Returns:
            Lista de dicts con información de puertos: {port, description, hwid}
        """
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'port': port.device,
                'description': port.description,
                'hwid': port.hwid
            })
        return ports

    def auto_detect_port(self) -> Optional[str]:
        """
        Intentar detectar automáticamente el puerto del YR9011

        Returns:
            Nombre del puerto detectado o None
        """
        logger.info("🔍 Detectando puerto YR9011...")

        ports = self.list_available_ports()

        # Intentar detectar por descripción (USB-Serial, CH340, etc.)
        for port_info in ports:
            description = port_info['description'].lower()
            hwid = port_info['hwid'].lower()

            # Palabras clave comunes en lectores USB-Serial chinos
            keywords = ['usb', 'serial', 'ch340', 'ch341', 'cp210', 'ftdi', 'prolific']

            if any(keyword in description or keyword in hwid for keyword in keywords):
                logger.info(f"✓ Puerto candidato: {port_info['port']} ({port_info['description']})")

                # Intentar conectar y verificar
                if self._test_port(port_info['port']):
                    logger.info(f"✅ YR9011 detectado en {port_info['port']}")
                    return port_info['port']

        logger.warning("⚠️  No se detectó YR9011 automáticamente")
        return None

    def _test_port(self, port: str) -> bool:
        """
        Probar si un puerto tiene un YR9011 conectado

        Args:
            port: Puerto a probar

        Returns:
            True si responde al comando de versión
        """
        try:
            test_serial = serial.Serial(
                port=port,
                baudrate=self.BAUDRATE,
                timeout=0.5
            )

            # Limpiar buffer
            test_serial.reset_input_buffer()

            # Enviar comando de versión
            test_serial.write(self.CMD_GET_VERSION)
            time.sleep(0.1)

            # Leer respuesta
            if test_serial.in_waiting > 0:
                response = test_serial.read(test_serial.in_waiting)
                test_serial.close()

                # Verificar que haya respuesta válida (protocolo INVELION)
                if len(response) > 3 and response[0] == 0xA0:
                    return True

            test_serial.close()
            return False

        except Exception as e:
            logger.debug(f"Error probando puerto {port}: {e}")
            return False

    def connect(self) -> bool:
        """
        Conectar al lector YR9011

        Returns:
            True si la conexión fue exitosa
        """
        try:
            # Auto-detectar puerto si no se especificó
            if not self.port:
                self.port = self.auto_detect_port()
                if not self.port:
                    error_msg = "No se pudo detectar YR9011. Especifica el puerto manualmente."
                    logger.error(f"❌ {error_msg}")
                    self.error_occurred.emit(error_msg)
                    return False

            logger.info(f"📡 Conectando a YR9011 en {self.port}...")

            # Abrir puerto serial
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

            # Verificar conexión con comando de versión
            version = self.get_firmware_version()
            if version:
                logger.info(f"✅ Conectado a YR9011 - Firmware: {version}")
                self.connected = True
                return True
            else:
                logger.warning("⚠️  Conectado pero sin respuesta de versión")
                self.connected = True
                return True

        except serial.SerialException as e:
            error_msg = f"Error de puerto serial: {str(e)}"
            logger.error(f"❌ {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
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
        logger.info("📴 Desconectado de YR9011")

    def get_firmware_version(self) -> Optional[str]:
        """
        Obtener versión del firmware

        Returns:
            String con versión o None si falla
        """
        if not self.serial or not self.serial.is_open:
            return None

        try:
            # Limpiar buffer
            self.serial.reset_input_buffer()

            # Enviar comando
            self.serial.write(self.CMD_GET_VERSION)
            time.sleep(0.1)

            # Leer respuesta
            if self.serial.in_waiting > 0:
                response = self.serial.read(self.serial.in_waiting)

                # Parsear respuesta (protocolo INVELION)
                if len(response) >= 5 and response[0] == 0xA0:
                    # Típicamente: [A0, LEN, major, minor, checksum]
                    major = response[2] if len(response) > 2 else 0
                    minor = response[3] if len(response) > 3 else 0
                    return f"{major}.{minor}"

            return None

        except Exception as e:
            logger.error(f"Error obteniendo versión: {e}")
            return None

    def read_single_tag(self, timeout: float = 2.0) -> Optional[str]:
        """
        Leer un solo tag (modo síncrono)

        Args:
            timeout: Tiempo máximo de espera en segundos

        Returns:
            EPC del tag leído o None
        """
        if not self.connected or not self.serial:
            return None

        try:
            start_time = time.time()

            # Limpiar buffer
            self.serial.reset_input_buffer()

            while (time.time() - start_time) < timeout:
                # Enviar comando de inventario
                self.serial.write(self.CMD_INVENTORY)
                time.sleep(0.05)

                # Leer respuesta
                if self.serial.in_waiting > 0:
                    response = self.serial.read(self.serial.in_waiting)

                    # Parsear EPC
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

    def _parse_inventory_response(self, data: bytes) -> Optional[str]:
        """
        Parsear respuesta de inventario para extraer EPC

        Args:
            data: Bytes de respuesta

        Returns:
            EPC como string hexadecimal o None
        """
        try:
            # Protocolo INVELION típico:
            # [A0, LEN, CMD, STATUS, PC_MSB, PC_LSB, EPC..., RSSI, ANTENNA, CHECKSUM]

            if len(data) < 10 or data[0] != 0xA0:
                return None

            # Verificar status (debe ser 0x00 para éxito)
            status = data[3]
            if status != 0x00:
                return None

            # PC (Protocol Control) - 2 bytes
            pc_msb = data[4]
            pc_lsb = data[5]

            # Calcular longitud del EPC (bits en PC[15:11] * 2 bytes)
            epc_length_words = (pc_msb >> 3) & 0x1F  # 5 bits
            epc_length_bytes = epc_length_words * 2

            if len(data) < (6 + epc_length_bytes):
                return None

            # Extraer EPC
            epc_bytes = data[6:6 + epc_length_bytes]
            epc_hex = ''.join(f'{b:02X}' for b in epc_bytes)

            return epc_hex

        except Exception as e:
            logger.debug(f"Error parseando respuesta: {e}")
            return None

    def start_continuous_reading(self):
        """
        Iniciar lectura continua (modo asíncrono)
        Emite señal tag_detected cuando detecta un tag
        """
        if not self.connected:
            logger.warning("⚠️  No conectado, no se puede iniciar lectura")
            return

        self.scanning = True
        logger.info("🟢 Lectura continua iniciada")

        # Iniciar thread de lectura continua
        import threading
        thread = threading.Thread(target=self._continuous_read_loop, daemon=True)
        thread.start()

    def stop_continuous_reading(self):
        """Detener lectura continua"""
        self.scanning = False
        logger.info("🔴 Lectura continua detenida")

    def _continuous_read_loop(self):
        """Loop de lectura continua (ejecuta en thread separado)"""
        last_tag = None
        last_tag_time = 0
        DEBOUNCE_TIME = 1.0  # Segundos entre lecturas del mismo tag

        while self.scanning and self.connected:
            try:
                epc = self.read_single_tag(timeout=0.5)

                if epc:
                    current_time = time.time()

                    # Debouncing: ignorar si es el mismo tag muy rápido
                    if epc != last_tag or (current_time - last_tag_time) > DEBOUNCE_TIME:
                        # Emitir señal con tag detectado
                        tag_data = {
                            'tag_id': epc,
                            'epc': epc,
                            'timestamp': datetime.now(),
                            'reader': 'YR9011-USB',
                            'antenna_port': 1  # USB reader solo tiene 1 antena
                        }

                        self.tag_detected.emit(tag_data)
                        logger.info(f"📡 Tag detectado: {epc}")

                        last_tag = epc
                        last_tag_time = current_time

                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error en loop de lectura: {e}")
                time.sleep(1)

    def __del__(self):
        """Limpieza al destruir objeto"""
        self.disconnect()
