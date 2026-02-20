
import socket
import time
import json
import os
import tinytuya

# Configuración
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "..", "tuya_config.json")

with open(CONFIG_PATH, "r") as f:
    conf = json.load(f)

IP = conf['ip']
ID = conf['device_id']
KEY = conf['local_key']

print(f"💀 INICIANDO PROTOCOLO DESPERTADOR PARA: {IP}")
print("------------------------------------------------")

def send_udp_broadcast():
    """Envía paquetes UDP de descubrimiento a puerto 6666/6668"""
    print("📡 Enviando pulsos UDP...", end="")
    c = tinytuya.Device(ID, IP, KEY)
    c.set_version(3.3) 
    
    # Intentar mandar comando de "actualizar estado" repetidamente
    # Esto fuerza al chip WiFi a procesar datos
    try:
        # Manda payload UDP raw si es posible, o usa la libreria
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.1)
        
        # Payload mágico genérico de Tuya (Heartbeat)
        payload = b'\x00\x00\x55\xaa\x00\x00\x00\x00\x00\x00\x00\x00'
        
        for p in [6666, 6667, 6668]:
            try:
                sock.sendto(payload, (IP, p))
            except: pass
        print(" OK")
    except Exception as e:
        print(f" Err: {e}")

def force_tcp_connection():
    """Intenta martillear el puerto TCP 6668"""
    print("🔨 Martilleando puerto TCP 6668...", end="")
    try:
        # Usamos tinytuya para intentar un handshake real
        d = tinytuya.Device(ID, IP, KEY)
        d.set_socketPersistent(False) # Forzar reconexión constante
        d.set_version(3.4) # Probar versión moderna
        
        # Intentamos obtener estado 3 veces rápido
        for i in range(3):
            try:
                data = d.status()
                if data and 'dps' in data:
                    print(f"\n🎉 ¡DESPIERTO! Batería: {data['dps'].get('145', 'Unknown')}%")
                    return True
            except:
                print(".", end="", flush=True)
                time.sleep(0.5)
    except:
        pass
    print(" No responde.")
    return False

# SECUENCIA DE ATAQUE
# 1. Bombardeo inicial
for i in range(5):
    send_udp_broadcast()
    time.sleep(0.5)

# 2. Intento de conexión TCP
if force_tcp_connection():
    print("\n✅ EL DISPOSITIVO ESTÁ ACTIVO. INTENTANDO VIDEO AHORA...")
    # Aquí podríamos lanzar el script de video
    import subprocess
    cmd = ["python3", "-c", "import sys; sys.path.append('..'); from utils import show_doorbell_stream; show_doorbell_stream(None)"]
    subprocess.run(cmd, cwd=PROJECT_ROOT)
else:
    print("\n❌ El dispositivo resiste. Sigue en Deep Sleep.")
    print("   Nota: Los dispositivos a batería modernos ignoran todo el tráfico lan si la CPU duerme.")
