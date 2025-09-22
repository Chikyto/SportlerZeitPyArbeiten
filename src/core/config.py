# Configuración básica del scanner RFID
RFID_HOST = "192.168.0.178"
RFID_PORT = 4001
RFID_TIMEOUT = 3.0

# Patrones de chips que ya funcionan
KNOWN_TAG_PATTERNS = {
    (0x85, 0x99): "8599",
    (0x85, 0x75): "8575", 
    (0x85, 0x87): "8587",
    (0x76, 0x62): "7662",
    (0x36, 0x42): "3642",
    (0x59, 0x62): "5962",
    (0x86, 0x00): "8600",
}