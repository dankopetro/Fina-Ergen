#!/usr/bin/env python3
"""
Script de prueba usando snd-aloop (cable de audio virtual)
Este es el método que REALMENTE funciona con Waydroid
"""

import subprocess
import time
import sys
import os

# Añadir raíz del proyecto para importar utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from utils import speak

def test_with_loopback_device():
    print("🎙️ TEST CON SND-ALOOP (Cable de Audio Virtual)")
    print("=" * 50)
    
    try:
        # 1. Obtener los dispositivos loopback
        print("\n🔍 Buscando dispositivos loopback...")
        
        loopback_output = subprocess.check_output(
            "pactl list short sinks | grep 'snd_aloop' | head -n1 | cut -f2",
            shell=True
        ).decode().strip()
        
        loopback_input = subprocess.check_output(
            "pactl list short sources | grep 'snd_aloop' | grep 'input' | head -n1 | cut -f2",
            shell=True
        ).decode().strip()
        
        print(f"📤 Loopback Output: {loopback_output}")
        print(f"📥 Loopback Input: {loopback_input}")
        
        # 2. Configurar Waydroid para usar el loopback input
        print("\n🔧 Configurando Waydroid para usar loopback...")
        subprocess.run(["pactl", "set-default-source", loopback_input])
        print("✅ Fuente configurada")
        
        print("\n📝 INSTRUCCIONES:")
        print("1. Abre la grabadora de sonidos en Waydroid")
        print("2. Presiona GRABAR en la app")
        print("3. Presiona ENTER aquí para continuar...")
        input()
        
        # 3. Redirigir la salida de audio al loopback
        print("\n🗣️ Fina hablará a través del cable virtual...")
        
        # Guardar el sink predeterminado actual
        try:
            original_sink = subprocess.check_output(
                "pactl get-default-sink",
                shell=True
            ).decode().strip()
        except:
            original_sink = None
        
        # Cambiar el sink predeterminado al loopback
        subprocess.run(["pactl", "set-default-sink", loopback_output])
        
        # Ahora cuando Fina hable, irá al loopback
        mensaje = "Hola. Esta es una prueba usando el cable de audio virtual. Si escuchas esto, el sistema funciona perfectamente."
        speak(mensaje, None)
        
        # Esperar a que termine de hablar
        time.sleep(2)
        
        # Restaurar sink original
        if original_sink:
            subprocess.run(["pactl", "set-default-sink", original_sink])
        
        print("\n✅ PRUEBA COMPLETADA")
        print("\n📝 Detén la grabación en Waydroid y reproduce el audio.")
        print("   Si escuchas el mensaje, ¡FUNCIONA! 🎉")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Restaurar fuente predeterminada
        print("\n🔄 Restaurando fuente predeterminada...")
        try:
            mic_input = subprocess.check_output(
                "pactl list short sources | grep 'analog-stereo' | grep 'input' | grep -v 'snd_aloop' | head -n1 | cut -f2",
                shell=True
            ).decode().strip()
            subprocess.run(["pactl", "set-default-source", mic_input])
            print("✅ Fuente restaurada")
        except:
            pass

if __name__ == "__main__":
    test_with_loopback_device()
