#!/usr/bin/env python3
"""
Script para navegar a EPG en TCL: Configuración → Canal → EPG
"""

import subprocess
import json
import time
import re

def get_tv_ip():
    """Obtener IP de TV conectada"""
    tv_ips = ['192.168.0.11', '192.168.0.10']
    for ip in tv_ips:
        try:
            result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'echo', 'test'], 
                                  capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                return ip
        except:
            continue
    return None

def navigate_to_epg(ip):
    """Navegar al menu EPG"""
    print('🔍 Navegando a EPG: Configuración → Canal → EPG')
    
    # 1. Iniciar app de TV
    print('1. Iniciando app de TV...')
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'start', '-n', 'com.tcl.tv/.TVActivity'], 
                  capture_output=True, text=True, timeout=5)
    time.sleep(3)
    
    # 2. Abrir Configuración
    print('2. Abriendo Configuración...')
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_SETTINGS'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(2)
    
    # 3. Navegar a Canal
    print('3. Navegando a Canal...')
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(1)
    
    # Buscar opción Canal
    for i in range(6):
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                      capture_output=True, text=True, timeout=3)
        time.sleep(0.5)
    
    # Seleccionar Canal
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(3)
    
    # 4. Buscar EPG en el menú Canal
    print('4. Buscando opción EPG...')
    
    # Explorar menú Canal buscando EPG
    for i in range(10):
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                      capture_output=True, text=True, timeout=3)
        time.sleep(0.5)
    
    # Intentar seleccionar EPG
    print('5. Seleccionando EPG...')
    
    for i in range(8):
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                      capture_output=True, text=True, timeout=3)
        time.sleep(0.5)
    
    # Seleccionar EPG
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(4)
    
    return True

def extract_epg_channels(ip):
    """Extraer canales desde EPG"""
    print('6. Extrayendo canales desde EPG...')
    
    # Esperar a que cargue EPG
    time.sleep(5)
    
    # Tomar screenshot del EPG
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'screencap', '-p', '/sdcard/epg_opened.png'], 
                  capture_output=True, text=True, timeout=3)
    
    # Verificar content providers
    epg_queries = [
        ('Canales', 'content query --uri content://android.media.tv/channel --projection display_number:display_name'),
        ('Programas', 'content query --uri content://android.media.tv/program --projection channel_id:title'),
        ('TCL EPG', 'content query --uri content://com.tcl.tvinput.provider/channel --projection display_number:display_name')
    ]
    
    for name, query in epg_queries:
        try:
            print(f'   Probando: {name}')
            cmd = ['adb', '-s', f'{ip}:5555', 'shell'] + query.split()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.stdout.strip() and 'No result found' not in result.stdout:
                print(f'✅ Datos encontrados: {name}')
                
                # Parsear canales
                channels = {}
                lines = result.stdout.splitlines()
                
                for line in lines:
                    num_match = re.search(r'display_number=([^,]+)', line)
                    name_match = re.search(r'display_name=([^,]+)', line)
                    
                    if num_match and name_match:
                        number = num_match.group(1).strip()
                        name = name_match.group(1).strip()
                        key = name.lower()
                        channels[key] = number
                
                if channels:
                    return channels
                    
        except Exception as e:
            print(f'   Error: {e}')
    
    return None

def main():
    """Función principal"""
    print("📺 Navegación a EPG TCL")
    print("=" * 50)
    
    ip = get_tv_ip()
    if not ip:
        print("❌ No hay TV conectada vía ADB")
        return
    
    print(f"📡 TV conectada: {ip}")
    
    try:
        # Navegar al EPG
        if navigate_to_epg(ip):
            # Extraer canales
            channels = extract_epg_channels(ip)
            
            if channels:
                # Guardar resultados
                with open('test/digital.json', 'w', encoding='utf-8') as f:
                    json.dump(channels, f, indent=4, ensure_ascii=False)
                
                print(f"\n✅ Éxito: {len(channels)} canales extraídos desde EPG")
                print("\n📋 Canales encontrados:")
                for i, (name, number) in enumerate(list(channels.items())[:10]):
                    print(f"  {name}: {number}")
                if len(channels) > 10:
                    print(f"  ... y {len(channels) - 10} más")
            else:
                print("\n❌ No se pudieron extraer canales desde EPG")
        
        # Volver al inicio
        print("7. Volviendo al inicio...")
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_HOME'], 
                      capture_output=True, text=True, timeout=3)
        
        print("\n📋 Resumen:")
        print("✅ Ruta navegada: Configuración → Canal → EPG")
        print("📁 Screenshots guardados en: /sdcard/")
        print("🔍 Resultados en: test/digital.json")
        
    except Exception as e:
        print(f"Error durante navegación EPG: {e}")

if __name__ == "__main__":
    main()
