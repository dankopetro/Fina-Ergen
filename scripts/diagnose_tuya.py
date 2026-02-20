import tinytuya
import json
import time

print("🔍 Iniciando diagnóstico de Timbre Tuya...")

try:
    with open("tuya_config.json") as f:
        config = json.load(f)
except Exception as e:
    print(f"❌ Error leyendo config: {e}")
    exit(1)

print(f"🎯 Objetivo: {config['ip']} (ID: {config['device_id']})")

try:
    d = tinytuya.OutletDevice(config["device_id"], config["ip"], config["local_key"])
    d.set_version(float(config["version"]))
    
    print("📡 Obteniendo estado actual...")
    data = d.status()
    print(f"✅ Estado inicial: {json.dumps(data, indent=2)}")
    
    print("\n👂 Escuchando cambios por 15 segundos...")
    print("👉 ¡VE A TOCAR EL TIMBRE AHORA! 🏃‍♂️💨")
    
    start = time.time()
    while time.time() - start < 15:
        # Leer estado continuamente para ver si cambia algo
        try:
            # heartbeat=False para lectura pasiva si es posible, o activa si no
            current = d.status()
            if current != data:
                print(f"⚡ ¡CAMBIO DETECTADO! \n{json.dumps(current, indent=2)}")
                data = current
        except Exception as e:
            print(f"⚠️ Error lectura: {e}")
        time.sleep(0.5)
        
    print("\n🏁 Diagnóstico finalizado.")

except Exception as e:
    print(f"❌ Error de conexión: {e}")
