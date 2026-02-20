#!/usr/bin/env python3
import tinytuya
import json
import time
import socket

# Configuración
DEVICE_ID = "eba60f4e71e9782575wdkh"
LOCAL_KEY = "235f1929a575c07d" # LLAVE MAESTRA ORIGINAL
IP_ADDRESS = "192.168.0.5"

def scan_ports(ip):
    # Escaneo Ampliado de Puertos Sospechosos y Rango IoT
    target_ports = [6668, 6669, 554, 8554, 80, 8080, 443, 8883, 1883, 3333, 3334, 1212, 12345]
    # + Rango dinámico
    target_ports += list(range(6000, 7000))
    
    print(f"\n🔍 Escaneando {len(target_ports)} puertos en {ip} (Modo Agresivo)...")
    open_ports = []
    
    # Timeout muy agresivo para velocidad
    for port in target_ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.05) # 50ms
            if s.connect_ex((ip, port)) == 0:
                print(f"   🟢 ¡PUERTO {port} ABIERTO!")
                open_ports.append(port)
            s.close()
        except: pass
            
    if not open_ports:
        print("   🔴 Sin puertos abiertos detectados.")
    return open_ports

def listen_to_device():
    versions = [3.3, 3.4, 3.1, 3.5]
    print(f"\n📡 Iniciando Bucle de Caza en {IP_ADDRESS}...")
    print("👉 VE A TOCAR EL TIMBRE Y ATIENDE LA LLAMADA.")
    print("   El script intentará conectar cada 2s hasta lograrlo.\n")

    while True:
        # Pre-scan rápido
        open_ports = scan_ports(IP_ADDRESS)
        
        if 6668 in open_ports or 6669 in open_ports:
            print("⚡ DETECTADO PUERTO TUYA ABIERTO. ATACANDO...")
            for ver in versions:
                try:
                    print(f"   Infiltrando con v{ver}...", end="")
                    d = tinytuya.Device(dev_id=DEVICE_ID, address=IP_ADDRESS, local_key=LOCAL_KEY, version=ver)
                    d.set_socketPersistent(True)
                    data = d.status()
                    if data and 'dps' in data:
                        print(f"\n\n🎉 ¡HACKEO EXITOSO (v{ver})! 🎉")
                        print(json.dumps(data, indent=4))
                        
                        # Quedarse escuchando
                        print("👂 Escuchando stream de datos...")
                        while True:
                            payload = d.receive()
                            if payload: print(f"📩 DATA: {payload}")
                            time.sleep(0.1)
                    else:
                        print(" Falló (auth).")
                except Exception as e:
                    print(f" ❌") # Error silencioso para no spamear
                    pass
        else:
            print("💤 Dispositivo dormido/cerrado. Reintentando en 2s...", end="\r")
        
        time.sleep(2)

if __name__ == "__main__":
    print("--- 🕵️ HACKER DOORBELL TOOL v2.0 (MODO CAZADOR) ---")
    listen_to_device()
