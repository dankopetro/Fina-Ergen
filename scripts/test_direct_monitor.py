#!/usr/bin/env python3
"""
Script de prueba que redirige la entrada de Waydroid al monitor
"""

import subprocess
import time
import sys
import os

# Añadir raíz del proyecto para importar utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from utils import speak

def test_direct_monitor():
    print("🎙️ TEST DE AUDIO DIRECTO (Monitor -> Waydroid)")
    print("=" * 50)
    print("\n📝 INSTRUCCIONES:")
    print("1. Abre la grabadora de sonidos en Waydroid")
    print("2. Presiona GRABAR en la app")
    print("3. Presiona ENTER aquí para continuar...")
    input()
    
    original_source = None
    
    try:
        print("\n🔧 Obteniendo configuración actual...")
        
        # Obtener la fuente predeterminada actual
        try:
            original_source = subprocess.check_output(
                "pactl get-default-source",
                shell=True
            ).decode().strip()
            print(f"📌 Fuente original: {original_source}")
        except:
            print("⚠️ No se pudo obtener fuente original")
        
        # Obtener el monitor
        monitor_source = subprocess.check_output(
            "pactl list short sources | grep 'monitor' | grep -v 'waydroid' | head -n1 | cut -f2",
            shell=True
        ).decode().strip()
        
        print(f"📡 Monitor: {monitor_source}")
        
        # Cambiar la fuente predeterminada al monitor
        print("\n🔄 Cambiando fuente de entrada al monitor...")
        subprocess.run(["pactl", "set-default-source", monitor_source])
        print("✅ Fuente cambiada")
        
        # Esperar un momento
        print("\n⏳ Esperando 2 segundos...")
        time.sleep(2)
        
        # Fina habla
        print("\n🗣️ Fina está hablando...")
        mensaje = "Hola. Esta es una prueba del sistema de audio directo. Si escuchas esto en la grabadora, el sistema funciona perfectamente."
        speak(mensaje, None)
        
        # Mantener activo un poco más
        print("\n⏳ Esperando 3 segundos más...")
        time.sleep(3)
        
        print("\n✅ PRUEBA COMPLETADA")
        print("\n📝 Ahora detén la grabación en Waydroid y reproduce el audio.")
        print("   Si escuchas el mensaje de Fina, ¡el sistema funciona! 🎉")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Restaurar fuente original
        if original_source:
            print(f"\n🔄 Restaurando fuente original: {original_source}")
            try:
                subprocess.run(["pactl", "set-default-source", original_source])
                print("✅ Fuente restaurada")
            except:
                print("⚠️ No se pudo restaurar automáticamente")

if __name__ == "__main__":
    test_direct_monitor()
