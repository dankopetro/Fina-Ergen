import os
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
import sounddevice as sd
import time
import sys

# Configuración
USER_NAME = "admin"
ERGEN_ROOT = os.path.dirname(os.path.abspath(__file__))
STORAGE_PATH = Path(ERGEN_ROOT) / "voice_profiles"
NUM_SAMPLES = 5
DURATION = 4
FS = 16000

def record_audio(duration=DURATION, fs=FS):
    print(f"🎤 Grabando por {duration} segundos...", end="", flush=True)
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    print(" ✅")
    return recording.flatten()

def main():
    print(f"\n🎙️  ENTRENAMIENTO DE VOZ PARA: {USER_NAME}")
    print(f"📂 Guardando en: {STORAGE_PATH}")
    print("--------------------------------------------------")
    
    # Asegurar directorio
    STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    
    print("🧠 Cargando modelo de codificación de voz (espere)...")
    encoder = VoiceEncoder()
    print("✅ Modelo cargado.\n")
    
    print("📋 INSTRUCCIONES:")
    print("Voy a pedirte que leas 5 frases diferentes.")
    print("Habla con tono natural y claro, a una distancia normal del micrófono.\n")
    
    frases = [
        "Hola Fina, soy Administrador y quiero que realices mis comandos.",
        "La temperatura ambiente hoy es perfecta para trabajar.",
        "Fina, activa el modo de seguridad y apaga las luces.",
        "Reproduce mi lista de música favorita en Spotify.",
        "Adiós, soy Administrador, inicia el protocolo de apagado."
    ]
    
    embeddings = []
    
    for i in range(NUM_SAMPLES):
        input(f"\nPresiona ENTER para grabar la Muestra {i+1}...")
        print(f"🗣️  Di: '{frases[i]}'")
        time.sleep(0.5)
        
        wav_data = record_audio()
        
        # Procesar
        wav = preprocess_wav(wav_data, source_sr=FS)
        embed = encoder.embed_utterance(wav)
        embeddings.append(embed)
        print(f"✨ Muestra {i+1} procesada exitosamente.")
        
    # Calcular promedio
    print("\n🔄 Calculando perfil de voz promedio...")
    avg_embed = np.mean(embeddings, axis=0)
    
    # Guardar
    file_path = STORAGE_PATH / f"{USER_NAME}.npy"
    np.save(file_path, avg_embed)
    
    print("\n========================================")
    print(f"✅ PERFIL DE VOZ GUARDADO: {file_path}")
    print("========================================")
    print("Ahora Fina debería reconocerte mucho mejor.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Cancelado por el usuario.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
