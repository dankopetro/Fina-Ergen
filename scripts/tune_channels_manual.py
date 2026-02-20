#!/usr/bin/env python3
"""
Script mejorado para sintonizar canales uno por uno y guardarlos en digital.json
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

def tune_channel(ip, channel_number):
    """Sintonizar un canal específico"""
    print(f"🔧 Sintonizando canal {channel_number}...")
    
    # Iniciar app de TV
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'am', 'start', '-n', 'com.tcl.tv/.TVActivity'], 
                  capture_output=True, text=True, timeout=5)
    time.sleep(2)
    
    # Enviar dígitos del canal
    for digit in str(channel_number):
        if digit == '.':
            # Enviar punto decimal
            subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_NUMPAD_DOT'], 
                          capture_output=True, text=True, timeout=3)
        else:
            # Enviar número
            keycode = f'KEYCODE_{digit}'
            subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', keycode], 
                          capture_output=True, text=True, timeout=3)
        time.sleep(0.2)  # Reducido para entrada más rápida
    
    # Enviar OK para sintonizar
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_DPAD_CENTER'], 
                  capture_output=True, text=True, timeout=3)
    
    print(f"  ⏳ Esperando a que la TV sincronice la señal...")
    time.sleep(8)  # Esperar 8 segundos para que la TV sintonice y muestre la imagen
    
    # Verificar si hay señal
    return check_signal(ip, channel_number)

def check_signal(ip, channel_number, debug=False):
    """Verificar si hay señal en el canal actual usando múltiples métodos"""
    
    print(f"  🔍 Verificando señal del canal {channel_number}...")
    
    # Método 1: Análisis de dumpsys media.tv
    try:
        result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'dumpsys', 'media.tv'], 
                              capture_output=True, text=True, timeout=5)
        
        if debug:
            print(f"  📊 Analizando dumpsys media.tv...")
            # Mostrar líneas relevantes
            for line in result.stdout.splitlines():
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in ['signal', 'lock', 'frequency', 'tuned', 'strength', 'quality']):
                    print(f"    → {line.strip()}")
        
        # Buscar indicadores positivos de señal
        output = result.stdout.lower()
        positive_indicators = [
            'lock=1', 'lock=true', 'locked=true', 'locked=1',
            'signal=true', 'signal=1', 'hassignal=true',
            'tuned=true', 'tuned=1', 'istuned=true',
            'strength=' # Si hay un valor de fuerza de señal
        ]
        
        for indicator in positive_indicators:
            if indicator in output:
                print(f"  ✅ Señal detectada (indicador: {indicator})")
                return True
                
    except Exception as e:
        if debug:
            print(f"  ⚠️ Error en dumpsys: {e}")
    
    # Método 2: Verificar si hay contenido de video activo
    try:
        result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'dumpsys', 'media.player'], 
                              capture_output=True, text=True, timeout=5)
        
        if 'isPlaying=true' in result.stdout or 'state=started' in result.stdout.lower():
            print(f"  ✅ Señal detectada (video reproduciéndose)")
            return True
            
    except Exception as e:
        if debug:
            print(f"  ⚠️ Error en media.player: {e}")
    
    # Método 3: Screenshot deshabilitado (no funciona bien en esta TV)
    # Se omite para evitar falsos negativos
    
    # Confirmación manual del usuario
    print(f"  ⚠️ No se pudo detectar señal automáticamente")
    print(f"  👀 Por favor, mira la TV y verifica si hay imagen en el canal {channel_number}")
    
    while True:
        response = input(f"  ¿Hay señal en el canal {channel_number}? (s/n): ").strip().lower()
        if response in ['s', 'si', 'sí', 'y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("  Por favor responde 's' para sí o 'n' para no")

def get_channel_name(ip, channel_number):
    """Obtener nombre del canal sintonizado"""
    try:
        # Intentar obtener información del canal actual
        result = subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'dumpsys', 'activity', 'top'], 
                              capture_output=True, text=True, timeout=5)
        
        # Buscar información del canal en el dump
        lines = result.stdout.splitlines()
        for line in lines:
            if 'tv' in line.lower() or 'channel' in line.lower():
                print(f"Info canal: {line.strip()}")
        
        # Si no se puede obtener el nombre, usar uno genérico
        return f"Canal {channel_number}"
        
    except Exception as e:
        print(f"Error obteniendo nombre: {e}")
        return f"Canal {channel_number}"

def save_channel(channel_name, channel_number, filename='test/digital.json'):
    """Guardar canal en archivo JSON"""
    channels = {}
    
    # Cargar canales existentes
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                channels = json.load(f)
        except:
            channels = {}
    
    # Agregar nuevo canal
    channels[channel_name.lower()] = str(channel_number)
    
    # Guardar
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(channels, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Guardado: {channel_name} → {channel_number}")

def manual_channel_scan(ip):
    """Escaneo manual de canales"""
    print("📺 Iniciando escaneo manual de canales")
    print("Presiona Ctrl+C para detener")
    
    # Canales comunes para Argentina
    common_channels = [
        "80.1", "80.2", "80.3", "80.4", "80.5", "80.6", "80.7", "80.8",
        "81.1", "81.2", "81.3", "81.4", "81.5", "81.6", "81.7", "81.8",
        "82.1", "82.2", "82.3", "82.4", "82.5", "82.6", "82.7", "82.8",
        "83.1", "83.2", "83.3", "83.4", "83.5", "83.6", "83.7", "83.8",
        "84.1", "84.2", "84.3", "84.4", "84.5", "84.6", "84.7", "84.8",
        "85.1", "85.2", "85.3", "85.4", "85.5", "85.6", "85.7", "85.8",
        "86.1", "86.2", "86.3", "86.4", "86.5", "86.6", "86.7", "86.8",
        "87.1", "87.2", "87.3", "87.4", "87.5", "87.6", "87.7", "87.8",
        "88.1", "88.2", "88.3", "88.4", "88.5", "88.6", "88.7", "88.8",
        "89.1", "89.2", "89.3", "89.4", "89.5", "89.6", "89.7", "89.8"
    ]
    
    channels_found = 0
    
    try:
        for channel_num in common_channels:
            print(f"\n🔍 Probando canal {channel_num}...")
            
            # Sintonizar canal
            if tune_channel(ip, channel_num):
                # Hay señal, pedir nombre y guardar
                channel_name = input(f"  📝 Nombre del canal {channel_num}: ").strip()
                if not channel_name:
                    channel_name = f"Canal {channel_num}"
                
                save_channel(channel_name, channel_num)
                channels_found += 1
                
                print(f"✅ Canal {channel_num} guardado como: {channel_name}")
            else:
                print(f"❌ Canal {channel_num} sin señal")
            
            # Pequeña pausa entre canales
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Escaneo detenido por el usuario")
    
    print(f"\n📊 Resumen: {channels_found} canales encontrados y guardados")

def interactive_mode(ip):
    """Modo interactivo para sintonizar canales manualmente"""
    print("🎮 Modo interactivo de sintonización")
    print("Ingresa números de canal para sintonizar (ej: 80.5, 13.1)")
    print("Escribe 'salir' para terminar")
    
    while True:
        try:
            channel_input = input("\n📺 Canal a sintonizar: ").strip()
            
            if channel_input.lower() == 'salir':
                break
            
            if not channel_input:
                continue
            
            # Validar formato del canal
            if re.match(r'^\d+(\.\d+)?$', channel_input):
                if tune_channel(ip, channel_input):
                    channel_name = input(f"✅ Señal encontrada en {channel_input}. Nombre del canal: ").strip()
                    if not channel_name:
                        channel_name = f"Canal {channel_input}"
                    
                    save_channel(channel_name, channel_input)
                    print(f"✅ Guardado: {channel_name} → {channel_input}")
                else:
                    print(f"❌ No hay señal en el canal {channel_input}")
            else:
                print("❌ Formato inválido. Usa formato como 80.5 o 13.1")
                
        except KeyboardInterrupt:
            break
    
    print("👋 Modo interactivo terminado")

def main():
    """Función principal"""
    print("📺 Sintonizador Manual de Canales TCL")
    print("=" * 50)
    
    ip = get_tv_ip()
    if not ip:
        print("❌ No hay TV conectada vía ADB")
        return
    
    print(f"📡 TV conectada: {ip}")
    
    print("\n🎯 Opciones:")
    print("1. Escaneo automático de canales comunes")
    print("2. Modo interactivo (ingresar canales manualmente)")
    print("3. Ver canales guardados")
    
    try:
        option = input("\nElige una opción (1-3): ").strip()
        
        if option == "1":
            manual_channel_scan(ip)
        elif option == "2":
            interactive_mode(ip)
        elif option == "3":
            filename = 'test/digital.json'
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    channels = json.load(f)
                print(f"\n📋 Canales guardados ({len(channels)}):")
                for name, number in channels.items():
                    print(f"  {name}: {number}")
            else:
                print("❌ No hay canales guardados")
        else:
            print("❌ Opción inválida")
            
    except KeyboardInterrupt:
        print("\n👋 Programa terminado")

if __name__ == "__main__":
    main()
