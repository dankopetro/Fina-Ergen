import subprocess
import re

def get_connected_tv_ip():
    tv_ips = ['192.168.0.11', '192.168.0.10']
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        for ip in tv_ips:
            if ip in result.stdout and 'device' in result.stdout:
                return ip
    except:
        pass
    return None

def scan_screen():
    ip = get_connected_tv_ip()
    if not ip:
        print("No TV connected")
        return

    print(f"Escaneando pantalla de {ip}...")
    
    # 1. Obtener XML de la pantalla
    try:
        # uiautomator dump genera un XML en /sdcard/window_dump.xml
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'uiautomator', 'dump', '/sdcard/window_dump.xml'], 
                     timeout=10, capture_output=True)
        
        # traerlo a local (o leerlo con cat)
        res = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'cat', '/sdcard/window_dump.xml'],
                           capture_output=True, text=True)
        
        xml_content = res.stdout
        
        # 2. Buscar textos con regex simple (text="ALGO")
        texts = re.findall(r'text="([^"]+)"', xml_content)
        
        # Filtrar textos vacíos o irrelevantes
        clean_texts = [t for t in texts if len(t) > 2]
        
        print("\n--- TEXTO ENCONTRADO EN PANTALLA ---")
        for t in clean_texts:
            print(t)
            
    except Exception as e:
        print(f"Error escaneando: {e}")

if __name__ == "__main__":
    scan_screen()
