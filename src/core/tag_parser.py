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
        Extrae número usando solo los bytes ESTABLES del EPC
        Ignora los últimos bytes que pueden ser contadores o metadata
        """
        self.detection_stats['total'] += 1
        
        if len(epc_data) < 2:
            self.detection_stats['invalid'] += 1
            return None
        
        # Debug opcional
        if self.debug:
            debug_data = epc_data[:min(12, len(epc_data))]
            print(f"    Debug EPC: {' '.join(f'{b:02x}' for b in debug_data)}")
        
        # Encontrar donde empiezan los bytes significativos
        significant_start = 0
        for i, byte in enumerate(epc_data):
            if byte != 0x00:
                significant_start = i
                break
        
        significant_bytes = epc_data[significant_start:]
        
        if len(significant_bytes) < 2:
            self.detection_stats['invalid'] += 1
            return None
        
        # ⭐ Tomar solo los primeros bytes ESTABLES
        # NO usar los últimos que pueden variar
        if len(significant_bytes) >= 4:
            # Si hay 4+ bytes, usar los primeros 4
            stable_bytes = significant_bytes[:4]
        elif len(significant_bytes) >= 2:
            # Si hay 2-3 bytes, usar los primeros 2
            stable_bytes = significant_bytes[:2]
        else:
            stable_bytes = significant_bytes
        
        # Formatear como hex (sin los bytes variables)
        tag_number = ''.join(f'{b:02X}' for b in stable_bytes)
        
        if self.debug:
            print(f"    → Número estable: {tag_number}")
        
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