#!/usr/bin/env python3
"""
Script ultra rápido para escanear canales usando la IP correcta detectada
"""

import subprocess
import json
import time
import os
import sys

def get_tv_ip_smart():
    """Obtener IP de TV de manera inteligente: Cache -> ADB -> Scan"""
    
    # 1. Probar caché reciente (/tmp/fina_last_tv_ip)
    # Solo confiamos si se actualizó hace menos de 10 minutos
    try:
        if os.path.exists("/tmp/fina_last_tv_ip"):
            mtime = os.path.getmtime("/tmp/fina_last_tv_ip")
            if time.time() - mtime < 600: # 10 min
                with open("/tmp/fina_last_tv_ip", "r") as f:
                    candidate = f.read().strip()
                    if candidate and is_adb_connected(candidate):
                        return candidate
    except: pass
    
    # 2. ADB devices vivos
    try:
        res = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=2)
        connected = [l.split('\t')[0] for l in res.stdout.split('\n') if '\tdevice' in l]
        # Priorizar .10 o .11 si están
        # Pero aceptar cualquiera
        for p in ['192.168.0.10:5555', '192.168.0.11:5555']:
            base = p.split(':')[0]
            if p in connected or base in connected: return base
            
        if connected: return connected[0].split(':')[0]
    except: pass

    # 3. Fallback a lista amplia hardcoded (Rango Amplio Solicitado)
    # Generamos rango .2 a .20 para cubrir casi todo lo usual
    tv_ips = [f"192.168.0.{i}" for i in range(2, 21)]
    
    print("🔍 Buscando TV en la red (Rango amplio)...")
    for ip in tv_ips:
        # Ping rápido primero
        if ping_host(ip):
             # Intentar conectar
             try:
                 subprocess.run(['adb', 'connect', ip], capture_output=True, timeout=2)
                 if is_adb_connected(ip):
                     # Guardar cache
                     try:
                         with open("/tmp/fina_last_tv_ip", "w") as f: f.write(ip)
                     except: pass
                     return ip
             except: pass
            
    return None

def ping_host(ip):
    try:
        subprocess.run(['ping', '-c', '1', '-W', '1', ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except:
        return False

def is_adb_connected(ip):
    try:
        # Check rápido
        subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'echo', '1'], 
                      capture_output=True, timeout=2, check=True)
        return True
    except:
        return False

def input_channel_direct(ip, channel_number):
    """Ingresar canal directamente sin pausas"""
    cmd = f"input text '{channel_number}'"
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', cmd], 
                  capture_output=True, text=True, timeout=2)
    time.sleep(0.2)
    return True

def scan_ultra_fast(ip):
    """Escaneo ultra rápido desde 80.1"""
    print(f"⚡ Escaneo ULTRA RÁPIDO sobre {ip}")
    
    channels_found = {}
    channel_names = {
        '80.1': 'Somos La Plata', '80.2': 'Canal de la Ciudad', '80.3': 'Metro',
        '80.4': 'América TV', '80.5': 'Telefe', '80.6': 'TV Pública',
        '80.7': 'El Trece', '80.8': 'El Nueve', '80.9': 'Magazine',
        '81.1': 'TN', '81.2': 'La Nacion+', '81.3': 'C5N', '81.4': 'Crónica TV',
        '81.5': 'Canal 26', '81.6': 'A24', '81.7': 'Ciudad Magazine', '81.8': 'Net TV',
        '81.9': 'Bravo',
        '82.1': 'Bravo', '82.2': 'Argentina 12', '82.3': 'KZO', '82.4': 'TyC Sports',
        '82.5': 'ESPN 2', '82.6': 'ESPN', '82.7': 'ESPN 3', '82.8': 'ESPN 4',
        '82.9': 'Fox Sports Premium',
        '83.1': 'Fox Sports', '83.2': 'Fox Sports 2', '83.3': 'Fox Sports 3',
        '83.4': 'Disney Channel', '83.5': 'Nickelodeon', '83.6': 'Cartoonito',
        '83.7': 'Discovery Kids', '83.8': 'Disney Junior', '83.9': 'Paka Paka',
        '84.1': 'Paka Paka', '84.2': 'Cartoon Network', '84.3': 'Space',
        '84.4': 'Cinemax', '84.5': 'Paramount', '84.6': 'Volver', '84.7': 'Info Flow',
        '84.8': 'Cinecanal', '84.9': 'TNT',
        '85.1': 'TNT', '85.2': 'TNT Series', '85.3': 'FX', '85.4': 'Star Channel',
        '85.5': 'Sony Channel', '85.6': 'Warner Channel', '85.7': 'Universal Channel',
        '85.8': 'AXN', '85.9': 'A&E',
        '86.1': 'A&E', '86.2': 'TNT Novelas', '86.3': 'TCM', '86.4': 'AMC',
        '86.5': 'Discovery ID', '86.6': 'Comedy Central', '86.7': 'Cine Ar',
        '86.8': 'Studio Universal', '86.9': 'El Gourmet',
        '87.1': 'El Gourmet', '87.2': 'El Garage TV', '87.3': 'Discovery H&H',
        '87.4': 'Encuentro', '87.5': 'National Geographic', '87.6': 'Discovery Channel',
        '87.7': 'Animal Planet', '87.8': 'History Channel', '87.9': 'Canal A',
        '88.1': 'Canal A', '88.2': 'History 2', '88.3': 'E!', '88.4': 'Quiero Música',
        '88.5': 'MTV', '88.6': 'Telemundo', '88.7': 'TVE', '88.8': 'RAI',
        '88.9': 'Estrellas',
        '89.1': 'Estrellas', '89.2': 'DeporTV', '89.3': 'CNN en Español',
        '89.4': 'Lifetime', '89.5': 'TLC', '89.6': 'Canal Rural',
        '89.7': 'Eventos 2', '89.8': 'Eventos HD', '89.9': 'Glitz'
    }
    
    # Iniciar app de TV
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'start', '-n', 'com.tcl.tv/.TVActivity'], 
                  capture_output=True, text=True, timeout=5)
    time.sleep(2)
    
    try:
        # Escanear range
        for main in range(80, 90):
            for decimal in range(1, 10):
                channel_num = f"{main}.{decimal}"
                input_channel_direct(ip, channel_num)
                channel_name = channel_names.get(channel_num, f'Canal {channel_num}')
                channels_found[channel_name.lower()] = channel_num
                print(f"⚡ {channel_num} → {channel_name}")
                time.sleep(0.1)
            
            print(f"✅ Rango {main}.x completado\n")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Escaneo detenido")
    
    return channels_found

def main():
    print("⚡ Escaneo ULTRA RÁPIDO (Auto-IP)")
    print("=" * 50)
    
    ip = get_tv_ip_smart()
    if not ip:
        print("❌ No se encontró NINGUNA TV activa en la red (192.168.0.2-20).")
        return
    
    print(f"📡 Objetivo Fijado: {ip}")
    
    channels_found = scan_ultra_fast(ip)
    
    if channels_found:
        with open('test/digital.json', 'w', encoding='utf-8') as f:
            json.dump(channels_found, f, indent=4, ensure_ascii=False)
        print(f"\n✅ Guardados {len(channels_found)} canales.")

if __name__ == "__main__":
    main()
