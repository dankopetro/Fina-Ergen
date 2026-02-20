#!/usr/bin/env python3
"""
Script rápido para escanear canales desde 80.1 ascendiendo de 0.1
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

def tune_channel_fast(ip, channel_number):
    """Sintonizar canal rápidamente"""
    print(f"🔧 {channel_number}", end="", flush=True)
    
    # Enviar dígitos del canal directamente
    for digit in str(channel_number):
        if digit == '.':
            subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_NUMPAD_DOT'], 
                          capture_output=True, text=True, timeout=2)
        else:
            keycode = f'KEYCODE_{digit}'
            subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', keycode], 
                          capture_output=True, text=True, timeout=2)
        time.sleep(0.1)
    
    # Enviar OK
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                  capture_output=True, text=True, timeout=2)
    time.sleep(1.5)  # Esperar mínimo para sintonizar
    
    return True

def get_channel_name_simple(ip, channel_number):
    """Obtener nombre simple del canal"""
    # Nombres predefinidos para canales comunes
    channel_names = {
        '80.1': 'Somos La Plata',
        '80.2': 'Canal de la Ciudad', 
        '80.3': 'Metro',
        '80.4': 'América TV',
        '80.5': 'Telefe',
        '80.6': 'TV Pública',
        '80.7': 'El Trece',
        '80.8': 'El Nueve',
        '81.1': 'TN',
        '81.2': 'La Nacion+',
        '81.3': 'C5N',
        '81.4': 'Crónica TV',
        '81.5': 'Canal 26',
        '81.6': 'A24',
        '81.7': 'Ciudad Magazine',
        '81.8': 'Net TV',
        '82.1': 'Bravo',
        '82.2': 'Argentina 12',
        '82.3': 'KZO',
        '82.4': 'TyC Sports',
        '82.5': 'ESPN 2',
        '82.6': 'ESPN',
        '82.7': 'ESPN 3',
        '82.8': 'ESPN 4',
        '83.1': 'Fox Sports',
        '83.2': 'Fox Sports 2',
        '83.3': 'Fox Sports 3',
        '83.4': 'Disney Channel',
        '83.5': 'Nickelodeon',
        '83.6': 'Cartoonito',
        '83.7': 'Discovery Kids',
        '83.8': 'Disney Junior',
        '84.1': 'Paka Paka',
        '84.2': 'Cartoon Network',
        '84.3': 'Space',
        '84.4': 'Cinemax',
        '84.5': 'Paramount',
        '84.6': 'Volver',
        '84.7': 'Info Flow',
        '84.8': 'Cinecanal',
        '85.1': 'TNT',
        '85.2': 'TNT Series',
        '85.3': 'FX',
        '85.4': 'Star Channel',
        '85.5': 'Sony Channel',
        '85.6': 'Warner Channel',
        '85.7': 'Universal Channel',
        '85.8': 'AXN',
        '86.1': 'A&E',
        '86.2': 'TNT Novelas',
        '86.3': 'TCM',
        '86.4': 'AMC',
        '86.5': 'Discovery ID',
        '86.6': 'Comedy Central',
        '86.7': 'Cine Ar',
        '86.8': 'Studio Universal',
        '87.1': 'El Gourmet',
        '87.2': 'El Garage TV',
        '87.3': 'Discovery H&H',
        '87.4': 'Encuentro',
        '87.5': 'National Geographic',
        '87.6': 'Discovery Channel',
        '87.7': 'Animal Planet',
        '87.8': 'History Channel',
        '88.1': 'Canal A',
        '88.2': 'History 2',
        '88.3': 'E!',
        '88.4': 'Quiero Música',
        '88.5': 'MTV',
        '88.6': 'Telemundo',
        '88.7': 'TVE',
        '88.8': 'RAI',
        '89.1': 'Estrellas',
        '89.2': 'DeporTV',
        '89.3': 'CNN en Español',
        '89.4': 'Lifetime',
        '89.5': 'TLC',
        '89.6': 'Canal Rural',
        '89.7': 'Eventos 2',
        '89.8': 'Eventos HD'
    }
    
    return channel_names.get(channel_number, f'Canal {channel_number}')

def scan_channels_fast(ip):
    """Escaneo rápido desde 80.1 ascendiendo"""
    print("🚀 Escaneo rápido de canales (80.1 → 99.9)")
    print("   Presiona Ctrl+C para detener\n")
    
    channels_found = {}
    
    # Iniciar app de TV una vez
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'start', '-n', 'com.tcl.tv/.TVActivity'], 
                  capture_output=True, text=True, timeout=5)
    time.sleep(2)
    
    try:
        # Escanear desde 80.1 hasta 99.9
        for main in range(80, 100):
            for decimal in range(1, 10):
                channel_num = f"{main}.{decimal}"
                
                # Sintonizar canal
                if tune_channel_fast(ip, channel_num):
                    # Obtener nombre y guardar
                    channel_name = get_channel_name_simple(ip, channel_num)
                    channels_found[channel_name.lower()] = channel_num
                    print(f" ✅ {channel_name}")
                else:
                    print(" ❌", end="", flush=True)
                
                # Pequeña pausa entre canales
                time.sleep(0.3)
            
            print(f"\n--- Finalizado rango {main}.x ---\n")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Escaneo detenido")
    
    return channels_found

def main():
    """Función principal"""
    print("📺 Escaneo Rápido de Canales TCL")
    print("=" * 40)
    
    ip = get_tv_ip()
    if not ip:
        print("❌ No hay TV conectada vía ADB")
        return
    
    print(f"📡 TV conectada: {ip}")
    
    # Escanear canales
    channels_found = scan_channels_fast(ip)
    
    # Guardar resultados
    if channels_found:
        with open('test/digital.json', 'w', encoding='utf-8') as f:
            json.dump(channels_found, f, indent=4, ensure_ascii=False)
        
        print(f"\n✅ Guardados {len(channels_found)} canales en test/digital.json")
        print("\n📋 Primeros 10 canales encontrados:")
        for i, (name, number) in enumerate(list(channels_found.items())[:10]):
            print(f"  {name}: {number}")
        if len(channels_found) > 10:
            print(f"  ... y {len(channels_found) - 10} más")
    else:
        print("\n❌ No se encontraron canales")

if __name__ == "__main__":
    main()
