#!/usr/bin/env python3
"""
Script para buscar apps EPG en la TV TCL
"""

import subprocess
import json
import time

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

def find_epg_apps(ip):
    """Buscar apps relacionadas con EPG"""
    print('🔍 Buscando apps EPG en la TV TCL')
    
    # Listar todas las apps
    result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'pm', 'list', 'packages'], 
                          capture_output=True, text=True, timeout=10)
    
    apps = result.stdout.splitlines()
    epg_apps = []
    
    for app in apps:
        pkg = app.replace('package:', '').strip()
        if any(keyword in pkg.lower() for keyword in ['epg', 'guide', 'program', 'channel']):
            epg_apps.append(pkg)
    
    if epg_apps:
        print('✅ Apps EPG encontradas:')
        for app in epg_apps:
            print(f'   {app}')
        return epg_apps
    else:
        print('❌ No se encontraron apps EPG')
        return []

def launch_epg_app(ip, package):
    """Intentar lanzar app EPG"""
    try:
        print(f"🚀 Intentando lanzar: {package}")
        
        # Intentar launcher genérico
        result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'start', '-n', f'{package}/.MainActivity'], 
                              capture_output=True, text=True, timeout=5)
        
        time.sleep(3)
        
        # Verificar si se lanzó
        result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'dumpsys', 'activity', 'top'], 
                              capture_output=True, text=True, timeout=5)
        
        if package in result.stdout:
            print(f"✅ App {package} lanzada exitosamente")
            return True
        else:
            print(f"❌ No se pudo lanzar {package}")
            return False
            
    except Exception as e:
        print(f"Error lanzando {package}: {e}")
        return False

def check_epg_data(ip):
    """Verificar si hay datos EPG después de lanzar apps"""
    print("🔍 Verificando datos EPG...")
    
    # Esperar a que cargue
    time.sleep(5)
    
    # Verificar content providers
    epg_queries = [
        'content query --uri content://android.media.tv/channel',
        'content query --uri content://android.media.tv/program',
        'content query --uri content://com.tcl.tvinput.provider/channel'
    ]
    
    for query in epg_queries:
        try:
            cmd = ['adb', '-s', f'{ip}:5555', 'shell'] + query.split()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.stdout.strip() and 'No result found' not in result.stdout:
                print(f"✅ Datos EPG encontrados con: {query}")
                return result.stdout
                
        except Exception as e:
            print(f"Error con query: {e}")
    
    return None

def extract_channels_from_epg(epg_data):
    """Extraer canales desde datos EPG"""
    import re
    
    channels = {}
    lines = epg_data.splitlines()
    
    for line in lines:
        # Buscar display_number y display_name
        num_match = re.search(r'display_number=([^,]+)', line)
        name_match = re.search(r'display_name=([^,]+)', line)
        
        if num_match and name_match:
            number = num_match.group(1).strip()
            name = name_match.group(1).strip()
            key = name.lower()
            channels[key] = number
    
    return channels

def main():
    """Función principal"""
    print("📺 Búsqueda de Apps EPG en TCL")
    print("=" * 50)
    
    ip = get_tv_ip()
    if not ip:
        print("❌ No hay TV conectada vía ADB")
        return
    
    print(f"📡 TV conectada: {ip}")
    
    # Buscar apps EPG
    epg_apps = find_epg_apps(ip)
    
    if not epg_apps:
        print("🔍 Buscando apps con keywords alternativas...")
        
        # Búsqueda más amplia
        result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'pm', 'list', 'packages'], 
                              capture_output=True, text=True, timeout=10)
        
        apps = result.stdout.splitlines()
        tv_apps = []
        
        for app in apps:
            pkg = app.replace('package:', '').strip()
            if any(keyword in pkg.lower() for keyword in ['tv', 'tuner', 'media', 'broadcast']):
                tv_apps.append(pkg)
        
        print(f"✅ Apps TV encontradas: {len(tv_apps)}")
        
        # Intentar lanzar algunas apps TV para ver si tienen EPG
        for app in tv_apps[:5]:  # Limitar a 5 para no tomar mucho tiempo
            if launch_epg_app(ip, app):
                # Verificar si hay datos EPG
                epg_data = check_epg_data(ip)
                if epg_data:
                    channels = extract_channels_from_epg(epg_data)
                    if channels:
                        # Guardar canales
                        with open('test/digital.json', 'w', encoding='utf-8') as f:
                            json.dump(channels, f, indent=4, ensure_ascii=False)
                        
                        print(f"✅ Éxito: {len(channels)} canales extraídos desde EPG")
                        print("📋 Canales encontrados:")
                        for i, (name, number) in enumerate(list(channels.items())[:5]):
                            print(f"  {name}: {number}")
                        if len(channels) > 5:
                            print(f"  ... y {len(channels) - 5} más")
                        return
                
                # Volver al inicio
                subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_HOME'], 
                              capture_output=True, text=True, timeout=3)
                time.sleep(2)
    
    print("\n📋 Resumen de búsqueda EPG:")
    print("❌ No se encontraron apps EPG funcionales")
    print("📁 Recomendación: Usar escaneo rápido de canales")
    print("🔍 La TV puede necesitar configuración manual de EPG")

if __name__ == "__main__":
    main()
