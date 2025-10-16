# test_parser_simple.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.tag_parser import TagParser

parser = TagParser(debug=True)

# Simular chips con EPCs parecidos
chips = [
    bytes([0x00, 0x85, 0x87, 0x41]),  # Último 2 bytes: 87 41
    bytes([0x00, 0x85, 0x87, 0x42]),  # Último 2 bytes: 87 42
    bytes([0x00, 0x85, 0x87, 0x43]),  # Último 2 bytes: 87 43
    bytes([0x00, 0x85, 0x87, 0x44]),  # Último 2 bytes: 87 44
]

print("=== TEST PARSER SIMPLE ===\n")

for i, chip in enumerate(chips, 1):
    number = parser.extract_tag_number(chip)
    print(f"Chip {i}: {number}\n")

# Deberían ser todos diferentes:
# 8741, 8742, 8743, 8744