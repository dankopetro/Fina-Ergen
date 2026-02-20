import os
import time
import subprocess
import sys

# Redirect all output to a log file for debugging
log_file = open("/tmp/waydroid_launch.log", "a")
sys.stdout = log_file
sys.stderr = log_file

print(f"\n--- Launch Attempt: {time.ctime()} ---")

# TUYA PACKAGE NAME
PKG = "com.tuya.smart"

def launch_video():
    uid = os.getuid()
    wayland_socket = f"/run/user/{uid}/wayland-1"
    
    print("🚀 Iniciando Motor Waydroid...")
    
    # DESPERTAR: Si la ventana está en el Tray, sacarla AHORA.
    # Matar kdocker libera la ventana y la devuelve al escritorio.
    subprocess.run("pkill kdocker", shell=True)
    
    # Check si ya está corriendo para no matar todo
    skip_init = False
    env = os.environ.copy() # Initialize env here, will be updated later if needed
    try:
        status = subprocess.check_output("waydroid status", shell=True).decode()
        if "RUNNING" in status and "STOPPED" not in status:
            print("⚡ Waydroid ya está activo. Reutilizando sesión.")
            skip_init = True
            
            # Recuperar env vars si es posible (asumimos wayland-1)
            if "WAYLAND_DISPLAY" not in env:
                env["WAYLAND_DISPLAY"] = "wayland-1"
    except Exception as e:
        print(f"⚠️ Error al chequear estado de Waydroid: {e}")
        pass # Continue as if not running, will attempt full init

    if not skip_init:
        # 0. Limpiar (Solo si no estaba corriendo o estaba zombie)
        subprocess.run("waydroid session stop", shell=True)
        time.sleep(1)

        # 1. Chequear entorno gráfico
        # env = os.environ.copy() # env is already initialized above
        if "WAYLAND_DISPLAY" not in env:
            print("🖥️ Lanzando Weston (Display Server)...")
            # Lanzar Weston en background con resolución PHONE
            subprocess.Popen(["weston", "--width=455", "--height=822", "--socket=wayland-1"], env=env)
            
            # ESPERAR ACTIVAMENTE AL SOCKET (Clave del éxito)
            print("⏳ Esperando socket gráfico...")
            for i in range(10):
                if os.path.exists(wayland_socket):
                    print("✅ Socket detectado.")
                    break
                time.sleep(1)
            
            env["WAYLAND_DISPLAY"] = "wayland-1"
            
            # MINIMIZAR AL TRAY AUTOMÁTICAMENTE
            print("📉 Ocultando ventana...")
            min_script = os.path.join(os.path.dirname(__file__), "minimizar_weston.sh")
            subprocess.Popen(["bash", min_script])

        # 2. Iniciar Waydroid (con el entorno correcto)
        print("🔛 Iniciando Sesión Android...")
        subprocess.Popen("waydroid session start", shell=True, env=env)

        # 3. Esperar a que el sistema esté listo
        print("⏳ Esperando arranque de Android...")
        time.sleep(5) # Waydroid tarda en levantar servicios internos
    
    # 4. Acción Principal
    if len(sys.argv) > 1 and sys.argv[1] == "--desktop":
        print("🖥️ Mostrando Escritorio...")
        subprocess.run("waydroid show-full-ui", shell=True, env=env)
    else:
        # MODO ATENDER / CÁMARA
        print(f"📞 Despertando UI para atender...")
        subprocess.run("waydroid show-full-ui", shell=True, env=env)
        subprocess.run("waydroid shell input keyevent KEYCODE_WAKEUP", shell=True)
        
        # RÁFAGA INTELIGENTE (Smart Polling - Con SUDO NOPASSWD)
        print("🔭 Buscando Notificación de Tuya (Máx 60s)...")
        found = False
        for i in range(30):
            try:
                # Buscar notificación activa de Tuya (Raw Output)
                # Ejecutamos dumpsys limpio y filtramos en Python para evitar errores de shell
                out = subprocess.check_output("sudo waydroid shell dumpsys notification", shell=True).decode()
                
                # Buscamos el paquete exacto o el nombre clave
                if "pkg=com.tuya.smart" in out or "tuya" in out.lower():
                    print("🎯 ¡Notificación DETECTADA en el Sistema!")
                    print("⏳ Esperando animación (4.5s)...")
                    time.sleep(4.5) # Esperar que baje visualmente (Aumentado por feedback)
                    
                    print("👆 TAP 1 (333, 154)")
                    subprocess.run("sudo waydroid shell input tap 333 154", shell=True)
                    
                    time.sleep(1.5)
                    print("👆 TAP 2 (Confirmación)")
                    subprocess.run("sudo waydroid shell input tap 333 154", shell=True)
                    
                    found = True
                    break
            except:
                pass
            
            time.sleep(2.0)
            print(".", end="", flush=True)

        if not found:
            print("⚠️ Timeout: No llegó notificación en 60s.")
    
    # Bring to front
    time.sleep(2)
    # El título suele ser Waydroid cuando mostramos full UI
    subprocess.run(f"wmctrl -a 'Waydroid' || wmctrl -a 'Tuya Smart' || true", shell=True)

if __name__ == "__main__":
    launch_video()
