#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time
from datetime import datetime


# ================= CONFIG =================

PORT = "COM3"
BAUDRATE = 115200

SCAN_INTERVAL = 0.2
DUP_TIMEOUT = 2


# ================= HEX para Print =================

def dump_hex(data, label=""):
    if label:
        print(label)
    print("HEX:", " ".join(f"{b:02X}" for b in data))
    print("DEC:", " ".join(str(b) for b in data))
    print("LEN:", len(data))
    print()

# ================= PROTO =================

def checksum(data):
    return sum(data) & 0xFF

def build(cmd, data=b""):
    addr = 0x01
    # Length = addr + cmd + data + checksum?
    length = 3 + len(data)
    pkt = bytes([
        length,
        addr,
        cmd
    ]) + data
    frame = b"\xA0" + pkt + bytes([checksum(pkt)])
    dump_hex(frame, "➡️ ENVIANDO:")
    return frame


# ================= COMMANDS =================

CMD_RESET = build(0x70)
CMD_INIT = build(0x74, b"\x00")
CMD_RF_ON = build(0x74, b"\x10")
CMD_INVENTORY = build(0x89, b"\x01")
CMD_HOST_MODE = build(0x75, b"\x01")

# ================= PARSER =================

def extract_frames(buffer):
    frames = []
    i = 0
    while i < len(buffer):
        if buffer[i] != 0xA0:
            i += 1
            continue
        if i + 2 >= len(buffer):
            break
        length = buffer[i + 1]
        total = length + 2
        if i + total > len(buffer):
            break
        frame = buffer[i:i + total]
        frames.append(frame)
        i += total
    return frames


def parse_tag(frame):
    if len(frame) < 9:
        return None
    if frame[0] != 0xA0:
        return None
    cmd = frame[3]
    if cmd != 0x89:
        return None
    # checksum
    if checksum(frame[1:-1]) != frame[-1]:
        return None
    rssi = frame[4]
    epc_len = frame[1] - 5
    start = 6
    end = start + epc_len
    epc = frame[start:end]
    if not epc:
        return None
    return epc.hex().upper(), rssi

# ================= MAIN =================

def main():
    print("=" * 50)
    print(" LECTOR RFID YR9011 ")
    print("=" * 50)
    print()
    ser = serial.Serial(PORT, BAUDRATE, timeout=0.3)
    print("✅ Conectado\n")
    time.sleep(0.5)
    # Init sequence
    print("⚙️ Inicializando lector...")
    ser.write(CMD_RESET)
    time.sleep(0.3)
    ser.write(CMD_INIT)
    time.sleep(0.3)
    ser.write(CMD_HOST_MODE)   # <-- NUEVO
    time.sleep(0.3)
    ser.write(CMD_RF_ON)
    time.sleep(0.5)
    print("📡 RF Activado\n")
    last_seen = {}
    buffer = b""
    print("🔍 Buscando tags...\n")
    try:
        while True:
            ser.write(CMD_INVENTORY)
            time.sleep(SCAN_INTERVAL)
            if ser.in_waiting:
                data = ser.read(ser.in_waiting)
                dump_hex(data, "⬅️ RECIBIDO:")
                buffer += data
                frames = extract_frames(buffer)
                for f in frames:
                    tag = parse_tag(f)
                    if tag:
                        epc, rssi = tag
                        now = time.time()
                        if epc in last_seen:
                            if now - last_seen[epc] < DUP_TIMEOUT:
                                continue
                        last_seen[epc] = now
                        ts = datetime.now().strftime("%H:%M:%S")
                        print(f"[{ts}] 🏷️ {epc} | RSSI {rssi}")
                # limpiar buffer
                if frames:
                    last = buffer.rfind(frames[-1])
                    buffer = buffer[last + len(frames[-1]):]
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n🛑 Detenido")
    finally:
        ser.close()
        print("🔌 Cerrado")

if __name__ == "__main__":
    main()