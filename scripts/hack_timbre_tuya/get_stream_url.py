#!/usr/bin/env python3
import tinytuya
import json

# Credenciales (Extraídas de tuya_config.json)
ACCESS_ID = "ce4xk53qg5kgph5fsfux"
ACCESS_SECRET = "059755cbce2b444cb23c7e9f8cd241b7"
REGION = "us"
DEVICE_ID = "eba60f4e71e9782575wdkh"

print("☁️ Conectando a Tuya Cloud con TinyTuya...")
c = tinytuya.Cloud(
    apiRegion=REGION, 
    apiKey=ACCESS_ID, 
    apiSecret=ACCESS_SECRET, 
    apiDeviceID=DEVICE_ID
)

# Esto fuerza a tinytuya a obtener un token válido
print("🔑 Autenticando...")
# TinyTuya maneja el token internamente al hacer una request

# Pedir URL HLS (Más compatible)
payload = {"type": "hls"}
print(f"📡 Solicitando URL de video (HLS) para {DEVICE_ID}...")

# Usamos la función interna de tinytuya para hacer calls V2 firmadas
try:
    response = c.cloudrequest(
        f"/v1.0/devices/{DEVICE_ID}/stream/actions/allocate",
        action="POST",
        post=payload
    )
    
    print("📦 RESPUESTA RAW:", json.dumps(response, indent=2)) # DEBUG CRÍTICO
    
    if response and 'success' in response and response['success']:
        # Explorar qué hay adentro
        result = response['result']
        if 'url' in result:
             url = result['url']
             print("\n🎉 ¡ÉXITO! URL DE VIDEO OBTENIDA:")
             print(f"👉 {url}")
        else:
             print("⚠️ No encontré 'url' en result. Revisa el JSON arriba.")
    else:
        print(f"⚠️ API Error: {response}")
        
except Exception as e:
    print(f"❌ Error: {e}")
