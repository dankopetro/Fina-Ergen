import re
import sys
import os
import time
import subprocess

def get_waydroid_ip():
    status = subprocess.getoutput("waydroid status")
    ip_match = re.search(r"IP:\s+(\d+\.\d+\.\d+\.\d+)", status)
    return f"{ip_match.group(1)}:5555" if ip_match else "192.168.240.112:5555"

def hangup_doorbell():
    adb_target = get_waydroid_ip()
    print(f"📞 Ejecutando comando: CORTAR TIMBRE (Destino: {adb_target})")
    
    try:
        subprocess.run(f"adb connect {adb_target}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Enviar TAP (Botón Rojo: 225, 710)
        print("👉 Presionando botón de colgar...")
        subprocess.run(f"adb -s {adb_target} shell input tap 225 710", shell=True)
        
        # Volver atrás
        time.sleep(1)
        subprocess.run(f"adb -s {adb_target} shell input keyevent 4", shell=True)
        
        time.sleep(1)
        
        # 2. Matar scrcpy (Ventana de video)
        # Esto sirve para limpiar la pantalla del usuario
        print("🚫 Cerrando ventana de video (scrcpy)...")
        subprocess.run("pkill scrcpy", shell=True)
        
        print("✅ Llamada finalizada y limpieza completada.")
        
        # Feedback auditivo para confirmar
        try:
             # Intentar usar utils si está disponible, sino espeak directo
             sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
             from utils import speak
             speak("Timbre desconectado.", None)
        except:
             subprocess.run("spd-say 'Timbre desconectado'", shell=True)

    except Exception as e:
        print(f"❌ Error al cortar timbre: {e}")

if __name__ == "__main__":
    hangup_doorbell()
