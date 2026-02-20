
import subprocess
import time
import pychromecast
import sys

TV_IP = "192.168.0.10"
DECO_IP = "192.168.0.9"

def adb_tv_command(keycode):
    """Envia tecla a la TV esperando que pase por CEC"""
    subprocess.run(['adb', '-s', f'{TV_IP}:5555', 'shell', 'input', 'keyevent', str(keycode)])

def wake_deco_sequence():
    print("🚀 1. Despertando Deco con Cast (YouTube)...")
    try:
        services, browser = pychromecast.discovery.discover_chromecasts(timeout=5)
        cast = None
        for s in services:
             if s.host == DECO_IP:
                 cast = pychromecast.get_chromecast_from_cast_info(s, browser.zc)
                 break
        
        if not cast: cast = pychromecast.Chromecast(DECO_IP)
            
        cast.wait()
        cast.start_app("233637DE") # YouTube
        
        print("⏳ Esperando 12s para estabilizar señal...")
        time.sleep(12) 
        
        print("🛑 2. Cerrando Cast (Volviendo a Home)...")
        cast.quit_app()
        
        print("⏳ Esperando 4s para cargar Menú TPlay...")
        time.sleep(4)

        # Intento de Navegación a Ciegas por CEC
        print("👉 3. Intentando ir a la derecha (TV en Vivo)...")
        adb_tv_command(22) # DPAD_RIGHT
        time.sleep(1)
        
        print("✅ 4. Seleccionando (OK)...")
        adb_tv_command(23) # DPAD_CENTER (Probamos 23 que es más estándar para CEC)
        time.sleep(0.5)
        adb_tv_command(66) # ENTER (Por si acaso)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    wake_deco_sequence()
