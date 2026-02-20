#!/usr/bin/env python3
"""
Script para navegar a EPG en TCL: com.tcl.settings → Canal → EPG
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

def navigate_to_tcl_settings(ip):
    """Navegar a com.tcl.settings"""
    print('🔍 Navegando a EPG: com.tcl.settings → Canal → EPG')
    
    # 1. Abrir com.tcl.settings directamente
    print('1. Abriendo com.tcl.settings...')
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'start', '-n', 'com.tcl.settings/.MainActivity'], 
                  capture_output=True, text=True, timeout=5)
    time.sleep(3)
    
    # 2. Navegar a Canal
    print('2. Navegando a Canal...')
    
    # Buscar opción Canal en el menú de configuración TCL
    for i in range(15):
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                      capture_output=True, text=True, timeout=3)
        time.sleep(0.3)
        
        # Tomar screenshot para analizar
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'screencap', '-p', '/sdcard/tcl_settings_menu.png'], 
                      capture_output=True, text=True, timeout=3)
        
        # Esperar un momento
        time.sleep(0.2)
    
    # Seleccionar Canal
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(3)
    
    # 3. Buscar EPG en el menú Canal
    print('3. Buscando opción EPG...')
    
    # Explorar menú Canal buscando EPG
    for i in range(12):
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                      capture_output=True, text=True, timeout=3)
        time.sleep(0.3)
        
        # Tomar screenshot para analizar
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'screencap', '-p', '/sdcard/channel_menu_epg.png'], 
                      capture_output=True, text=True, timeout=3)
        
        # Esperar un momento
        time.sleep(0.2)
    
    # Intentar seleccionar EPG
    print('4. Seleccionando EPG...')
    
    # Buscar EPG en diferentes posiciones
    for attempt in range(3):
        # Subir al inicio del menú
        for i in range(15):
            subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_UP'], 
                          capture_output=True, text=True, timeout=3)
            time.sleep(0.2)
        
        # Bajar hasta encontrar EPG
        for i in range(12):
            subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                          capture_output=True, text=True, timeout=3)
            time.sleep(0.3)
            
            # Intentar seleccionar en diferentes posiciones
            if i in [3, 6, 8, 10]:  # Posiciones comunes para EPG
                subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                              capture_output=True, text=True, timeout=3)
                time.sleep(3)
                
                # Verificar si EPG se abrió
                if check_epg_opened(ip):
                    return True
                
                # Si no es EPG, volver atrás
                subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_BACK'], 
                              capture_output=True, text=True, timeout=3)
                time.sleep(1)
    
    return False

def check_epg_opened(ip):
    """Verificar si EPG se abrió correctamente"""
    print('   Verificando si EPG se abrió...')
    
    # Tomar screenshot para verificar
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'screencap', '-p', '/sdcard/epg_check.png'], 
                  capture_output=True, text=True, timeout=3)
    
    # Esperar a que cargue
    time.sleep(3)
    
    # Verificar content providers
    epg_queries = [
        'content query --uri content://android.media.tv/channel --projection display_number:display_name',
        'content query --uri content://android.media.tv/program --projection channel_id:title',
        'content query --uri content://com.tcl.tvinput.provider/channel --projection display_number:display_name'
    ]
    
    for query in epg_queries:
        try:
            cmd = ['adb', '-s', f'{ip}:5555', 'shell'] + query.split()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.stdout.strip() and 'No result found' not in result.stdout:
                print('   ✅ EPG abierto y datos disponibles!')
                return True
                
        except Exception as e:
            print(f'   Error verificando EPG: {e}')
    
    return False

def extract_epg_channels(ip):
    """Extraer canales desde EPG"""
    print('5. Extrayendo canales desde EPG...')
    
    # Esperar a que cargue completamente
    time.sleep(5)
    
    # Tomar screenshot final del EPG
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'screencap', '-p', '/sdcard/epg_final.png'], 
                  capture_output=True, text=True, timeout=3)
    
    # Verificar content providers
    epg_queries = [
        ('Canales Android TV', 'content query --uri content://android.media.tv/channel --projection display_number:display_name'),
        ('Programas Android TV', 'content query --uri content://android.media.tv/program --projection channel_id:title'),
        ('Canales TCL', 'content query --uri content://com.tcl.tvinput.provider/channel --projection display_number:display_name'),
        ('Programas TCL', 'content query --uri content://com.tcl.tvinput.provider/program --projection channel_id:title'),
        ('Preview Programs', 'content query --uri content://android.media.tv/preview_program --projection channel_id:title')
    ]
    
    for name, query in epg_queries:
        try:
            print(f'   Probando: {name}')
            cmd = ['adb', '-s', f'{ip}:5555', 'shell'] + query.split()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.stdout.strip() and 'No result found' not in result.stdout:
                print(f'   ✅ Datos encontrados: {name}')
                
                # Parsear canales
                channels = {}
                lines = result.stdout.splitlines()
                
                for line in lines:
                    num_match = re.search(r'display_number=([^,]+)', line)
                    name_match = re.search(r'display_name=([^,]+)', line)
                    channel_match = re.search(r'channel_id=([^,]+)', line)
                    title_match = re.search(r'title=([^,]+)', line)
                    
                    if num_match and name_match:
                        number = num_match.group(1).strip()
                        name = name_match.group(1).strip()
                        key = name.lower()
                        channels[key] = number
                    elif channel_match and title_match:
                        channel_id = channel_match.group(1).strip()
                        title = title_match.group(1).strip().strip('"')
                        channels[title.lower()] = channel_id
                
                if channels:
                    return channels
                    
        except Exception as e:
            print(f'   Error: {e}')
    
    return None

def main():
    """Función principal"""
    print("📺 Navegación a EPG TCL (com.tcl.settings)")
    print("=" * 60)
    
    ip = get_tv_ip()
    if not ip:
        print("❌ No hay TV conectada vía ADB")
        return
    
    print(f"📡 TV conectada: {ip}")
    
    try:
        # Navegar al EPG
        if navigate_to_tcl_settings(ip):
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
        else:
            print("\n❌ No se pudo acceder al EPG")
        
        # Volver al inicio
        print("6. Volviendo al inicio...")
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_HOME'], 
                      capture_output=True, text=True, timeout=3)
        
        print("\n📋 Resumen:")
        print("✅ Ruta navegada: com.tcl.settings → Canal → EPG")
        print("📁 Screenshots guardados en: /sdcard/")
        print("🔍 Resultados en: test/digital.json")
        
    except Exception as e:
        print(f"Error durante navegación EPG: {e}")

if __name__ == "__main__":
    main()
