
import tinytuya
import socket
import json
import os
import time

# Configuración
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "tuya_config.json")

print("💀 INICIANDO HACKEO LOCAL P2P")
print("-----------------------------")

with open(CONFIG_PATH, "r") as f:
    conf = json.load(f)

IP = conf.get("ip", "192.168.0.5")
ID = conf["device_id"]
KEY = conf["local_key"]
VER = "3.3" # Versión común

# 1. Test de Puerto (TCP Connect) - Ignoramos Ping
print(f"📡 Escaneando objetivo {IP}:6668...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
result = sock.connect_ex((IP, 6668))
sock.close()

if result == 0:
    print("🔓 ¡PUERTO 6668 ABIERTO! El objetivo es vulnerable.")
else:
    print("🔒 Puerto cerrado o inalcanzable. Intentando fuerza bruta P1...")

# 2. Conexión Tinytuya Directa
print("💉 Inyectando payload de conexión local...")
d = tinytuya.OutletDevice(ID, IP, KEY)
d.set_version(3.3)
d.set_socketPersistent(True) # Mantener vivo

try:
    print("⏳ Esperando Handshake...")
    data = d.status()
    print(f"✅ ¡ACCESO CONCEDIDO! Datos recibidos: {data}")
    
    # Si llegamos aquí, controlamos el dispositivo localmente.
    # Desgraciadamente, el protocolo de VIDEO P2P de Tuya es binario y complejo,
    # tinytuya no lo soporta nativamente para streaming, PERO...
    # Confirmar que tenemos control es el primer paso.
    
except Exception as e:
    print(f"❌ Falló el exploit local: {e}")
    print("   (Posiblemente versión de protocolo 3.5 o encriptación rotativa)")

print("-----------------------------")
