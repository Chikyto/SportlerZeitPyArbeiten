"""
Configuración del sistema RFID
"""

# === Patrones conocidos (LEGACY - opcional) ===
# Solo necesario si quieres mapear chips específicos a números personalizados
# Para competencias normales, NO es necesario
KNOWN_TAG_PATTERNS = {
    # (byte1, byte2): "número_mostrado"
    # Ejemplo: tus chips actuales
    (0x85, 0x99): "8599",
    (0x85, 0x75): "8575",
    (0x85, 0x87): "8587",
    (0x76, 0x62): "7662",
    (0x36, 0x42): "3642",
    # ... puedes agregar más si quieres mapeos específicos
}

# === Configuración del Parser ===
PARSER_CONFIG = {
    'use_known_patterns': False,  # ⭐ False = modo universal
    'debug': False,  # True para ver debug de cada tag
    'min_epc_length': 2,  # Longitud mínima de EPC válido
}