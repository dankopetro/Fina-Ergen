
import subprocess
import time
import pychromecast
import sys

import sys

TV_IP = sys.argv[1] if len(sys.argv) > 1 else None
DECO_IP = sys.argv[2] if len(sys.argv) > 2 else None

if not TV_IP or not DECO_IP:
    print("Uso: python3 wake_deco.py <TV_IP> <DECO_IP>")
    sys.exit(1)

def adb_command(cmd_list):
    full_cmd = ['adb', '-s', f'{TV_IP}:5555', 'shell', 'input', 'keyevent'] + cmd_list
    subprocess.run(full_cmd)

def switch_tv_to_air():
    print("📺 Cambiando TV a Aire (Desconectando HDMI)...")
    adb_command(['170']) # KEYCODE_TV
    time.sleep(3)

def wake_deco_with_cast():
    print("🚀 Lanzando Cast para despertar Deco...")
    try:
        cast = pychromecast.Chromecast(DECO_IP)
        cast.wait()
        # YouTube App ID: 233637DE
        cast.start_app("233637DE")
        print("   YouTube lanzado.")
        time.sleep(8) # Dejar que cargue y despierte
        
        print("🛑 Cerrando Cast...")
        cast.quit_app()
        time.sleep(2)
    except Exception as e:
        print(f"   Error en Cast: {e}")

def switch_tv_to_deco_input():
    print("🔌 Cambiando TV a entrada Deco (Secuencia Home)...")
    
    # 1. HOME
    adb_command(['3'])
    time.sleep(3)

    # 2. Arriba (Menu iconos)
    adb_command(['19'])
    time.sleep(0.5)

    # 3. Derecha x3 (Ir a Entradas)
    adb_command(['22'])
    time.sleep(0.2)
    adb_command(['22'])
    time.sleep(0.2)
    adb_command(['22'])
    time.sleep(0.5)

    # 4. OK (Abrir menu)
    adb_command(['66'])
    time.sleep(2)

    # 5. Abajo (Seleccionar Deco)
    adb_command(['20'])
    time.sleep(0.5)

    # 6. OK (Entrar)
    adb_command(['66'])

if __name__ == "__main__":
    print("⏰ INICIANDO PROTOCOLO DE DESPERTAR DECO...")
    
    # Paso 1: Ir a TV de Aire para refrescar estado HDMI
    switch_tv_to_air()
    
    # Paso 2: Bombardear el Deco con Cast para que despierte del screensaver
    wake_deco_with_cast()
    
    # Paso 3: Volver a poner la entrada
    switch_tv_to_deco_input()
    
    print("✅ Protocolo finalizado.")
