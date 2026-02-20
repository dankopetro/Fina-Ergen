import subprocess
import sys

def list_packages():
    """Enumera todos los paquetes instalados en el dispositivo conectado"""
    # 1. Encontrar IP conectada
    tv_ips = ['192.168.0.11', '192.168.0.10']
    connected_ip = None
    
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        for ip in tv_ips:
            if ip in result.stdout and 'device' in result.stdout:
                connected_ip = ip
                break
    except Exception as e:
        print(f"Error ADB: {e}")
        return

    if not connected_ip:
        print("No hay TV conectada. Ejecuta tv_on.py primero.")
        return

    print(f"Listando paquetes de {connected_ip}...")
    
    # 2. Listar paquetes
    try:
        # PM List Packages
        cmd = ['adb', '-s', f'{connected_ip}:5555', 'shell', 'pm', 'list', 'packages']
        res = subprocess.run(cmd, capture_output=True, text=True)
        
        all_pkgs = res.stdout.splitlines()
        
        # Filtros para encontrar algo relevante
        keywords = ['tv', 'live', 'input', 'channel', 'launcher', 'home', 'iptv', 'm3u', 'm']
        
        print(f"\n--- PAQUETES SOSPECHOSOS ({len(all_pkgs)} total) ---")
        for line in all_pkgs:
            pkg = line.replace('package:', '').strip()
            if any(k in pkg.lower() for k in keywords):
                print(pkg)
                
    except Exception as e:
        print(f"Error listando paquetes: {e}")

if __name__ == "__main__":
    list_packages()
