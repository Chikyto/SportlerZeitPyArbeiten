import serial
import time

PORT = "COM3"
BAUD = 115200


# =============================
# Utils
# =============================

def checksum_yr9011(data: bytes) -> int:
    return (sum(data) + 0x42) & 0xFF



def build_packet(cmd: int, data=b"") -> bytes:

    addr = 0x01

    # Inventory es especial
    if cmd == 0x89:
        length = 0x04
        body = bytes([length, addr, cmd]) + data
        fake = b"\x00"
        cs = checksum_yr9011(body + fake)
        return b"\xA0" + body + bytes([cs])

    # Otros comandos normales
    length = 1 + 1 + len(data) + 1

    body = bytes([length, addr, cmd]) + data + b"\x00"

    cs = checksum_yr9011(body)

    return b"\xA0" + body + bytes([cs])





def send_cmd(ser, cmd, data=b""):

    pkt = build_packet(cmd, data)

    print("➡️ TX:", pkt.hex(" ").upper())

    ser.write(pkt)
    ser.flush()


# =============================
# Init reader
# =============================

def init_reader(ser):

    print("⚙️ Inicializando lector...")

    # Reset
    send_cmd(ser, 0x70, b"\x00")
    time.sleep(1)

    # Host mode (CRITICO)
    send_cmd(ser, 0x75, b"\x01")
    time.sleep(0.3)

    # RF ON
    send_cmd(ser, 0x74, b"\x00")
    time.sleep(0.3)

    # Power default
    send_cmd(ser, 0x7A, b"\x00")
    time.sleep(0.3)


# =============================
# Read packet
# =============================

def read_packet(ser):

    # Buscar header A0
    while True:

        b = ser.read(1)

        if not b:
            return None

        if b == b"\xA0":
            break

    # Leer length
    length_b = ser.read(1)

    if not length_b:
        return None

    length = length_b[0]

    # Leer cuerpo + checksum
    rest = ser.read(length + 1)

    if len(rest) != length + 1:
        return None

    return b"\xA0" + length_b + rest


# =============================
# Parse tag
# =============================

def parse_tag(pkt):

    if pkt[3] != 0x89:
        return None

    data = pkt[4:-1]

    # Paquete largo = tag
    if len(data) < 16:
        return None

    uid = data[-4:-2]

    return uid.hex().upper()


# =============================
# Main
# =============================

def main():

    print("=" * 40)
    print(" LECTOR RFID YR9011 ")
    print("=" * 40)

    # Abrir puerto
    print("✅ Conectando...")

    ser = serial.Serial(
        PORT,
        BAUD,
        timeout=0.5
    )

    time.sleep(1)

    print("✅ Conectado\n")

    # Init
    init_reader(ser)

    print("\n📡 Escuchando tags...\n")

    try:

        while True:

            # Pedir inventario
            send_cmd(ser, 0x89, b"\x01")

            time.sleep(0.2)

            pkt = read_packet(ser)

            if not pkt:
                continue

            print("⬅️ RX:", pkt.hex(" ").upper())

            uid = parse_tag(pkt)

            if uid:
                print("🎯 TAG:", uid)

    except KeyboardInterrupt:

        print("\n🛑 Detenido por usuario")

    finally:

        ser.close()
        print("🔌 Puerto cerrado")


# =============================
# Run
# =============================

if __name__ == "__main__":
    main()
