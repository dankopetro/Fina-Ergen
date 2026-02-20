import subprocess
import time
import sys

def get_connected_tv_ip():
    """Busca qué IP de TV está conectada vía ADB"""
    tv_ips = []
    if len(sys.argv) > 1:
        tv_ips = [sys.argv[1]]
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        print("Dispositivos ADB actuales:\n" + result.stdout)
        
        for ip in tv_ips:
            if ip in result.stdout and 'device' in result.stdout:
                return ip
    except Exception as e:
        print(f"Error buscando dispositivos: {e}")
    return None

def send_key(ip, keycode, name):
    print(f"Probando {name} (Keycode {keycode})...")
    cmd = ['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', str(keycode)]
    subprocess.run(cmd)
    time.sleep(2) # Pausa para observar el efecto

def test_tv_commands():
    print("=== TEST DE COMANDOS DE TV ===")
    
    ip = get_connected_tv_ip()
    if not ip:
        print("✗ No se detectó ninguna TV conectada (192.168.0.10 o .11).")
        print("Asegúrate de haber ejecutado 'tv_on.py' primero.")
        sys.exit(1)
        
    print(f"✓ TV detectada en: {ip}")
    print("Iniciando secuencia de prueba en 5 segundos...")
    print("¡Mira la pantalla de la TV!")
    time.sleep(5)
    
    # 1. Volumen (Ráfaga rápida)
    print("Subiendo volumen 5 puntos (RÁPIDO)...")
    keys_up = ['24'] * 5
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent'] + keys_up)
    
    time.sleep(1)
    
    print("Bajando volumen 5 puntos (RÁPIDO)...")
    keys_down = ['25'] * 5
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent'] + keys_down)
    
    send_key(ip, 164, "Mute / Silencio (Activado)")
    time.sleep(2)
    send_key(ip, 164, "Unmute / Sonido (Desactivado)")
    
    send_key(ip, 167, "Canal Anterior (CH-)")
    
    # 2.5 Canal Numérico (80.1)
    print("Probando poner canal 80.1 (Dígitos + Punto Numérico)...")
    # 8(15), 0(7), .(158), 1(8)
    cmd_digits = ['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', '15', '7', '158', '8']
    subprocess.run(cmd_digits)
    time.sleep(2)
    
    # 3. Apps (YouTube)
    print("Probando abrir YouTube...")
    cmd_yt = ['adb', '-s', f'{ip}:5555', 'shell', 'monkey', '-p', 'com.google.android.youtube.tv', '-c', 'android.intent.category.LAUNCHER', '1']
    subprocess.run(cmd_yt, capture_output=True)
    
    print("Esperando 5 segundos con YouTube abierto...")
    time.sleep(5)
    
    # 4. Salir / Volver a TV (Con lógica de kill)
    print("Probando 'Volver a la Tele' (Matando apps primero)...")
    
    apps_to_kill = [
        "com.google.android.youtube.tv",
    ]
    
    for app in apps_to_kill:
        print(f"Matando {app}...")
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'force-stop', app], capture_output=True)
    
    # Intentamos paquete específico detectado (TCL)
    pkg = "com.tcl.tv"
    print(f"Intentando abrir {pkg}...")
    cmd = ['adb', '-s', f'{ip}:5555', 'shell', 'monkey', '-p', pkg, '-c', 'android.intent.category.LAUNCHER', '1']
    subprocess.run(cmd, capture_output=True)
    
    # Fallback keycode
    time.sleep(1)
    if True: # Simular que seguimos (en utils es condicional)
         send_key(ip, 170, "KEYCODE_TV (Fallback)")
    
    print("\n=== TEST FINALIZADO ===")

if __name__ == "__main__":
    try:
        test_tv_commands()
    except KeyboardInterrupt:
        print("\nTest cancelado.")
