#!/usr/bin/env python3
import subprocess
import time
import os
import sys

# Añadir raíz del proyecto para importar utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
try:
    from utils import speak
except ImportError:
    def speak(text, model=None):
        print(f"🗣️ {text}")
        subprocess.run(f"espeak -v es '{text}'", shell=True)

def test_francotirador():
    print("🎯 TEST DE GRABACIÓN 'FRANCOTIRADOR'")
    print("=====================================")
    print("Este test verifica si podemos grabar a Fina en Waydroid moviendo los cables de audio.")
    
    print("\n📝 PASO 1: Abre la Grabadora en Waydroid.")
    print("📝 PASO 2: Empieza a grabar AHORA.")
    print("📝 PASO 3: Presiona ENTER aquí inmediatamente después de empezar a grabar.")
    input()
    
    print("\n🔍 Buscando stream de Waydroid...")
    
    waydroid_stream_id = None
    monitor_source = "57" # Default
    mic_source = "58" # Default
    
    # 1. Detectar IDs reales
    try:
        monitor_source = subprocess.check_output("pactl list short sources | grep 'monitor' | grep -v 'waydroid' | head -n1 | cut -f1", shell=True).decode().strip()
        mic_source = subprocess.check_output("pactl list short sources | grep 'analog-stereo' | grep 'input' | head -n1 | cut -f1", shell=True).decode().strip()
        print(f"ℹ️ Monitor ID: {monitor_source} | Mic ID: {mic_source}")
    except:
        pass

    # 2. Buscar Stream
    for i in range(10):
        try:
            output = subprocess.check_output("pactl list source-outputs", shell=True).decode()
            if "Waydroid" in output:
                blocks = output.split("Salida de fuente #")
                for block in blocks:
                    if "Waydroid" in block:
                        waydroid_stream_id = block.split("\n")[0].strip()
                        break
            if waydroid_stream_id:
                break
        except:
            pass
        time.sleep(0.2)
    
    if waydroid_stream_id:
        print(f"✅ Stream detectado: #{waydroid_stream_id}")
        
        # 3. Mover a Monitor
        print(f"🔌 Moviendo cable al Monitor #{monitor_source}...")
        subprocess.run(f"pactl move-source-output {waydroid_stream_id} {monitor_source}", shell=True)
        
        # 4. Fina Habla
        print("\n🗣️ Fina hablando...")
        mensaje = "Prueba de grabación exitosa. Fina está hablando directamente a tu grabadora digital."
        speak(mensaje, None)
        time.sleep(1)
        
        # 5. Restaurar
        print(f"\n🔌 Devolviendo cable al Micrófono #{mic_source}...")
        subprocess.run(f"pactl move-source-output {waydroid_stream_id} {mic_source}", shell=True)
        print("✅ Restaurado.")
        
        print("\n🎉 PRUEBA TERMINADA.")
        print("👉 Detén la grabación en Waydroid y escúchala.")
        print("❓ ¿Se escuchó la voz de Fina?")
        
    else:
        print("❌ CRÍTICO: No se detectó ninguna grabación activa de Waydroid.")
        print("   Asegúrate de estar grabando ANTES de presionar Enter.")

if __name__ == "__main__":
    test_francotirador()
