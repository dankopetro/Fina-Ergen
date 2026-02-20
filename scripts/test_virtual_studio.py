#!/usr/bin/env python3
import subprocess
import time
import os
import sys

# Añadir raíz del proyecto para importar utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# Intentar importar speak de utils
try:
    from utils import speak
    print("✅ Utils importado correctamente.")
except ImportError as e:
    print(f"⚠️ No se pudo importar utils: {e}")
    # Definir un speak de emergencia que usa el comando 'say' o imprime
    def speak(text, model=None):
        print(f"🗣️ (Simulado) {text}")
        # Intentar piper estático si existe, o pico2wave, o lo que sea.
        # Asumimos que Fina tiene un mecanismo de TTS.
        return

def test_virtual_studio():
    print("🎙️ TEST DE GRABACIÓN: ESTUDIO VIRTUAL")
    print("====================================")
    
    # Verificar si speak está disponible (doble check)
    if 'speak' not in globals():
        print("❌ Error Fatal: Función 'speak' no disponible.")
        return

    print("\n📝 PASO 1: Abre la Grabadora en Waydroid.")
    print("\n📝 PASO 2: Empieza a grabar AHORA.")
    print("\n📝 PASO 3: Presiona ENTER aquí inmediatamente.")
    input()
    
    # 1. Obtener ID del Monitor Virtual
    try:
        virtual_source = subprocess.check_output("pactl list short sources | grep 'FinaVoice.monitor' | cut -f1", shell=True).decode().strip()
        print(f"ℹ️ Fuente Virtual ID: {virtual_source}")
    except:
        print("❌ No encuentro 'FinaVoice.monitor'. ¿Ejecutaste el setup?")
        return

    mic_source = "58" # Default fallback
    
    # 2. Buscar Waydroid
    waydroid_id = None
    print("🔍 Buscando Waydroid...")
    for i in range(10):
        try:
            output = subprocess.check_output("pactl list source-outputs", shell=True).decode()
            blocks = output.split("Salida de fuente #")
            for block in blocks:
                if "Waydroid" in block:
                    waydroid_id = block.split("\n")[0].strip()
                    break
            if waydroid_id: break
        except: pass
        time.sleep(0.2)
        
    if waydroid_id:
        print(f"✅ Waydroid detectado: #{waydroid_id}")
        
        # 3. Conectar a Sala Virtual
        print(f"🔌 Conectando a Sala Virtual #{virtual_source}...")
        subprocess.run(f"pactl move-source-output {waydroid_id} {virtual_source}", shell=True)
        
        # 4. Hablar en la Sala Virtual
        print("\n🗣️ Fina hablando en el Estudio Virtual...")
        mensaje = "Hola Administrador. Esta es una prueba de grabación digital en el estudio virtual."
        
        # IMPORTANTE: Configurar variable de entorno para que el subproceso de audio use el sink virtual
        os.environ["PULSE_SINK"] = "FinaVoice"
        
        try:
            speak(mensaje, None)
        except Exception as e:
            print(f"❌ Error al hablar: {e}")
        finally:
             if "PULSE_SINK" in os.environ:
                del os.environ["PULSE_SINK"]
             
        time.sleep(1)
        
        # 5. Restaurar (Opcional)
        print("\n🔌 Desconectando...")
        try:
             # Intentar restaurar al mic físico (ID 58 o el que sea 'input' real)
             mic = subprocess.check_output("pactl list short sources | grep 'analog-stereo' | grep 'input' | head -n1 | cut -f1", shell=True).decode().strip()
             if mic:
                subprocess.run(f"pactl move-source-output {waydroid_id} {mic}", shell=True)
        except:
             pass
             
        print("\n🎉 LISTO.")
        print("👉 Detén la grabación y verifica.")
    else:
        print("❌ No detecté Waydroid grabando.")

if __name__ == "__main__":
    test_virtual_studio()
