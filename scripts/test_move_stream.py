#!/usr/bin/env python3
"""
Script de prueba: FORZAR movimiento del stream de audio
Busca la aplicación que está grabando y le cambia el enchufe a la fuerza
"""

import subprocess
import time
import sys
import os
import re

# Añadir raíz del proyecto para importar utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from utils import speak

def find_recording_stream():
    """Busca el ID del stream que está grabando actualmente"""
    try:
        output = subprocess.check_output("pactl list source-outputs", shell=True).decode()
        
        # Buscar bloques de source-outputs
        current_id = None
        for line in output.split('\n'):
            if "Source Output #" in line:
                current_id = line.split("#")[1].strip()
            
            # Si encontramos algo que parece Waydroid o grabación genérica
            # (A veces Waydroid se muestra como 'python3' o 'pacat' o simplemente no tiene nombre claro)
            # Vamos a devolver el PRIMER stream que encontremos grabando que NO sea el monitor propio de cinnamon/gnome
            if current_id and "application.name" in line:
                # Ignorar monitores de volumen del sistema
                if "gnome.VolumeControl" in line or "Cinnamon Volume Control" in line:
                    current_id = None
                    continue
                
                print(f"🎯 Stream detectado: ID {current_id} ({line.strip()})")
                return current_id
                
        # Si llegamos aquí y tenemos un ID candidato perdimos el contexto, pero devolvamos el último válido que no sea sistema
        # Estrategia alternativa: devolver cualquier ID de grabación que no sea corked (pausado)
        return None
    except:
        return None

def test_force_routing():
    print("🎙️ TEST: MOVIMIENTO FORZADO DE AUDIO")
    print("=" * 50)
    print("\n📝 INSTRUCCIONES:")
    print("1. Abre la grabadora de sonidos en Waydroid")
    print("2. Presiona GRABAR en la app AHORA")
    print("3. Presiona ENTER aquí cuando ya esté grabando...")
    input()
    
    try:
        # 1. Obtener fuente MONITOR (lo que Fina habla)
        monitor_source = subprocess.check_output(
            "pactl list short sources | grep 'monitor' | grep -v 'waydroid' | grep -v 'aloop' | head -n1 | cut -f2",
            shell=True
        ).decode().strip()
        print(f"🔊 Fuente de Audio (Fina): {monitor_source}")
        
        # 2. Buscar quién está grabando
        print("\n🔍 Buscando la grabación de Waydroid...")
        stream_id = None
        
        # Intentar varias veces por si tarda en aparecer
        for i in range(5):
            stream_id = find_recording_stream()
            if stream_id:
                break
            time.sleep(0.5)
            
        if not stream_id:
            print("❌ No detecté ninguna grabación activa. ¿Seguro que Waydroid está grabando?")
            # Intentar estrategia bruta: listar todos los IDs
            ids = subprocess.check_output("pactl list short source-outputs | cut -f1", shell=True).decode().split()
            if ids:
                print(f"⚠️ Intentando con el último ID encontrado: {ids[-1]}")
                stream_id = ids[-1]
        
        if stream_id:
            print(f"\n🔌 MOVIENDO CABLE DE STREAM #{stream_id} a {monitor_source}...")
            subprocess.run(f"pactl move-source-output {stream_id} {monitor_source}", shell=True)
            print("✅ ¡Movimiento realizado!")
            
            # 3. Hablar
            print("\n🗣️ Fina hablando...")
            time.sleep(1)
            mensaje = "Hola. He movido tu cable de grabación a la fuerza. Si escuchas esto, la cirugía fue un éxito."
            speak(mensaje, None)
            time.sleep(3)
            
        else:
            print("😭 Imposible encontrar el stream de audio.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_force_routing()
