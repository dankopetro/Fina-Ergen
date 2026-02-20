#!/usr/bin/env python3
import subprocess
import requests
import os
import lzma
import shutil
import sys
import time

# Configuración
FRIDA_VERSION = "17.6.2" # Sincronizado con cliente local
ARCH = "x86_64"
DOWNLOAD_URL = f"https://github.com/frida/frida/releases/download/{FRIDA_VERSION}/frida-server-{FRIDA_VERSION}-android-{ARCH}.xz"
LOCAL_FILE = f"frida-server.xz"
EXTRACTED_FILE = "frida-server"
REMOTE_PATH = "/data/local/tmp/frida-server" # Ruta correcta y segura

def run_cmd(cmd):
    # Usamos sudo waydroid shell para máxima autoridad
    subprocess.run(f"sudo waydroid shell {cmd}", shell=True)

def main():
    print(f"📥 Descargando Frida Server {FRIDA_VERSION} ({ARCH})...")
    try:
        r = requests.get(DOWNLOAD_URL, stream=True)
        with open(LOCAL_FILE, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        print(f"❌ Error descarga: {e}")
        return

    print("📦 Descomprimiendo...")
    try:
        with lzma.open(LOCAL_FILE, 'rb') as source:
            with open(EXTRACTED_FILE, 'wb') as target:
                shutil.copyfileobj(source, target)
    except:
        print("❌ Error descomprimiendo. ¿Instalaste lzma?")
        return

    print("🚀 Inyectando en Waydroid (Requiere contraseña sudo)...")
    
    # 1. Empujar archivo (ADB es más fácil para transferir archivos que waydroid shell)
    # Primero nos aseguramos que ADB conecte
    subprocess.run("adb connect 192.168.240.112:5555", shell=True)
    subprocess.run(f"adb push {EXTRACTED_FILE} {REMOTE_PATH}", shell=True)
    
    # 2. Permisos y Ejecución (usando waydroid shell root)
    run_cmd(f"chmod 755 {REMOTE_PATH}")
    
    # Matar instancias viejas
    run_cmd("killall frida-server")
    time.sleep(1)
    
    print("🧟 Arrancando Frida Server en background...")
    # Lanzar server
    subprocess.Popen("sudo waydroid shell /data/local/tmp/frida-server &", shell=True)
    
    time.sleep(3)
    print("✅ Inyección completada. Verificando...")
    subprocess.run("frida-ps -U | head", shell=True)

if __name__ == "__main__":
    main()
