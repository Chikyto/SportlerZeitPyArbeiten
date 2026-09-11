import serial
import time

PORT = "COM3"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=1)

print("Conectado")

time.sleep(0.5)

# Frame crudo: A0 04 01 89 01 71
cmd = b"\xA0\x04\x01\x89\x01\x71"

print("Enviando inventario...")

ser.write(cmd)

time.sleep(1)

if ser.in_waiting:
    data = ser.read(ser.in_waiting)
    print("Respuesta:", data.hex(" ").upper())
else:
    print("❌ Sin respuesta")

ser.close()
print("Cerrado")
