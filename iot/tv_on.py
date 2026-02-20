import subprocess
import sys
import time
import socket
import os
import json
import threading

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(PROJECT_ROOT, "fina_settings.json")

# Configuración de los objetivos (TVs)
# Cada objetivo tiene su IP y su MAC address para Wake-on-LAN
def load_targets():
    """Carga la lista de TVs desde fina_settings.json (máx 4, solo enabled).
    
    Adicionalmente, escanea un rango de IPs si se define 'scan_range' en settings,
    o utiliza un rango por defecto (ej: .10 a .15) para máxima flexibilidad.
    """
    default_targets = [
        {"ip": "192.168.0.10", "mac": "34:51:80:f9:86:4a"},
        {"ip": "192.168.0.11", "mac": "38:c8:04:31:17:b0"},
        # Agregamos algunas IPs comunes por defecto para el escaneo ciego
        {"ip": "192.168.0.12", "mac": ""},
        {"ip": "192.168.0.13", "mac": ""},
        {"ip": "192.168.0.14", "mac": ""},
    ]

    try:
        if not os.path.exists(SETTINGS_PATH):
            return default_targets

        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        tvs = data.get("tvs", [])
        targets = []
        for tv in tvs:
            if not tv.get("enabled", True):
                continue
            ip = tv.get("ip")
            if not ip: continue
            mac = tv.get("mac", "")
            targets.append({"ip": ip, "mac": mac})
        
        # Merge con defaults (sin duplicar IPs)
        existing_ips = {t['ip'] for t in targets}
        for dt in default_targets:
            if dt['ip'] not in existing_ips:
                targets.append(dt)

        return targets
    except Exception:
        return default_targets

def wake_on_lan(mac_address, ip_hint=None):
    """Envía un paquete mágico WoL a la dirección MAC especificada"""
    if not mac_address: return False
    
    try:
        # Limpiar MAC
        mac_clean = mac_address.replace(':', '').replace('-', '')
        if len(mac_clean) != 12:
            return False
            
        mac_bytes = bytes.fromhex(mac_clean)
        magic_packet = b'\xff' * 6 + mac_bytes * 16
        
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # 1. Enviar a broadcast general
            try:
                sock.sendto(magic_packet, ('<broadcast>', 9))
            except Exception:
                pass

            # 2. Enviar a broadcast de subred (más efectivo)
            if ip_hint:
                try:
                    # Asumiendo red clase C /24
                    parts = ip_hint.split('.')
                    subnet_broadcast = f"{parts[0]}.{parts[1]}.{parts[2]}.255"
                    sock.sendto(magic_packet, (subnet_broadcast, 9))
                except Exception:
                    pass
            
        return True
    except Exception as e:
        # print(f'⚠ Error enviando WoL a {mac_address}: {e}')
        return False

def check_device_connection(ip):
    """Verifica si el dispositivo está conectado y responde"""
    try:
        result = subprocess.run(
            ['adb', 'devices'],
            capture_output=True,
            text=True,
            timeout=2
        )
        for line in result.stdout.split('\n'):
            if ip in line and 'device' in line and 'offline' not in line:
                return True
        return False
    except Exception:
        return False

def is_screen_on(ip):
    """Verifica si la pantalla ya está encendida via ADB"""
    try:
        # Check para diferentes versiones de Android TV
        result = subprocess.run(
            ['adb', '-s', f'{ip}:5555', 'shell', 'dumpsys', 'power'],
            capture_output=True,
            text=True,
            timeout=3
        )
        output = result.stdout
        # Patrones comunes que indican que está encendida
        if "mWakefulness=Awake" in output or "Display Power: state=ON" in output:
            return True
        return False
    except Exception:
        return False

def try_connect_and_wake(target):
    """Intenta conectar a una IP específica y despertarla. Retorna True si tiene éxito."""
    ip = target['ip']
    mac = target['mac']

    # 1. WoL preventivo
    if mac: wake_on_lan(mac, ip_hint=ip)
    
    # 2. Intentar conexión ADB
    try:
        subprocess.run(['adb', 'connect', ip], capture_output=True, timeout=2)
    except:
        pass
        
    # 3. Verificar si conectó
    if check_device_connection(ip):
        print(f"✓ TV Detectada en {ip}")
        
        # 4. Check estado pantalla
        if is_screen_on(ip):
            print(f"  └─ Pantalla YA ENCENDIDA. Todo listo.")
            return True
        else:
            print(f"  └─ Pantalla apagada. Enviando WAKEUP...")
            # WAKEUP
            subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_WAKEUP'], 
                          capture_output=True, timeout=5)
            time.sleep(3)
            # POWER si falló
            if not is_screen_on(ip):
                print(f"  └─ WAKEUP falló. Intentando POWER...")
                subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_POWER'], 
                              capture_output=True, timeout=5)
            return True
    return False

def connect_loop_parallel():
    """Escaneo paralelo de todos los targets para máxima velocidad."""
    print('=' * 60)
    print('TV ON - Modo Escaneo Multicanal')
    print('=' * 60)
    
    targets = load_targets()
    # print(f"Targets cargados: {len(targets)}")
    
    # Usar hilos para probar todas las IPs casi simultáneamente
    threads = []
    results = []
    
    def worker(tgt):
        if try_connect_and_wake(tgt):
            results.append(tgt['ip'])

    # Lanzar hilos
    for t in targets:
        th = threading.Thread(target=worker, args=(t,))
        th.start()
        threads.append(th)
        
    # Esperar (con timeout global razonable)
    for th in threads:
        th.join(timeout=5)
        
    if results:
        print(f"\n✓ ÉXITO: {len(results)} TV(s) gestionada(s): {', '.join(results)}")
        # Guardar la última IP exitosa en un archivo temporal para que otros scripts la usen rápido
        try:
             with open("/tmp/fina_last_tv_ip", "w") as f:
                 f.write(results[0])
        except: pass
        sys.exit(0)
    else:
        print("\n✗ No se pudo conectar a ninguna TV.")
        sys.exit(1)

if __name__ == '__main__':
    try:
        connect_loop_parallel()
    except KeyboardInterrupt:
        print('\nCancelado por usuario.')
        sys.exit(1)
