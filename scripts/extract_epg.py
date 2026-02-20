#!/usr/bin/env python3
"""
Script para extraer lista de canales desde EPG (Electronic Program Guide)
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

def extract_from_epg(ip):
    """Extraer canales desde EPG"""
    print('🔍 Extrayendo canales desde EPG...')
    
    # Queries de EPG para probar
    epg_queries = [
        ('EPG Programs', 'content query --uri content://android.media.tv/program --projection channel_id:title'),
        ('EPG Preview Programs', 'content query --uri content://android.media.tv/preview_program --projection channel_id:title'),
        ('EPG Watched Programs', 'content query --uri content://android.media.tv/watched_program --projection channel_id:title'),
        ('EPG Channels', 'content query --uri content://android.media.tv/channel --projection display_name:display_number'),
        ('TCL EPG Programs', 'content query --uri content://com.tcl.tvinput.provider/program --projection channel_id:title'),
        ('TCL EPG Channels', 'content query --uri content://com.tcl.tvinput.provider/channel --projection display_name:display_number')
    ]
    
    for name, query in epg_queries:
        try:
            print(f"   Probando: {name}")
            cmd = ['adb', '-s', f'{ip}:5555', 'shell'] + query.split()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.stdout.strip() and 'No result found' not in result.stdout:
                print(f"✅ Datos encontrados: {name}")
                
                # Parsear canales únicos
                channels = {}
                lines = result.stdout.splitlines()
                
                for line in lines:
                    # Buscar channel_id y display_name/title
                    channel_match = re.search(r'channel_id=([^,\s]+)', line)
                    name_match = re.search(r'title=([^,\s]+)', line) or re.search(r'display_name=([^,\s]+)', line)
                    number_match = re.search(r'display_number=([^,\s]+)', line)
                    
                    if channel_match and name_match:
                        channel_id = channel_match.group(1).strip()
                        channel_name = name_match.group(1).strip().strip('"')
                        
                        # Si hay número de canal, usarlo
                        if number_match:
                            channel_num = number_match.group(1).strip()
                        else:
                            # Usar channel_id como número
                            channel_num = channel_id
                        
                        channels[channel_name.lower()] = channel_num
                
                if channels:
                    print(f"   {len(channels)} canales extraídos")
                    return channels
                    
        except Exception as e:
            print(f"   Error: {e}")
    
    return None

def extract_from_database(ip):
    """Extraer desde base de datos de EPG"""
    print('🗄️ Buscando base de datos EPG...')
    
    db_paths = [
        '/data/data/com.android.providers.tv/databases/tv.db',
        '/data/data/com.tcl.tv/databases/epg.db',
        '/data/data/com.tcl.tvinput/databases/epg.db',
        '/data/data/com.tcl.tv/databases/channels.db'
    ]
    
    for db_path in db_paths:
        try:
            # Verificar si existe
            result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'test', '-f', db_path], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print(f"✅ Base encontrada: {db_path}")
                
                # Copiar a ubicación accesible
                subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'cp', db_path, '/sdcard/epg_data.db'], 
                              capture_output=True, text=True, timeout=5)
                
                # Listar tablas
                result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'sqlite3', '/sdcard/epg_data.db', '.tables'], 
                                      capture_output=True, text=True, timeout=10)
                
                if result.stdout.strip():
                    tables = result.stdout.strip().split()
                    channel_tables = [t for t in tables if 'channel' in t.lower()]
                    
                    if channel_tables:
                        print(f"   Tablas de canales: {channel_tables}")
                        
                        # Extraer datos
                        table = channel_tables[0]
                        result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'sqlite3', '/sdcard/epg_data.db', f'SELECT * FROM {table} LIMIT 20;'], 
                                              capture_output=True, text=True, timeout=10)
                        
                        if result.stdout.strip():
                            channels = parse_database_output(result.stdout)
                            if channels:
                                return channels
                                
        except Exception as e:
            print(f"   Error: {e}")
    
    return None

def parse_database_output(output):
    """Parsear salida de base de datos"""
    channels = {}
    lines = output.splitlines()
    
    for line in lines[1:]:  # Saltar encabezado
        parts = line.split('|')
        if len(parts) >= 2:
            # Buscar nombre y número
            for i, part in enumerate(parts):
                if part and part != 'NULL':
                    if re.match(r'^\d+(\.\d+)?$', part):
                        channel_num = part
                        # Buscar nombre en otras columnas
                        for j, other_part in enumerate(parts):
                            if j != i and other_part and other_part != 'NULL' and len(other_part) > 2:
                                channel_name = other_part.strip('"')
                                channels[channel_name.lower()] = channel_num
                                break
                        break
    
    return channels

def force_epg_update(ip):
    """Forzar actualización de EPG"""
    print('🔄 Forzando actualización de EPG...')
    
    epg_intents = [
        'android.media.tv.ACTION_INITIALIZE_PROGRAMS',
        'android.media.tv.ACTION_UPDATE_CHANNEL_LIST',
        'android.media.tv.ACTION_REQUEST_CHANNEL_BROWSABLE',
        'com.tcl.tvinput.action.UPDATE_EPG'
    ]
    
    for intent in epg_intents:
        try:
            subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'broadcast', '-a', intent], 
                          capture_output=True, text=True, timeout=5)
            print(f"   Enviado: {intent}")
            time.sleep(1)
        except Exception as e:
            print(f"   Error: {e}")

def main():
    """Función principal"""
    print("📺 Extracción de Canales desde EPG")
    print("=" * 50)
    
    ip = get_tv_ip()
    if not ip:
        print("❌ No hay TV conectada vía ADB")
        return
    
    print(f"📡 TV conectada: {ip}")
    
    channels = None
    
    # Método 1: Extraer desde EPG
    channels = extract_from_epg(ip)
    
    if not channels:
        # Método 2: Extraer desde base de datos
        channels = extract_from_database(ip)
    
    if not channels:
        # Método 3: Forzar actualización y reintentar
        force_epg_update(ip)
        print("⏳ Esperando actualización (10 segundos)...")
        time.sleep(10)
        
        channels = extract_from_epg(ip)
    
    # Guardar resultados
    if channels:
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
        print("   Posibles causas:")
        print("   - EPG no activo en la TV")
        print("   - Sin señal de antena/cable")
        print("   - Formato EPG propietario")

if __name__ == "__main__":
    main()
