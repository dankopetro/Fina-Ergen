#!/usr/bin/env python3
import subprocess
import time
import sys

print("🕵️‍♂️ MONITOR DE NOTIFICACIONES WAYDROID (Diagnóstico)")
print("-----------------------------------------------------")
print("Escaneando cada 2 segundos...")

while True:
    try:
        # Ejecutar dumpsys crudo
        # Usamos sudo porque descubrimos que se necesita
        cmd = "sudo waydroid shell dumpsys notification"
        out = subprocess.check_output(cmd, shell=True).decode()
        
        # Filtrar para mostrar algo legible
        # Buscamos bloques de notificaciones
        lines = out.split('\n')
        active_pkgs = []
        
        for line in lines:
            if "pkg=" in line:
                # Extraer nombre del paquete
                pkg = line.strip().split('pkg=')[1].split(' ')[0]
                active_pkgs.append(pkg)
                
            if "tickerText=" in line:
                 print(f"   📝 Ticker: {line.strip()}")

        if active_pkgs:
            print(f"[{time.strftime('%H:%M:%S')}] Notificaciones Activas: {list(set(active_pkgs))}")
            
            # Prueba de detección de TUYA
            if "com.tuya.smart" in str(active_pkgs) or "tuya" in str(active_pkgs):
                print("   ✅ ¡ALERTA! Tuya detectado (El script dispararía aquí)")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Sin notificaciones...")

    except subprocess.CalledProcessError:
        print("❌ Error ejecutando waydroid shell. ¿Está Waydroid corriendo?")
    except Exception as e:
        print(f"❌ Error: {e}")
        
    time.sleep(2)
