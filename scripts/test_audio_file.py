#!/usr/bin/env python3
"""
Script de prueba usando archivo de audio temporal
Este enfoque graba el audio de Fina y lo reproduce en Waydroid vía ADB
"""

import subprocess
import time
import sys
import os
import tempfile

# Añadir raíz del proyecto para importar utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from utils import speak

def test_audio_via_file():
    print("🎙️ TEST DE AUDIO PC -> WAYDROID (VÍA ARCHIVO)")
    print("=" * 50)
    
    # Crear archivo temporal
    temp_audio = tempfile.mktemp(suffix=".wav")
    
    try:
        # 1. Generar el audio de Fina
        print("\n🗣️ Generando mensaje de Fina...")
        mensaje = "Hola. Esta es una prueba del sistema de audio. Si escuchas esto, el sistema funciona correctamente."
        
        # Usar espeak para generar el archivo WAV directamente
        subprocess.run([
            "espeak", "-v", "es", "-s", "150", "-w", temp_audio, mensaje
        ])
        
        print(f"✅ Audio generado: {temp_audio}")
        
        # 2. Copiar el archivo a Waydroid
        print("\n📤 Copiando audio a Waydroid...")
        subprocess.run([
            "adb", "-s", "192.168.240.112:5555", 
            "push", temp_audio, "/sdcard/Download/test_fina.wav"
        ])
        
        print("✅ Archivo copiado a /sdcard/Download/test_fina.wav")
        
        # 3. Reproducir el archivo en Waydroid
        print("\n🔊 Reproduciendo en Waydroid...")
        print("   (Deberías escucharlo en los altavoces de la PC)")
        subprocess.run([
            "adb", "-s", "192.168.240.112:5555",
            "shell", "am", "start", "-a", "android.intent.action.VIEW",
            "-d", "file:///sdcard/Download/test_fina.wav",
            "-t", "audio/wav"
        ])
        
        print("\n✅ PRUEBA COMPLETADA")
        print("\n📝 Si escuchaste el audio, el sistema básico funciona.")
        print("   Ahora necesitamos encontrar una forma de enrutar el audio en tiempo real.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Limpiar
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
            print(f"\n🧹 Archivo temporal eliminado")

if __name__ == "__main__":
    test_audio_via_file()
