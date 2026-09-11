"""
Parser universal de tags RFID - Versión estable
Ignora bytes variables del protocolo
"""
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TagParser:
    """Parser que usa solo bytes estables del EPC"""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.detection_stats = {'total': 0, 'valid': 0, 'invalid': 0}
    
    def extract_tag_number(self, epc_data):
        """
        Extrae número del chip usando las MISMAS posiciones que USB.

        Para chips de 12+ bytes (típico): extrae bytes en posiciones -3:-1
        (penúltimos 2 bytes, igual que USB scanner en data[-3:-1])

        Para chips más cortos: usa toda la data significativa
        """
        self.detection_stats['total'] += 1

        if len(epc_data) < 2:
            self.detection_stats['invalid'] += 1
            return None

        # ALWAYS show debug for troubleshooting
        debug_data = epc_data[:min(13, len(epc_data))]
        logger.info(f"🔍 TagParser.extract_tag_number() - EPC recibido ({len(epc_data)} bytes): {' '.join(f'{b:02x}' for b in debug_data)}")

        # ⭐ NUEVA LÓGICA: Extraer mismas posiciones que USB
        # USB extrae data[-3:-1] (penúltimos 2 bytes del paquete)
        # TCP/IP debe hacer lo mismo con el EPC

        if len(epc_data) >= 12:
            # Chips largos (ej: e2 80 68 94 00 00 40 1a 4a 95 08 18 c8)
            # El ID único está en posiciones -3:-1
            stable_bytes = epc_data[-3:-1]
            logger.info(f"🔍 TagParser - EPC largo ({len(epc_data)} bytes): extrayendo posiciones [-3:-1]")
        else:
            # Chips cortos: encontrar bytes significativos (sin leading zeros)
            significant_start = 0
            for i, byte in enumerate(epc_data):
                if byte != 0x00:
                    significant_start = i
                    break

            significant_bytes = epc_data[significant_start:]

            if len(significant_bytes) < 2:
                self.detection_stats['invalid'] += 1
                return None

            # Usar todos los bytes significativos (máximo 4)
            stable_bytes = significant_bytes[:min(4, len(significant_bytes))]
            logger.info(f"🔍 TagParser - EPC corto: tomando {len(stable_bytes)} bytes significativos")

        # Formatear como hex
        tag_number = ''.join(f'{b:02X}' for b in stable_bytes)
        logger.info(f"🔍 TagParser - stable_bytes: [{' '.join(f'{b:02x}' for b in stable_bytes)}] → '{tag_number}'")

        self.detection_stats['valid'] += 1
        return tag_number
    
    def get_stats(self):
        """Retorna estadísticas de detección"""
        return self.detection_stats.copy()
    
    def reset_stats(self):
        """Reinicia estadísticas"""
        self.detection_stats = {'total': 0, 'valid': 0, 'invalid': 0}

    @staticmethod
    def normalize_tag_id(tag_id: str) -> str:
        """
        Normalizar ID de chip eliminando leading zeros inconsistentes

        Esto asegura que chips leídos por diferentes interfaces (USB vs TCP/IP)
        se normalicen al mismo formato.

        Ejemplos:
            '0181D' → '181D'
            '0818' → '818'
            '00AB' → 'AB'
            'E280' → 'E280' (sin cambios)

        Args:
            tag_id: ID del chip en formato hex string

        Returns:
            ID normalizado sin leading zeros
        """
        if not tag_id:
            return tag_id

        try:
            # Convertir hex → int → hex para eliminar leading zeros
            as_int = int(tag_id, 16)
            normalized = format(as_int, 'X')  # Uppercase hex sin padding

            logger.debug(f"Tag normalizado: '{tag_id}' → '{normalized}'")
            return normalized

        except ValueError:
            # Si no es hex válido, retornar uppercase sin cambios
            logger.warning(f"⚠️  Tag ID no es hex válido: '{tag_id}', retornando uppercase")
            return tag_id.upper()