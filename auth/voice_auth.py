import os
import numpy as np
import logging
from pathlib import Path
import sounddevice as sd
import time

logger = logging.getLogger("VoiceAuth")

try:
    from resemblyzer import VoiceEncoder, preprocess_wav
    HAS_RESEMBLYZER = True
except ImportError:
    HAS_RESEMBLYZER = False
    logger.warning("Resemblyzer no encontrado. La autenticación por voz estará deshabilitada.")

class VoiceAuthenticator:
    def __init__(self, storage_path=None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            def get_config_dir():
                xdg_config = os.environ.get("XDG_CONFIG_HOME")
                if xdg_config:
                    return os.path.join(xdg_config, "Fina")
                try:
                    from pathlib import Path
                    return os.path.join(str(Path.home()), ".config", "Fina")
                except:
                    return os.path.expanduser("~/.config/Fina")
            
            self.storage_path = Path(get_config_dir()) / "voice_profiles"
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.profiles_file = self.storage_path / "profiles.json"
        
        if HAS_RESEMBLYZER:
            print("🧠 Loading Voice Encoder Model...")
            self.encoder = VoiceEncoder()
            print("✅ Voice Encoder Loaded.")
        else:
            self.encoder = None
            logger.error("No se pudo inicializar VoiceEncoder porque resemblyzer no está instalado.")
        
    def record_audio(self, duration=3, fs=16000):
        print(f"🎤 Recording for {duration} seconds...")
        # Record mono audio
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        print("✅ Recording finished")
        return recording.flatten(), fs
        
    def enroll_new_user(self, user_name, num_samples=3):
        """
        Interactively enroll a new user by recording multiple samples.
        """
        embeddings = []
        print(f"\n--- Enrolling Voice for {user_name} ---")
        print("Please speak a full sentence naturally when prompted.")
        
        prompts = [
            "La temperatura en Buenos Aires es agradable hoy.",
            "Fina, por favor abre el navegador y busca noticias.",
            "Me gusta escuchar música mientras trabajo en la computadora."
        ]
        
        for i in range(num_samples):
            prompt = prompts[i % len(prompts)]
            print(f"\n📝 Sample {i+1}/{num_samples}")
            print(f"Say: '{prompt}'")
            input("Press Enter to start recording...")
            
            wav_data, fs = self.record_audio(duration=4, fs=16000)
            
            # Preprocess and embed
            # preprocess_wav can take a numpy array
            processed_wav = preprocess_wav(wav_data, source_sr=fs)
            embed = self.encoder.embed_utterance(processed_wav)
            embeddings.append(embed)
            print(f"✅ Sample {i+1} captured.")
            time.sleep(1)
            
        # Compute average embedding
        avg_embed = np.mean(embeddings, axis=0)
        
        # Save
        file_path = self.storage_path / f"{user_name}.npy"
        np.save(file_path, avg_embed)
        print(f"\n✅ Voice profile for {user_name} saved at {file_path}")
        return True

    def verify_user(self, user_name, audio_data, fs=16000, threshold=0.65):
        """
        Verify if the provided audio matches the verified user's profile.
        audio_data: numpy array of the audio
        """
        file_path = self.storage_path / f"{user_name}.npy"
        if not file_path.exists():
            logger.warning(f"Voice profile for {user_name} not found.")
            return False, 0.0
            
        # Load profile
        target_embed = np.load(file_path)
        
        # Embed candidate
        # CRITICAL FIX: Ensure format is float32 for librosa
        wav = audio_data.flatten().astype(np.float32)
        
        # Si parece int16 (valores grandes), normalizar a [-1, 1]
        if np.abs(wav).max() > 1.0:
            wav = wav / 32768.0
            
        processed_wav = preprocess_wav(wav, source_sr=fs)
        candidate_embed = self.encoder.embed_utterance(processed_wav)
        
        # Compute cosine similarity
        # Similarity is the dot product of normalized vectors
        # Resemblyzer embeddings are L2-normalized, so dot product is cosine similarity
        similarity = np.inner(candidate_embed, target_embed)
        
        is_match = similarity > threshold
        return bool(is_match), float(similarity)
