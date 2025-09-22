from datetime import datetime
from .config import KNOWN_TAG_PATTERNS

class TagParser:
    """Parser para tags RFID - mantiene tu lógica que funciona"""
    
    def __init__(self):
        self.known_patterns = KNOWN_TAG_PATTERNS
    
    def extract_tag_number(self, epc_data):
        """Extrae número del tag - MANTIENE tu lógica exacta"""
        if len(epc_data) < 2:
            return None
        
        # Debug como en tu código original
        debug_data = epc_data[:20]
        print(f"    Debug EPC: {' '.join(f'{b:02x}' for b in debug_data)}")
        
        # Buscar patrones exactos primero (tu lógica)
        for i in range(len(epc_data) - 1):
            byte1 = epc_data[i]
            byte2 = epc_data[i + 1]
            
            pattern = (byte1, byte2)
            if pattern in self.known_patterns:
                return self.known_patterns[pattern]
        
        # Buscar otros patrones válidos (tu lógica)
        for i in range(len(epc_data) - 1):
            byte1 = epc_data[i]
            byte2 = epc_data[i + 1]
            
            if byte1 > 0 and byte2 > 0:
                if (byte1, byte2) not in [(0x59, 0x62)]:
                    if 30 <= byte1 <= 99 and 0 <= byte2 <= 99:
                        number = f"{byte1:02d}{byte2:02d}"
                        if number not in ["5962"]:
                            return number
        
        return None