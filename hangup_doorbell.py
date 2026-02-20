#!/usr/bin/env python3
"""
Script para colgar el timbre desde Fina principal.
Uso: python3 hangup_doorbell.py
"""
import subprocess
import sys

def hangup_doorbell():
    """Envía comando de colgar al cerebro Phoenix o ejecuta ADB directamente"""
    
    # Coordenadas del botón de colgar
    BTN_HANGUP_X, BTN_HANGUP_Y = 225, 710
    
    try:
        # Opción 1: ADB directo (más confiable si Phoenix no está corriendo)
        print("Colgando timbre vía ADB...")
        subprocess.run(["adb", "shell", "input", "tap", str(BTN_HANGUP_X), str(BTN_HANGUP_Y)], 
                      check=True, timeout=5)
        
        # Cerrar ventana de Scrcpy
        subprocess.run("pkill -f 'scrcpy.*Fina Doorbell'", shell=True, stderr=subprocess.DEVNULL)
        
        # Cerrar servidor de streaming
        subprocess.run("pkill -f 'streamer.py'", shell=True, stderr=subprocess.DEVNULL)
        
        print("✅ Timbre colgado exitosamente")
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Error: ADB no responde (timeout)")
        return False
    except FileNotFoundError:
        print("❌ Error: ADB no encontrado. ¿Está instalado?")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = hangup_doorbell()
    sys.exit(0 if success else 1)
