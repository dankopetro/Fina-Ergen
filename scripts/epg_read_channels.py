#!/usr/bin/env python3
"""
Script para dejar TV en EPG y leer todos los canales
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

def setup_epg_and_wait(ip):
    """Configurar TV en EPG y esperar que cargue canales"""
    print('🔍 Configurando TV en EPG para lectura de canales')
    
    # 1. Abrir com.tcl.settings
    print('1. Abriendo com.tcl.settings...')
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'start', '-n', 'com.tcl.settings/.MainActivity'], 
                  capture_output=True, text=True, timeout=5)
    time.sleep(3)
    
    # 2. Navegar a Canal
    print('2. Navegando a Canal...')
    
    # Bajar 7 veces para llegar a Canal
    for i in range(7):
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                      capture_output=True, text=True, timeout=3)
        time.sleep(0.2)
    
    # Seleccionar Canal
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(3)
    
    # 3. Navegar a EPG
    print('3. Navegando a EPG...')
    
    # Bajar 5 veces para llegar a EPG
    for i in range(5):
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                      capture_output=True, text=True, timeout=3)
        time.sleep(0.2)
    
    # Seleccionar EPG
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(4)
    
    print('✅ TV configurada en EPG')
    return True

def read_all_channels_from_epg(ip):
    """Leer todos los canales disponibles desde EPG"""
    print('📖 Leyendo todos los canales desde EPG...')
    
    # Esperar a que EPG cargue completamente
    print('⏳ Esperando carga completa del EPG (15 segundos)...')
    time.sleep(15)
    
    # Tomar screenshot del EPG cargado
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'screencap', '-p', '/sdcard/epg_loaded.png'], 
                  capture_output=True, text=True, timeout=3)
    
    # Intentar todos los métodos de lectura de canales
    channels = {}
    
    # Método 1: Content providers estándar
    print('4.1 Intentando content providers estándar...')
    
    standard_uris = [
        ('Canales Android TV', 'content query --uri content://android.media.tv/channel --projection display_number:display_name'),
        ('Programas Android TV', 'content query --uri content://android.media.tv/program --projection channel_id:title'),
        ('Preview Programs', 'content query --uri content://android.media.tv/preview_program --projection channel_id:title'),
        ('Watched Programs', 'content query --uri content://android.media.tv/watched_program --projection channel_id:title')
    ]
    
    for name, query in standard_uris:
        try:
            print(f'   Probando: {name}')
            cmd = ['adb', '-s', f'{ip}:5555', 'shell'] + query.split()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.stdout.strip() and 'No result found' not in result.stdout:
                print(f'   ✅ Datos encontrados: {name}')
                
                # Parsear canales
                for line in result.stdout.splitlines():
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
                    print(f'   {len(channels)} canales extraídos')
                    break
                    
        except Exception as e:
            print(f'   Error: {e}')
    
    # Método 2: Content providers TCL
    if not channels:
        print('4.2 Intentando content providers TCL...')
        
        tcl_uris = [
            ('Canales TCL', 'content query --uri content://com.tcl.tvinput.provider/channel --projection display_number:display_name'),
            ('Programas TCL', 'content query --uri content://com.tcl.tvinput.provider/program --projection channel_id:title')
        ]
        
        for name, query in tcl_uris:
            try:
                print(f'   Probando: {name}')
                cmd = ['adb', '-s', f'{ip}:5555', 'shell'] + query.split()
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                
                if result.stdout.strip() and 'No result found' not in result.stdout:
                    print(f'   ✅ Datos encontrados: {name}')
                    
                    # Parsear canales
                    for line in result.stdout.splitlines():
                        num_match = re.search(r'display_number=([^,]+)', line)
                        name_match = re.search(r'display_name=([^,]+)', line)
                        
                        if num_match and name_match:
                            number = num_match.group(1).strip()
                            name = name_match.group(1).strip()
                            key = name.lower()
                            channels[key] = number
                    
                    if channels:
                        print(f'   {len(channels)} canales extraídos')
                        break
                        
            except Exception as e:
                print(f'   Error: {e}')
    
    # Método 3: Forzar actualización y reintentar
    if not channels:
        print('4.3 Forzando actualización de EPG...')
        
        # Enviar intents de actualización
        update_intents = [
            'android.media.tv.ACTION_INITIALIZE_PROGRAMS',
            'android.media.tv.ACTION_UPDATE_CHANNEL_LIST',
            'android.media.tv.ACTION_REQUEST_CHANNEL_BROWSABLE',
            'com.tcl.tvinput.action.UPDATE_EPG'
        ]
        
        for intent in update_intents:
            subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'broadcast', '-a', intent], 
                          capture_output=True, text=True, timeout=5)
            print(f'   Enviado: {intent}')
            time.sleep(2)
        
        # Esperar actualización
        print('⏳ Esperando actualización (20 segundos)...')
        time.sleep(20)
        
        # Reintentar lectura
        print('4.4 Reintentando lectura después de actualización...')
        
        try:
            result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'content', 'query', 
                                     '--uri', 'content://android.media.tv/channel', 
                                     '--projection', 'display_number:display_name'], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.stdout.strip() and 'No result found' not in result.stdout:
                print('   ✅ ¡Canales encontrados después de actualización!')
                
                for line in result.stdout.splitlines():
                    num_match = re.search(r'display_number=([^,]+)', line)
                    name_match = re.search(r'display_name=([^,]+)', line)
                    
                    if num_match and name_match:
                        number = num_match.group(1).strip()
                        name = name_match.group(1).strip()
                        key = name.lower()
                        channels[key] = number
                        
        except Exception as e:
            print(f'   Error en reintentar: {e}')
    
    return channels

def main():
    """Función principal"""
    print("📺 Lectura de Canales desde EPG TCL")
    print("=" * 60)
    
    ip = get_tv_ip()
    if not ip:
        print("❌ No hay TV conectada vía ADB")
        return
    
    print(f"📡 TV conectada: {ip}")
    
    try:
        # Configurar TV en EPG
        if setup_epg_and_wait(ip):
            # Leer todos los canales
            channels = read_all_channels_from_epg(ip)
            
            if channels:
                # Guardar resultados
                with open('test/digital.json', 'w', encoding='utf-8') as f:
                    json.dump(channels, f, indent=4, ensure_ascii=False)
                
                print(f"\n✅ Éxito: {len(channels)} canales leídos desde EPG")
                print("\n📋 Canales encontrados:")
                for i, (name, number) in enumerate(list(channels.items())[:15]):
                    print(f"  {name}: {number}")
                if len(channels) > 15:
                    print(f"  ... y {len(channels) - 15} más")
                    
                print(f"\n📁 Guardado en: test/digital.json")
                print("🎯 TV queda en EPG para referencia visual")
            else:
                print("\n❌ No se pudieron leer canales desde EPG")
                print("🔍 El EPG puede estar vacío o desactivado")
        
        # Mantener TV en EPG
        print("\n📺 TV permanece en EPG para referencia visual")
        print("ℹ️ Presiona HOME en el control remoto para salir del EPG")
        
    except Exception as e:
        print(f"Error durante lectura de EPG: {e}")

if __name__ == "__main__":
    main()
