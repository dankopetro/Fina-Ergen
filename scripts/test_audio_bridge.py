#!/usr/bin/env python3
"""
Script de prueba para verificar el puente de audio PC -> Waydroid
Uso: Abre la grabadora de sonidos en Waydroid y ejecuta este script
"""

import subprocess
import time
import sys
import os

# Añadir raíz del proyecto para importar utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from utils import speak

def test_audio_bridge():
    print("🎙️ TEST DE PUENTE DE AUDIO PC -> WAYDROID")
    print("=" * 50)
    print("\n📝 INSTRUCCIONES:")
    print("1. Abre la grabadora de sonidos en Waydroid")
    print("2. Presiona GRABAR en la app")
    print("3. Presiona ENTER aquí para continuar...")
    input()
    
    loopback_module = None
    
    try:
        print("\n🔧 Configurando puente de audio...")
        
        # Obtener el monitor de salida (lo que se escucha)
        monitor_source = subprocess.check_output(
            "pactl list short sources | grep 'monitor' | grep -v 'waydroid' | head -n1 | cut -f2",
            shell=True
        ).decode().strip()
        
        print(f"📡 Monitor: {monitor_source}")
        
        # Crear módulo loopback de PulseAudio
        # Esto crea un puente permanente entre el monitor y la entrada predeterminada
        print("\n🌉 Creando módulo loopback...")
        result = subprocess.check_output(
            f"pactl load-module module-loopback source={monitor_source} latency_msec=1",
            shell=True
        ).decode().strip()
        
        loopback_module = result
        print(f"✅ Módulo loopback cargado: #{loopback_module}")
        
        # Esperar un momento antes de hablar
        print("\n⏳ Esperando 2 segundos antes de hablar...")
        time.sleep(2)
        
        # Fina habla
        print("\n🗣️ Fina está hablando...")
        mensaje = "Hola. Esta es una prueba del puente de audio. Si escuchas esto en la grabadora de Waydroid, el sistema funciona correctamente."
        speak(mensaje, None)
        
        # Mantener el puente activo un poco más
        print("\n⏳ Manteniendo puente activo por 3 segundos más...")
        time.sleep(3)
        
        print("\n✅ PRUEBA COMPLETADA")
        print("\n📝 Ahora detén la grabación en Waydroid y reproduce el audio.")
        print("   Si escuchas el mensaje de Fina, ¡el puente funciona! 🎉")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Limpiar
        if loopback_module:
            print("\n🧹 Descargando módulo loopback...")
            try:
                subprocess.run(f"pactl unload-module {loopback_module}", shell=True)
                print("✅ Módulo descargado")
            except:
                print("⚠️ No se pudo descargar el módulo automáticamente")

if __name__ == "__main__":
    test_audio_bridge()
