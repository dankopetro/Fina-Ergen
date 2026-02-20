
import os
import json
import tinytuya
import subprocess
import time
import sys

# Configuración
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "tuya_config.json")

print("🔥 INICIANDO PROTOCOLO DE VIDEO AGRESIVO (RTSP)")
print("-----------------------------------------------")

# Cargar config
with open(CONFIG_PATH, "r") as f:
    conf = json.load(f)

# Conectar Nube
c = tinytuya.Cloud(
    apiRegion=conf['region_code'], 
    apiKey=conf['access_id'], 
    apiSecret=conf['access_secret'], 
    apiDeviceID=conf['device_id']
)

def get_rtsp_url():
    print("📡 Negociando túnel RTSP con la Nube...")
    
    # Intento 1: RTSP puro
    uri = f'/v1.0/devices/{conf["device_id"]}/stream/actions/allocate'
    body = {"type": "rtsp"} 
    
    response = c.cloudrequest(uri, post=body)
    
    if 'result' in response and 'url' in response['result']:
        url = response['result']['url']
        print(f"✅ ¡URL RTSP OBTENIDA!: {url[:50]}...")
        return url
    else:
        print(f"❌ Falló RTSP: {response}")
        return None

def launch_player(url):
    print("🚀 Lanzando reproductor en modo 'Sin Piedad'...")
    
    # Preferimos ffplay si existe (es más diagnóstico)
    if subprocess.call(["which", "ffplay"], stdout=subprocess.DEVNULL) == 0:
        print("🛠️ Usando FFplay (Baja latencia)...")
        # -rtsp_transport tcp: Más estable
        # -fflags nobuffer: Tiempo real puro
        # -loglevel debug: Ver todo el gore
        cmd = [
            "ffplay",
            "-rtsp_transport", "tcp",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-framedrop",
            "-strict", "experimental",
            url
        ]
        subprocess.run(cmd)
    else:
        print("🍊 Usando VLC (Modo Agresivo)...")
        # VLC tuneado al máximo
        cmd = [
            "vlc",
            "--network-caching=1000", # Buffer pequeño para forzar realtime
            "--rtsp-tcp",             # TCP obligatorio
            "--clock-jitter=0",       # Ignorar jitter
            "--clock-synchro=0",      # Desactivar sincro reloj
            url
        ]
        subprocess.run(cmd)

# Ejecución
url = get_rtsp_url()
if url:
    print("⚡ Intentando conexión... (Puede tardar 10-20s)")
    launch_player(url)
else:
    print("💀 No se pudo obtener URL.")
