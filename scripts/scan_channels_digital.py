#!/usr/bin/env python3
"""
Script de escaneo de canales para TCL TV
Usa múltiples métodos para obtener canales digitales
"""

import subprocess
import json
import time
import re
import os

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

def scan_channels_digital(ip):
    """Escaneo completo de canales digitales"""
    print(f"🔍 Escaneando canales en TV {ip}...")
    
    # Paso 1: Iniciar app de TV
    print("1. Iniciando app de TV...")
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'start', '-n', 'com.tcl.tv/.TVActivity'], 
                  capture_output=True, text=True, timeout=5)
    time.sleep(2)
    
    # Paso 2: Enviar secuencia de sintonización
    print("2. Enviando secuencia de sintonización...")
    
    # Abrir menú de canales
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_MENU'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(1)
    
    # Navegar a configuración
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                  capture_output=True, text=True, timeout=3)
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(2)
    
    # Buscar opción de sintonización
    for _ in range(5):
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN'], 
                      capture_output=True, text=True, timeout=3)
        time.sleep(0.5)
    
    # Seleccionar sintonización
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(3)
    
    # Iniciar escaneo automático
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                  capture_output=True, text=True, timeout=3)
    
    print("3. Esperando proceso de sintonización (30 segundos)...")
    time.sleep(30)
    
    # Paso 3: Verificar canales encontrados
    print("4. Verificando canales encontrados...")
    
    # Volver a la app principal
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_HOME'], 
                  capture_output=True, text=True, timeout=3)
    time.sleep(2)
    
    # Consultar canales via content provider
    result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'content', 'query', 
                             '--uri', 'content://android.media.tv/channel', 
                             '--projection', 'display_number:display_name'], 
                          capture_output=True, text=True, timeout=10)
    
    channels = {}
    if result.stdout.strip() and 'No result found' not in result.stdout:
        print("✅ Canales encontrados!")
        
        for line in result.stdout.splitlines():
            num_match = re.search(r'display_number=([^,]+)', line)
            name_match = re.search(r'display_name=([^,]+)', line)
            
            if num_match and name_match:
                number = num_match.group(1).strip()
                name = name_match.group(1).strip()
                key = name.lower()
                channels[key] = number
                print(f"  {name}: {number}")
    else:
        print("❌ No se encontraron canales")
        
        # Método alternativo: intentar con diferentes URIs
        alternative_uris = [
            'content://com.tcl.tvinput.provider/channel',
            'content://com.tcl.tvinput/tv_channel',
            'content://android.media.tv/tv_channel'
        ]
        
        for uri in alternative_uris:
            result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'content', 'query', 
                                   '--uri', uri], 
                                  capture_output=True, text=True, timeout=5)
            if result.stdout.strip() and 'No result found' not in result.stdout:
                print(f"✅ Canales encontrados con URI alternativo: {uri}")
                # Parsear resultado alternativo aquí
                break
    
    return channels

def save_channels(channels, filename='test/digital.json'):
    """Guardar canales en archivo JSON"""
    temp_test_dir = os.path.expanduser("~/.config/Fina/temp/test")
    os.makedirs(temp_test_dir, exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(channels, f, indent=4, ensure_ascii=False)
    
    print(f"📁 Guardados {len(channels)} canales en {filename}")

def main():
    """Función principal"""
    print("📺 Escaneo de Canales Digitales TCL TV")
    print("=" * 50)
    
    ip = get_tv_ip()
    if not ip:
        print("❌ No hay TV conectada vía ADB")
        return
    
    print(f"📡 TV conectada: {ip}")
    
    # Verificar conexión de señal
    print("\n🔌 Verificando conexión de señal...")
    result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'dumpsys', 'tv_input'], 
                          capture_output=True, text=True, timeout=10)
    
    if 'cable_connection_status=0' in result.stdout:
        print("⚠️  ADVERTENCIA: No se detecta conexión de antena/cable")
        print("   Por favor conecte una señal de TV antes de continuar")
        
        response = input("¿Desea continuar de todos modos? (s/N): ")
        if response.lower() != 's':
            return
    
    # Realizar escaneo
    channels = scan_channels_digital(ip)
    
    if channels:
        save_channels(channels)
        print(f"\n✅ Escaneo completado exitosamente")
        print(f"   Total de canales: {len(channels)}")
    else:
        print(f"\n❌ No se encontraron canales")
        print(f"   Recomendaciones:")
        print(f"   1. Conecte antena o cable de TV")
        print(f"   2. Use el control remoto para sintonizar primero")
        print(f"   3. Verifique que la TV tenga sintonizador activado")

if __name__ == "__main__":
    main()
