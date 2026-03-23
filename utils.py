# Standard Library
import os
import re
import shlex
import time
import json
import queue
import asyncio
import string
import subprocess
import threading
import logging
import shutil
import socket
import sys
import imaplib
import smtplib
try:
    import requests
except ImportError:
    requests = None

try:
    import aiohttp
except ImportError:
    aiohttp = None

from typing import List, Dict, Optional, Any, Tuple, Union, Callable
from email.message import EmailMessage
from datetime import datetime, timedelta

# --- DYNAMIC PATHS FOR ERGEN ---
ERGEN_ROOT = os.path.dirname(os.path.abspath(__file__))
# GLOBAL_ROOT is now same as ERGEN for independence
GLOBAL_ROOT = ERGEN_ROOT

# --- ROBUST LOGGING SETUP ---
# Clear pre-existing handlers from libraries to avoid conflicts
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

def get_config_dir():
    # 1. Prioridad: XDG_CONFIG_HOME
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return os.path.join(xdg_config, "Fina")
    # 2. Rescate: Home del usuario real
    try:
        from pathlib import Path
        return os.path.join(str(Path.home()), ".config", "Fina")
    except:
        return os.path.expanduser("~/.config/Fina")

CONFIG_DIR = get_config_dir()
log_base_config_dir = os.path.join(CONFIG_DIR, "Logs")
log_dir = os.path.join(log_base_config_dir, datetime.now().strftime("%Y-%m-%d"))
os.makedirs(log_dir, exist_ok=True)
log_filename = f"ergen_session_{datetime.now().strftime('%H-%M-%S')}.log"
log_path = os.path.join(log_dir, log_filename)

# Force unbuffered output for streams
class UnbufferedStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

file_handler = logging.FileHandler(log_path, mode='w', encoding='utf-8')
file_handler.setFormatter(formatter)

# --- SILENCIAR LIBRERÍAS RUIDOSAS (DIETA DIGITAL EXTREMA) ---
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# CRITICAL para HuggingFace: suprime el warning "unauthenticated requests"
for lib in ["huggingface_hub", "huggingface_hub.utils._http", "huggingface_hub.utils",
            "urllib3", "sentence_transformers", "transformers", "tqdm"]:
    logging.getLogger(lib).setLevel(logging.CRITICAL)

# Silenciar httpx (baja a WARNING, no hace falta CRITICAL)
logging.getLogger("httpx").setLevel(logging.WARNING)

try:
    import transformers
    transformers.utils.logging.set_verbosity_error()
except: pass

def _clean_old_logs(days=7):
    """Limpia logs de sesión más viejos que N días"""
    try:
        now = time.time()
        for folder in os.listdir(log_base_config_dir):
            folder_path = os.path.join(log_base_config_dir, folder)
            if os.path.isdir(folder_path):
                # Si la carpeta tiene formato YYYY-MM-DD
                if re.match(r'\d{4}-\d{2}-\d{2}', folder):
                    mtime = os.path.getmtime(folder_path)
                    if (now - mtime) > (days * 86400):
                        shutil.rmtree(folder_path)
                        logging.info(f"🧹 Log antiguo borrado: {folder}")
    except: pass

def _truncate_services_log(max_size_mb=2):
    """Evita que fina_services.log crezca infinitamente"""
    services_log = os.path.join(CONFIG_DIR, "fina_services.log")
    if os.path.exists(services_log):
        try:
            size_mb = os.path.getsize(services_log) / (1024 * 1024)
            if size_mb > max_size_mb:
                # Truncar dejando solo el final o simplemente vaciarlo
                with open(services_log, 'w') as f:
                    f.write(f"--- Log truncado por tamaño ({datetime.now()}) ---\n")
                logging.info(f"✂️ fina_services.log truncado (era {size_mb:.2f} MB)")
        except: pass

# Ejecutar dieta digital al inicio
_clean_old_logs()
_truncate_services_log()

stream_handler = UnbufferedStreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler]
)

logger = logging.getLogger("ErgenUtils")
logger.info(f"--- SESIÓN INICIADA: {datetime.now()} ---")
logger.info(f"Log path: {log_path}")

# --- CONFIG DIRECTORY LOGIC ALREADY DEFINED AT TOP ---
for folder in ["", "voice_models", "voice_profiles", "temp_audio", "plugins", "model", "faces", "Logs"]:
    path = os.path.join(CONFIG_DIR, folder)
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        logger.error(f"❌ Error creando carpeta {path}: {e}")

# Definir rutas absolutas para archivos de datos
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
USER_DATA_PATH = os.path.join(CONFIG_DIR, "user_data.json")
CONTACTS_PATH_PRIMARY = os.path.join(CONFIG_DIR, "contact.json")
CONTACTS_PATH_SECONDARY = os.path.join(CONFIG_DIR, "contacts.json")

CONTACTS_PATH = CONTACTS_PATH_PRIMARY if os.path.exists(CONTACTS_PATH_PRIMARY) else CONTACTS_PATH_SECONDARY
CONFIG_PY_PATH = os.path.join(CONFIG_DIR, "config.py")
TUYA_CONFIG_PATH = os.path.join(CONFIG_DIR, "tuya_config.json")

# DIAGNÓSTICO DE PERMISOS (Crítico para AppImage)
import getpass
current_user = getpass.getuser()
logger.info(f"👤 Usuario Actual: {current_user}")
logger.info(f"🏠 HOME: {os.environ.get('HOME')}")
logger.info(f"🌐 XDG_CONFIG_HOME: {os.environ.get('XDG_CONFIG_HOME')}")
logger.info(f"📂 Config Dir: {CONFIG_DIR} (Acceso R: {os.access(CONFIG_DIR, os.R_OK)}, W: {os.access(CONFIG_DIR, os.W_OK)})")

for label, p in [("Settings", SETTINGS_PATH), ("Contacts", CONTACTS_PATH), ("Config.py", CONFIG_PY_PATH)]:
    exists = os.path.exists(p)
    readable = os.access(p, os.R_OK) if exists else "N/A"
    logger.info(f"📄 {label}: {p} (Existe: {exists}, Lectura: {readable})")

def _ensure_config_exists():
    """Migrar o crear archivos base si no existen en .config/Fina"""
    # Intentar detectar si estamos en un entorno de desarrollo o AppImage
    # Si estamos en AppImage, ERGEN_ROOT suele ser algo como /tmp/.mount_XXXX
    migration_map = {
        os.path.join(ERGEN_ROOT, "config", "settings.json"): SETTINGS_PATH,
        os.path.join(ERGEN_ROOT, "user_data.json"): USER_DATA_PATH,
        os.path.join(ERGEN_ROOT, "config", "contact.json"): CONTACTS_PATH,
        os.path.join(ERGEN_ROOT, "config.py"): CONFIG_PY_PATH,
        os.path.join(ERGEN_ROOT, "tuya_config.json"): TUYA_CONFIG_PATH,
    }
    for src, dst in migration_map.items():
        if not os.path.exists(dst) and os.path.exists(src):
            try:
                # Solo copiar si el destino no existe, para no pisar ajustes del usuario
                shutil.copy2(src, dst)
                logger.info(f"📦 Auto-Migración exitosa: {os.path.basename(src)} -> {CONFIG_DIR}")
            except Exception as e:
                logger.error(f"❌ Falló auto-migración de {src}: {e}")

# Ejecutar migración silenciosa para asegurar que el AppImage tenga algo que leer
_ensure_config_exists()

# --- I18N SUPPORT ---
I18N_DATA = {}
try:
    lang_path = os.path.join(ERGEN_ROOT, "lang.json")
    if os.path.exists(lang_path):
        with open(lang_path, 'r', encoding='utf-8') as f:
            I18N_DATA = json.load(f)
            logger.info(f"🌍 Idiomas cargados: {list(I18N_DATA.keys())}")
except Exception as e:
    logger.error(f"❌ Error cargando lang.json: {e}")

# --- MODISMOS SUPPORT ---
IDIO_DATA = {}
try:
    potential_paths = [
        os.path.join(ERGEN_ROOT, "modismos.json"),
        os.path.join(CONFIG_DIR, "modismos.json"),
        "/usr/lib/fina-ergen/modismos.json"
    ]
    idio_path: Optional[str] = None
    for p in potential_paths:
        if p and os.path.exists(p):
            idio_path = p
            break
            
    if idio_path:
        with open(str(idio_path), 'r', encoding='utf-8') as f:
            IDIO_DATA = json.load(f)
            logger.info(f"🌍 Modismos regionales cargados desde: {idio_path}")
    else:
        logger.warning("⚠️ No se encontró modismos.json en ninguna ruta conocida.")
except Exception as e:
    logger.error(f"❌ Error cargando modismos.json: {e}")

def get_sys_locale():
    """Detecta el locale completo (ej: es_AR) para modismos."""
    # 1. Preferencia guardada (ej: es_AR) en settings.json o config.py
    config_lang = get_unified_config("FINA_LANGUAGE")
    if config_lang and len(config_lang) >= 5: # ej: es_AR
        logger.debug(f"🔍 Locale desde config: {config_lang}")
        return config_lang

    # 2. Variables de entorno (LANG=es_AR.UTF-8)
    for env_var in ['LANG', 'LC_ALL', 'LANGUAGE']:
        env_val = os.environ.get(env_var, '').strip()
        if env_val and env_val not in ('C', 'POSIX', 'C.UTF-8'):
            loc = env_val.split('.')[0]
            logger.debug(f"🔍 Locale desde entorno ({env_var}): {loc}")
            return loc
    
    # 3. Fallback a locale del sistema vía comando
    try:
        import subprocess as _sp
        result = _sp.run(['locale'], capture_output=True, text=True, timeout=1)
        for line in result.stdout.splitlines():
            if line.startswith('LANG='):
                val = line.split('=')[1].strip('"').strip("'")
                if val: 
                    loc = val.split('.')[0]
                    logger.debug(f"🔍 Locale desde comando locale: {loc}")
                    return loc
    except: pass
    
    # Intento final: buscar en el sistema el país
    try:
        if os.path.exists('/etc/timezone'):
            with open('/etc/timezone', 'r') as f:
                tz = f.read().strip()
                if 'Argentina' in tz: 
                    logger.debug("🔍 Detectada Zona Horaria Argentina: Forzando es_AR")
                    return "es_AR"
    except: pass

    logger.debug("🔍 Usando fallback por defecto: es_AR")
    print("🌍 Idioma Regional Detectado:", "es_AR", flush=True)
    return "es_AR" # Fallback conservador

def get_sys_lang():
    """Detecta el idioma base (es, en, etc)."""
    loc = get_sys_locale()
    return loc.split('_')[0].lower()

def get_idiom(category, default=None):
    """Obtiene un modismo aleatorio para la categoría."""
    import random
    locale = get_sys_locale()
    lang = get_sys_lang()
    
    logger.info(f"🗣️ Solicitando modismo: {category} (Detected Locale: {locale}, Lang: {lang})")
    logger.info(f"📂 Modismos disponibles para: {list(IDIO_DATA.keys())}")
    
    # 1. Por locale exacto (ej: es_AR) considerando mayúsculas/minúsculas
    # Normalizamos llaves para búsqueda insensible
    idio_keys_lower = {k.lower(): k for k in IDIO_DATA.keys()}
    
    locale_lower = locale.lower()
    if locale_lower in idio_keys_lower:
        real_key = idio_keys_lower[locale_lower]
        phrases = IDIO_DATA[real_key].get(category)
        if phrases: return random.choice(phrases)
        
    # 2. Por prefijo de idioma (si es 'es_ES' y tenemos 'es_AR', o si solo tenemos 'es')
    base_lang = locale_lower.split('_')[0]
    if base_lang in idio_keys_lower:
        real_key = idio_keys_lower[base_lang]
        phrases = IDIO_DATA[real_key].get(category)
        if phrases: return random.choice(phrases)
    
    # 3. Buscar cualquier coincidencia que empiece con el mismo idioma (ej: 'es_')
    # Forzamos prioridad para Argentina si el idioma es español
    if base_lang == "es":
        if "es_ar" in idio_keys_lower:
            real_key = idio_keys_lower["es_ar"]
            phrases = IDIO_DATA[real_key].get(category)
            if phrases: return random.choice(phrases)
    
    for key_lower, real_key in idio_keys_lower.items():
        if key_lower.startswith(f"{base_lang}_"):
            phrases = IDIO_DATA[real_key].get(category)
            if phrases: return random.choice(phrases)

    # 5. Fallback proporcionado por el usuario
    if default is not None:
        return default

    # 6. Fallback hardcoded (ahora consciente del tiempo)
    if category == "welcome":
        h = datetime.now().hour
        if h < 12: greet = "Buen día."
        elif h < 20: greet = "Buenas tardes."
        else: greet = "Buenas noches."
        return random.choice([f"{greet} ¿En qué puedo ayudarte?", greet, "Hola."])
    
    return random.choice(["Entendido, descanso.", "Hasta luego.", "Me pongo en espera."])

def update_ui_state(status, process=None, intensity=0.0, extra_payload=None):
    try:
        if process:
            process = auto_translate(process)

        payload = {"status": status, "process": process, "intensity": intensity}
        if extra_payload: payload.update(extra_payload)
        
        data = {"type": "event", "name": "fina-state", "payload": payload}
        # LOG CRÍTICO PARA EL USUARIO: Ver lo que se envía a la UI en la terminal
        if process:
            # Clean print for terminal visibility
            print(f"🖥️ UI UPDATE -> {process}", flush=True)
        print(json.dumps(data), flush=True)

        # Intento de redundancia HTTP por si el evento de consola falla
        try:
             import requests
             requests.post("http://127.0.0.1:18000/api/state", json=payload, timeout=0.05)
        except: pass

    except: pass

def i18n(key, fallback=""):
    # Prioridad 1: Traducciones estándar (vía I18N_DATA)
    lang = get_sys_lang()
    if lang not in I18N_DATA:
        lang = "en"
    
    translations = I18N_DATA.get(lang, {})
    return translations.get(key, fallback)

# --- CONFIGURATION UNIFICATION (UI Priority) ---
def get_unified_config(key, default=None):
    """Prioriza settings.json (UI) sobre config.py (Código)"""
    # 1. Intentar desde settings.json
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                val = data.get("apis", {}).get(key)
                if val: return val
                # Fallback para claves de primer nivel
                val = data.get(key)
                if val: return val
    except: pass

    # 2. Fallback al config.py absoluto del usuario
    try:
        cfg, _ = load_config()
        return getattr(cfg, key, default)
    except:
        return default

def load_config():
    """Carga config.py desde ~/.config/Fina con CARGA ABSOLUTA para evitar colisiones"""
    import importlib.util
    try:
        if os.path.exists(str(CONFIG_PY_PATH)):
            spec = importlib.util.spec_from_file_location("user_config", str(CONFIG_PY_PATH))
            if spec and spec.loader:
                cfg = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(cfg)
                logger.debug(f"✅ config.py cargado desde: {CONFIG_PY_PATH}")
                return cfg, True
            else:
                logger.warning("⚠️ No se pudo crear el spec para config.py")
        
        # Fallback al config.py interno si el del usuario no existe o falló el spec
        try:
            import config as internal_cfg
            return internal_cfg, False
        except ImportError:
            # Si ni siquiera el interno existe, devolvemos dummy
            class EmptyConfig: pass
            return EmptyConfig(), False
    except Exception as e:
        logger.error(f"❌ Error crítico cargando config.py: {e}")
        class DummyConfig:
            def __getattr__(self, name): return None
        return DummyConfig(), False

def check_system_dependencies():
    """Verifica si faltan herramientas críticas en el sistema"""
    deps = {
        "ffmpeg": "Procesamiento de audio/video",
        "adb": "Control de móvil y timbre",
        "scrcpy": "Visualización de cámara",
        "vlc": "Reproductor de música",
        "nmap": "Escaneo de red IoT",
        "xclip": "Portapapeles (X11)",
        "lsof": "Limpieza de puertos y procesos",
        "fuser": "Liberación de sockets"
    }
    missing = []
    for cmd, desc in deps.items():
        if shutil.which(cmd) is None:
            # Caso especial: wl-clipboard
            if cmd == "xclip" and shutil.which("wl-paste"): continue
            missing.append(f"{cmd} ({desc})")
    
    if missing:
        print("\n\x1b[33m⚠️ ADVERTENCIA: Faltan dependencias de sistema:\x1b[0m")
        for m in missing: print(f"  - {m}")
        print("\x1b[33m💡 Algunas funciones podrían no estar disponibles.\x1b[0m\n")
        
        # Pop-up visual para ayudar a usuarios novatos en AppImage
        try:
            if shutil.which("zenity"):
                lang = get_sys_lang()
                pkg_names = " ".join([m.split()[0] for m in missing])
                if lang == "es":
                    msg = "¡Hola! Fina funcionará bien, pero he detectado que en tu Linux faltan estas herramientas del sistema:\n\n"
                    for m in missing: msg += f" - {m}\n"
                    msg += f"\nPara tener la experiencia al 100%, abrí una terminal y ejecutá:\n\nsudo apt install {pkg_names}"
                    title = "Aviso de Sistema - Fina Ergen"
                else:
                    msg = "Hello! Fina will run fine, but I detected your Linux is missing some system tools:\n\n"
                    for m in missing: msg += f" - {m}\n"
                    msg += f"\nFor a 100% complete experience, open a terminal and run:\n\nsudo apt install {pkg_names}"
                    title = "System Notice - Fina Ergen"
                
                import subprocess
                subprocess.Popen(["zenity", "--warning", "--title", title, "--text", msg, "--width", "500"])
        except Exception as e:
            pass
            
    return missing

# Caching for Lazy Loading
vosk_model = None
vosk_recognizer = None
loaded_language = None

_translation_cache = {}

def auto_translate(text: str) -> str:
    """Traduce automáticamente los textos de Fina ('es') al idioma del usuario si este no es español."""
    if not text or not isinstance(text, str):
        return str(text) if text is not None else ""
        
    lang = get_sys_lang()
    # Si Fina está en español o si pasamos un texto muy largo (Wiki/Noticias que ya se obtienen en el propio idioma), evitamos traducir.
    if lang == "es" or len(text) > 300:
        return text
        
    # Slice seguro para caché
    text_prefix = text[:50] if len(text) > 50 else text
    cache_key = f"{lang}:{text_prefix}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
        
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source='es', target=lang).translate(text)
        _translation_cache[cache_key] = translated
        return translated
    except Exception as e:
        logger.warning(f"Error de traducción en Fina: {e}")
        _translation_cache[cache_key] = text
        return text

def update_ui_state(status, process=None, intensity=0.0, extra_payload=None):
    try:
        if process:
            process = auto_translate(process)

        payload = {"status": status, "process": process, "intensity": intensity}
        if extra_payload: payload.update(extra_payload)
        
        data = {"type": "event", "name": "fina-state", "payload": payload}
        # LOG CRÍTICO PARA EL USUARIO: Ver lo que se envía a la UI en la terminal
        if process:
            # Clean print for terminal visibility
            print(f"🖥️ UI UPDATE -> {process}", flush=True)
        print(json.dumps(data), flush=True)

        # Intento de redundancia HTTP por si el evento de consola falla
        # Esto ayuda si la API está viva pero el pase de mensajes stdout falla
        try:
             import requests
             requests.post("http://127.0.0.1:18000/api/state", json=payload, timeout=0.05)
        except: pass

    except: pass

def send_ui_command(name, payload):
    """Envía un comando al frontend vía API REST (polling) y stdout (redundancia)"""
    try:
        data = {"name": name, "payload": payload}
        # 1. Redundancia por stdout
        print(json.dumps({"type": "event", "name": name, "payload": payload}), flush=True)
        # 2. Vía API para que el polling de la UI lo capture
        import requests
        requests.post("http://127.0.0.1:18000/api/command", json=data, timeout=0.1)
    except: pass


PIPER_MODELS = {
    "es": {
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/ald/medium/es_MX-ald-medium.onnx.json",
        "name": "es_MX-ald-medium.onnx"
    },
    "en": {
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx.json",
        "name": "en_US-amy-low.onnx"
    },
    "fr": {
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/low/fr_FR-siwis-low.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/low/fr_FR-siwis-low.onnx.json",
        "name": "fr_FR-siwis-low.onnx"
    },
    "de": {
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/low/de_DE-thorsten-low.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/low/de_DE-thorsten-low.onnx.json",
        "name": "de_DE-thorsten-low.onnx"
    },
    "ja": {
        "onnx": "https://huggingface.co/ayousanz/piper-plus-tsukuyomi-chan/resolve/main/tsukuyomi-wavlm-300epoch.onnx",
        "json": "https://huggingface.co/ayousanz/piper-plus-tsukuyomi-chan/resolve/main/config.json",
        "name": "ja_JP-tsukuyomi-medium.onnx"
    },
    "zh": {
        "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx",
        "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx.json",
        "name": "zh_CN-huayan-medium.onnx"
    }
}

def _download_piper_model_if_missing(language=None):
    """Descarga un modelo de voz pequeño según el idioma detectado/elegido."""
    import requests
    if not language: language = get_sys_lang()
    
    model_info = PIPER_MODELS.get(language, PIPER_MODELS["en"])
    onnx_url = model_info["onnx"]
    json_url = model_info["json"]
    model_name = model_info["name"]
    
    user_models_dir = os.path.join(CONFIG_DIR, "voice_models")
    if not os.path.exists(user_models_dir): os.makedirs(user_models_dir, exist_ok=True)
    
    onnx_dest = os.path.join(user_models_dir, model_name)
    json_dest = os.path.join(user_models_dir, model_name + ".json")
    
    if os.path.exists(onnx_dest): return onnx_dest
    
    try:
        logger.info(f"🗣️ Descargando modelo de voz inicial ({language})...")
        update_ui_state("idle", process=f"Descargando Voz: {language.upper()}...")
        
        # Download JSON first (Small)
        json_resp = requests.get(json_url)
        with open(json_dest, 'wb') as f: f.write(json_resp.content)
        
        # Download ONNX (Large)
        response = requests.get(onnx_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        with open(onnx_dest, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        update_ui_state("idle", process=f"Voz {language.upper()}: {percent}%")
        
        update_ui_state("idle", process=i18n("sys_ready_short", "SISTEMA LISTO"))
        return onnx_dest
    except Exception as e:
        logger.error(f"❌ Error descarga Piper: {e}")
        return None

# --- VOICE ENGINE (SEQUENTIAL & CONTROLLED) ---
voice_queue = queue.Queue()
current_voice_process = None
voice_process_lock = threading.Lock()

def _voice_engine_worker():
    """Motor de voz SECUENCIAL - espera a que termine cada frase antes de la siguiente."""
    global current_voice_process
    # Detectar rutas dinámicamente
    import shutil
    # Estrategia: 1. Assets empaquetados, 2. Local, 3. PATH
    piper_path = None
    potential_locations = [
        # Ruta REAL donde Tauri/deb instala el sidecar
        "/usr/lib/fina-ergen/binaries/piper-x86_64-unknown-linux-gnu",
        "/usr/lib/fina-ergen/binaries/piper",
        # Tauri externalBin también puede ir a /usr/bin
        "/usr/bin/piper-x86_64-unknown-linux-gnu",
        "/usr/bin/piper",
        "/usr/local/bin/piper",
        # Rutas dentro del bundle de recursos
        os.path.join(ERGEN_ROOT, "binaries", "piper", "piper"),
        os.path.join(ERGEN_ROOT, "binaries", "piper-x86_64-unknown-linux-gnu"),
        os.path.join(ERGEN_ROOT, "piper-x86_64-unknown-linux-gnu"),
        os.path.join(ERGEN_ROOT, "piper"),
        os.path.join(os.path.dirname(ERGEN_ROOT), "binaries", "piper-x86_64-unknown-linux-gnu"),
        os.path.join(ERGEN_ROOT, "bin", "piper"),
        "/usr/lib/fina-ergen/_up_/binaries/piper-x86_64-unknown-linux-gnu",
        os.path.join(os.path.expanduser("~"), ".local", "bin", "piper")
    ]
    for loc in potential_locations:
        if os.path.exists(loc):
            # Intentar dar permisos si faltan
            if not os.access(loc, os.X_OK):
                try: 
                    import stat
                    os.chmod(loc, os.stat(loc).st_mode | stat.S_IEXEC)
                except: pass
            
            if os.access(loc, os.X_OK):
                piper_path = loc
                break
        
        # 2. Intentar con el sufijo de Tauri (sidecar)
        sidecar = f"{loc}-x86_64-unknown-linux-gnu"
        if os.path.exists(sidecar):
            if not os.access(sidecar, os.X_OK):
                try:
                    import stat
                    os.chmod(sidecar, os.stat(sidecar).st_mode | stat.S_IEXEC)
                except: pass
            if os.access(sidecar, os.X_OK):
                piper_path = sidecar
                break

    if not piper_path:
        piper_path = shutil.which("piper")

    aplay_path = shutil.which("aplay") or "/usr/bin/aplay"

    if not piper_path:
        logger.error(f"FATAL: Piper no encontrado. La síntesis de voz no funcionará.")
    if not aplay_path or not os.path.exists(aplay_path):
        logger.error(f"FATAL: Aplay no encontrado (paquete alsa-utils insuficiente).")
    
    temp_dir = os.path.join(CONFIG_DIR, "temp_audio")

    while True:
        try:
            item = voice_queue.get()
            if item is None: 
                break
            
            try: # Inner try ensures task_done is called
                # Unpacking seguro
                text, model_path = item
                
                if not model_path:
                    # 1. Prioridad: carpeta personal del usuario
                    user_models_dir = os.path.join(CONFIG_DIR, "voice_models")
                    for fname in ["es_MX-ald-medium.onnx", "en_US-amy-low.onnx", "es_AR-daniela-high.onnx", "es_MX-claude-high.onnx", "es_MX-laura-high.onnx", "miro_es-ES.onnx"]:
                        candidate = os.path.join(user_models_dir, fname)
                        if os.path.exists(candidate):
                            model_path = candidate
                            break
                    # 2. Si no encontró ninguno conocido, tomar cualquier .onnx del directorio
                    if not model_path and os.path.exists(user_models_dir):
                        for f in os.listdir(user_models_dir):
                            if f.endswith(".onnx"):
                                model_path = os.path.join(user_models_dir, f)
                                break
                    # 3. Fallback: ruta definida por el usuario en la UI
                    if not model_path:
                        user_defined_path = get_unified_config("VOICE_MODELS_PATH")
                        if user_defined_path and os.path.exists(user_defined_path):
                            if os.path.isdir(user_defined_path):
                                for f in os.listdir(user_defined_path):
                                    if f.endswith(".onnx"):
                                        model_path = os.path.join(user_defined_path, f)
                                        break
                            else:
                                model_path = user_defined_path

                # Verify model exists
                if not model_path or not os.path.exists(model_path):
                    logger.warning(f"Rescate: Modelo {model_path} no encontrado. Buscando alternativa...")
                    user_models_dir = os.path.join(CONFIG_DIR, "voice_models")
                    potential_models = []
                    if os.path.exists(user_models_dir):
                        potential_models = [os.path.join(user_models_dir, m) for m in os.listdir(user_models_dir) if m.endswith(".onnx")]
                    if potential_models:
                        model_path = potential_models[0]
                        logger.info(f"Usando modelo de rescate: {model_path}")
                    else:
                        # Auto-descarga si no hay nada
                        model_path = _download_piper_model_if_missing()

                clean_text = text.replace('"', '').replace("'", "").replace("\n", " ").strip()
                if not clean_text:
                    continue

                filename = f"speech_{int(time.time()*1000)}.wav"
                filepath = os.path.join(temp_dir, filename)
                
                # Comando de generación
                if not piper_path or not model_path or not os.path.exists(model_path):
                    logger.error(f"TTS abortado: Piper o modelo no válido. Path: {piper_path}, Model: {model_path}")
                    continue

                safe_text = shlex.quote(clean_text)
                # Directorio donde están las .so y espeak-ng-data de Piper (bundled con el .deb)
                piper_libs_dir = "/usr/lib/fina-ergen/binaries/piper"
                if not os.path.exists(piper_libs_dir):
                    piper_libs_dir = os.path.join(os.path.dirname(piper_path), "piper") if piper_path else ""
                espeak_data = os.path.join(piper_libs_dir, "espeak-ng-data")
                espeak_flag = f'--espeak-data "{espeak_data}"' if os.path.exists(espeak_data) else ""
                gen_cmd = (
                    f'echo {safe_text} | '
                    f'LD_LIBRARY_PATH="{piper_libs_dir}:$LD_LIBRARY_PATH" '
                    f'ESPEAK_DATA_PATH="{espeak_data}" '
                    f'{piper_path} --model "{model_path}" {espeak_flag} --length_scale 1.3 --output_file "{filepath}"'
                )
                
                # Ejecutar generación (Esto causa la latencia "invisible")
                gen_success = False
                piper_stderr = ""
                try:
                    result = subprocess.run(gen_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=60)
                    piper_stderr = result.stderr.decode("utf-8", errors="ignore").strip()
                    gen_success = True
                except subprocess.TimeoutExpired:
                    logger.error("TTS Timeout: Piper tardó demasiado en generar el audio (>60s).")
                except Exception as e:
                    logger.error(f"TTS Error ejecutando Piper: {e}")
                
                if piper_stderr:
                    logger.debug(f"Piper stderr: {piper_stderr[:500]}")
                
                if gen_success and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    update_ui_state("speaking", text, 0.8)
                    
                    play_cmd = f'{aplay_path} -q "{filepath}"'
                    
                    with voice_process_lock:
                        current_voice_process = subprocess.Popen(play_cmd, shell=True)
                    
                    # Esperar a que termine de hablar
                    if current_voice_process:
                        try:
                            current_voice_process.wait(timeout=30)
                        except subprocess.TimeoutExpired:
                            logger.error("Audio playback timed out")
                            current_voice_process.kill()
                        except: pass
                        
                    try: os.remove(filepath)
                    except: pass
                else:
                    # Fallback visual si falla el audio
                    logger.error("Fallo generación/reproducción audio")
                    update_ui_state("speaking", text, 0.0)
                    time.sleep(2)

                with voice_process_lock:
                    current_voice_process = None
                
                if voice_queue.empty():
                    # Pequeña espera para que el usuario pueda leer el último mensaje antes de volver a 'ESCUCHANDO'
                    time.sleep(0.8)
                    update_ui_state("idle", "ESCUCHANDO...", 0.0)
                else:
                    # Pausa natural entre frases consecutivas
                    time.sleep(0.4)

            finally:
                # CRITICAL: Always mark done so main thread doesn't freeze
                voice_queue.task_done()
            
        except Exception as e:
            logger.error(f"CRITICAL WORKER ERROR: {e}")
            with voice_process_lock:
                current_voice_process = None
            # Last ditch attempt to unblock queue if get() succeeded but inner try failed horribly?
            # Actually inner try catches most.
            time.sleep(1)

threading.Thread(target=_voice_engine_worker, daemon=True).start()

def stop_voice_engine():
    """Detiene el motor de voz y mata cualquier proceso activo."""
    global current_voice_process
    with voice_process_lock:
        if current_voice_process:
            try:
                current_voice_process.terminate()
                current_voice_process.wait(timeout=1)
            except:
                try:
                    current_voice_process.kill()
                except:
                    pass
            current_voice_process = None
    
    # Limpiar cola
    while not voice_queue.empty():
        try:
            voice_queue.get_nowait()
            voice_queue.task_done()
        except:
            break
    
    # Enviar señal de parada al worker
    voice_queue.put(None)


def speak(text, selected_model=None, sink=None, wait=True):
    """
    selected_model: Ruta al archivo .onnx
    sink: Ignorado por ahora, para compatibilidad con main.py
    wait: Si es True (por defecto), espera a que termine de hablar antes de retornar
    """
    if not text: return
    text = auto_translate(text)

    if selected_model == "ElevenLabs":
        from elevenlabs.client import ElevenLabs
        from elevenlabs.play import play
        try:
            api_key = get_unified_config("ELEVENLABS_API_KEY")
            voice_id = get_unified_config("FINA_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") # Fallback ID
            if not api_key:
                 raise ValueError("No ElevenLabs API Key")
            client = ElevenLabs(api_key=api_key)
            audio = client.text_to_speech.convert(text=text, voice_id=voice_id, model_id="eleven_multilingual_v2")
            play(audio)
        except Exception as e: 
            logger.warning(f"ElevenLabs falló, usando Piper: {e}")
            voice_queue.put((text, None)) 
            if wait: voice_queue.join()
    else:
        # Enviamos a la cola para no bloquear el hilo principal (main loop)
        voice_queue.put((text, selected_model))
        if wait:
            # Esperar a que el worker termine de procesar la cola
            voice_queue.join()


# --- SPEECH RECOGNITION (VOSK) ---
# Flag para no saturar el log con errores de modelo
vosk_error_reported = False

VOSK_MODELS = {
    "es": ("vosk-model-small-es-0.42", "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"),
    "en": ("vosk-model-small-en-us-0.15", "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"),
    "fr": ("vosk-model-small-fr-0.22", "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip"),
    "de": ("vosk-model-small-de-0.15", "https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip"),
    "ja": ("vosk-model-small-ja-0.22", "https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip"),
    "zh": ("vosk-model-small-cn-0.22", "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip")
}

def _download_vosk_model(dest_path, model_name, url, language):
    """Descarga el modelo Vosk guardando a disco y con barra de progreso."""
    import zipfile
    import requests
    from io import BytesIO
    import shutil
    
    model_dir = os.path.dirname(dest_path) # ~/.config/Fina/model
    if not os.path.exists(model_dir):
        os.makedirs(model_dir, exist_ok=True)
        
    try:
        logger.info(f"👂 Fina está descargando el modelo rápido ('{model_name}') para idioma '{language}'...")
        update_ui_state("idle", process=f"Descargando Cerebro... 0%")
        
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            zip_path = os.path.join(model_dir, f"{model_name}.zip")
            
            with open(zip_path, 'wb') as f:
                downloaded = 0
                last_percent = -1
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int((downloaded / total_size) * 100)
                            if percent != last_percent and percent % 5 == 0:
                                update_ui_state("idle", process=f"Descargando Cerebro... {percent}%")
                                last_percent = percent
            
            logger.info("📦 Descarga completada. Extrayendo archivos...")
            update_ui_state("idle", process=f"Extrayendo ({language})...")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(model_dir)
                
            os.remove(zip_path) # Limpiar el zip
            
            extracted_dir = os.path.join(model_dir, model_name)
            if os.path.exists(extracted_dir) and extracted_dir != dest_path:
                if os.path.exists(dest_path): shutil.rmtree(dest_path)
                os.rename(extracted_dir, dest_path)
                
            logger.info("✅ Modelo pesado Fina instalado correctamente.")
            return True
    except Exception as e:
        logger.error(f"❌ No se pudo descargar el modelo Vosk ({model_name}): {e}")
    return False

def load_vosk_model(language=None):
    global vosk_model, vosk_recognizer, loaded_language, vosk_error_reported
    
    if not language:
        language = get_sys_lang()

    if vosk_model is not None and loaded_language == language: return
    
    try:
        from vosk import Model, KaldiRecognizer, SetLogLevel
        SetLogLevel(-1)
        
        # Obtenemos info del modelo pequeño y rápido
        model_name, url_small = VOSK_MODELS.get(language, VOSK_MODELS["en"])
        
        # Nombres de modelo a buscar (Prioridad 1: Idioma Seleccionado -> Prioridad 2: Inglés base rápido)
        model_names_to_try = [model_name, f"vosk-model-small-{language}-0.42", f"vosk-model-small-{language}-0.22", f"vosk-model-small-{language}-0.15", f"vosk-model-{language}-0.42", f"vosk-model-{language}-0.22"]
        model_names_to_try.append("vosk-model-small-en-us-0.15") # Fallback universal inglés

        loaded_path = None
        for m_name in model_names_to_try:
            user_config_path = os.path.join(CONFIG_DIR, "model", m_name)
            project_path = os.path.join(ERGEN_ROOT, "model", m_name)
            
            if os.path.exists(user_config_path):
                loaded_path = user_config_path
                break
            elif os.path.exists(project_path):
                loaded_path = project_path
                break

        if loaded_path:
            vosk_model = Model(loaded_path)
            vosk_recognizer = KaldiRecognizer(vosk_model, 16000)
            loaded_language = language
            vosk_error_reported = False
            logger.info(f"✅ Vosk cargado desde: {loaded_path} ({language})")
        else:
            logger.info(f"ℹ️ Modelo rápido no encontrado. Auto-descargando '{model_name}' (~40MB)...")
            target_dest = os.path.join(CONFIG_DIR, "model", model_name)
            
            if _download_vosk_model(target_dest, model_name, url_small, language):
                vosk_model = Model(target_dest)
                vosk_recognizer = KaldiRecognizer(vosk_model, 16000)
                loaded_language = language
                vosk_error_reported = False
            else:
                if not vosk_error_reported:
                    logger.error(f"⚠️ La auto-descarga del modelo rápido Vosk falló.")
                    vosk_error_reported = True
    except ImportError:
        if not vosk_error_reported:
            logger.error("❌ Librería 'vosk' no instalada. El reconocimiento de voz no funcionará.")
            vosk_error_reported = True
        raise  # Re-lanzar para que main() lo capture amigablemente

def listen(model="tiny", language="es", timeout=None, return_audio=False):
    try:
        load_vosk_model(language)
    except:
        return "" # Fallback silencioso si no hay vosk
    
    try:
        import sounddevice as sd
    except ImportError:
        logger.error("❌ Librería 'sounddevice' no instalada.")
        return ""
    if not vosk_recognizer: 
        return (None, None) if return_audio else None
    
    import sounddevice as sd
    import numpy as np
    
    update_ui_state("listening")
    q = queue.Queue()
    audio_buffer = []
    
    def cb(indata, f, t, s): 
        q.put(bytes(indata))
        if return_audio:
            # Convertir buffer raw a numpy array int16 antes de guardar
            audio_buffer.append(np.frombuffer(indata, dtype='int16').copy())
    
    try:
        with sd.RawInputStream(samplerate=16000, blocksize=4000, dtype='int16', channels=1, callback=cb):
            start = time.time()
            while True:
                if timeout and (time.time() - start) > timeout: 
                    return (None, None) if return_audio else None
                
                try:
                    data = q.get(timeout=1)
                except:
                    continue
                    
                if vosk_recognizer.AcceptWaveform(data):
                    res = json.loads(vosk_recognizer.Result()).get("text", "").strip()
                    if res:
                        if return_audio:
                            # Concatenar todos los chunks de audio capturados
                            audio_array = np.concatenate(audio_buffer) if audio_buffer else np.array([], dtype='int16')
                            return (res, audio_array)
                        else:
                            return res
    except Exception as e:
        logger.error(f"Error en listen: {e}")
        return (None, None) if return_audio else None



# --- UTILS FOR main.py ---
def clean_text_for_speech(t): 
    if not t: return ""
    t = t.encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[*_`#\[\](){}>]', '', t).strip()

def trim_response(t, m=300): 
    if not t: return ""
    return (t[:m] + "...") if len(t) > m else t

def clean_input(t): return t.strip().lower() if t else ""

def sleep_now(model, detect_intent_func=None):
    speak(get_idiom("sleep"), model)
    update_ui_state("sleeping")
    while True:
        # Escuchamos usando el idioma base detectado
        audio = listen(language=get_sys_lang())
        if audio and isinstance(audio, str):
            if detect_intent_func:
                intent, conf = detect_intent_func(audio)
                if intent == "wake_up":
                    speak(get_idiom("welcome"), model)
                    return
            
            # Fallback por palabra clave si falla el clasificador o no se provee
            if "fina" in audio.lower():
                speak(get_idiom("welcome"), model)
                return

# --- EMAIL ---
def get_date_n_days_ago(n=7): 
    return (datetime.now() - timedelta(days=n)).strftime("%d-%b-%Y")

def count_recent_unread_emails(i, e, p, d=7):
    try:
        mail = imaplib.IMAP4_SSL(i)
        mail.login(e, p)
        mail.select("inbox")
        _, resp = mail.search(None, f'(UNSEEN SINCE {get_date_n_days_ago(d)})')
        # Usar PEEK para solo contar sin marcar como leído
        nums = resp[0].split()
        count = len(nums)
        mail.logout()
        return count
    except: 
        return 0

def read_recent_unread_emails(i, e, p, d=7, m=5):
    try:
        mail = imaplib.IMAP4_SSL(i)
        mail.login(e, p)
        mail.select("inbox")
        _, resp = mail.search(None, f'(UNSEEN SINCE {get_date_n_days_ago(d)})')
        nums = resp[0].split()
        if not nums: 
            return None
        import email
        # USAR PEEK PARA NO MARCAR COMO LEÍDO
        _, data = mail.fetch(nums[-1], '(BODY.PEEK[])')
        msg = email.message_from_bytes(data[0][1])
        subj = email.header.decode_header(msg["Subject"])[0][0]
        if isinstance(subj, bytes): 
            subj = subj.decode()
        mail.logout()
        return (msg.get("From"), subj, msg.get("Date"), nums)
    except: 
        return None

def send_email(user, pwd, to, subj, body, attachment=None):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subj
        msg['From'] = user
        msg['To'] = to
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s: 
            s.login(user, pwd)
            s.send_message(msg)
        return "Correo enviado."
    except: 
        return "Fallo envío."

def load_contacts():
    try:
        with open(CONTACTS_PATH, "r") as f: return json.load(f)
    except: return {}

# --- WEATHER & NEWS ---
# Helper interno para recuperar config (Scope Global)
def _get_w_conf():
    import json
    try:
        with open(SETTINGS_PATH) as f:
            d = json.load(f)
            return d.get("apis", {}).get("WEATHER_API_KEY"), d.get("apis", {}).get("WEATHER_CITY_ID")
    except: return None, None

def _get_default_weather(lang):
    defaults = {
        "es": {"city": "Buenos Aires", "temp": 20, "desc": "cielo claro"},
        "en": {"city": "Londres", "temp": 20, "desc": "clear sky"},
        "pt": {"city": "Lisboa", "temp": 20, "desc": "céu limpo"},
        "fr": {"city": "Paris", "temp": 20, "desc": "ciel dégagé"},
        "de": {"city": "Berlin", "temp": 20, "desc": "klarer Himmel"},
        "ja": {"city": "Tokio", "temp": 20, "desc": "快晴"},
        "zh": {"city": "Pekin", "temp": 20, "desc": "晴空"}
    }
    data = defaults.get(lang, defaults["es"])
    if lang == 'en':
        return f"In {data['city']} the temperature is {data['temp']} degrees, with {data['desc']}."
    elif lang == 'pt':
        return f"Em {data['city']} a temperatura é de {data['temp']} graus, com {data['desc']}."
    return f"En {data['city']} la temperatura es de {data['temp']} grados, con {data['desc']}."

async def get_weather(city=None):
    import aiohttp
    import json
    
    api_key, city_id = _get_w_conf()
    lang = get_sys_lang()
    
    if not api_key: 
        return _get_default_weather(lang)
    
    if city:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang={lang}"
    elif city_id:
        url = f"http://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={api_key}&units=metric&lang={lang}"
    else:
        return _get_default_weather(lang)

    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=3) as r: 
                if r.status != 200: return _get_default_weather(lang)
                d = await r.json()
                temp = d['main']['temp']
                desc = d['weather'][0]['description']
                name = d.get('name', i18n('val_your_city', 'tu ciudad'))
                
                # ACTUALIZACIÓN PROACTIVA DE UI: Para que aparezca en el widget sin esperar
                weather_payload = {
                    "temp": int(temp),
                    "desc": desc.capitalize(),
                    "city": name,
                    "code": d['weather'][0]['id'],
                    "humidity": d['main']['humidity'],
                    "wind": int(d.get('wind', {}).get('speed', 0) * 3.6),
                    "feels_like": int(d['main'].get('feels_like', temp))
                }
                update_ui_state("idle", extra_payload={"weather_data": weather_payload})

                if lang == 'en':
                    return f"In {name} the temperature is {int(temp)} degrees, with {desc}."
                return f"En {name} la temperatura es de {int(temp)} grados, con {desc}."
    except Exception as e: 
        print(f"Weather error: {e}")
        return _get_default_weather(lang)

def _get_default_forecast(lang):
    defaults = {
        "es": {"desc": "cielo claro"}, "en": {"desc": "clear skies"},
        "pt": {"desc": "céu limpo"}, "fr": {"desc": "ciel dégagé"},
        "de": {"desc": "klarer Himmel"}, "ja": {"desc": "快晴"}, "zh": {"desc": "晴空"}
    }
    data = defaults.get(lang, defaults["es"])
    if lang == 'en': return f"Tomorrow expects {data['desc']}, with a temperature of about 20 degrees."
    elif lang == 'pt': return f"Amanhã espera-se {data['desc']}, com uma temperatura de cerca de 20 graus."
    return f"Mañana se espera {data['desc']}, con una temperatura de unos 20 grados."

async def get_weather_tomorrow(city=None): 
    import aiohttp
    api_key, city_id = _get_w_conf()
    lang = get_sys_lang()
    if not api_key or not city_id: return _get_default_forecast(lang)
    
    url = f"https://api.openweathermap.org/data/2.5/forecast?id={city_id}&appid={api_key}&units=metric&lang={lang}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=3) as r:
                if r.status != 200: return _get_default_forecast(lang)
                d = await r.json()
                if "list" in d and len(d["list"]) > 8:
                    tom = d["list"][8]
                    temp = tom["main"]["temp"]
                    desc = tom["weather"][0]["description"]
                    if lang == 'en':
                        return f"Tomorrow expects {desc}, with a temperature of about {int(temp)} degrees."
                    return f"Mañana se espera {desc}, con una temperatura de unos {int(temp)} grados."
                return _get_default_forecast(lang)
    except Exception as e:
        print(f"Forecast error: {e}")
        return _get_default_forecast(lang)

async def when_will_rain(city=None): 
    return i18n("msg_rain_no_data", "No tengo datos de lluvia por ahora.")

async def get_top_news(api_key): 
    # Fallback to proactive briefing
    return get_proactive_briefing()

async def get_weather_forecast(c): 
    return await get_weather_tomorrow(c)


# --- SYSTEM & CONTROL ---
def shutdown(model): 
    speak(i18n("msg_shutdown", "Apagando el sistema."), model)
    time.sleep(1)
    subprocess.run("poweroff", shell=True)

def reboot(model):
    speak(i18n("msg_reboot", "Reiniciando el sistema."), model)
    time.sleep(1)
    subprocess.run("reboot", shell=True)

def suspend(model):
    speak(i18n("msg_suspend", "Suspendiendo el sistema."), model)
    time.sleep(1)
    subprocess.run("systemctl suspend", shell=True)

def update(): 
    speak("Actualizando.", "Aldo (M): Español")
    subprocess.run("sudo pacman -Syu --noconfirm", shell=True)

def get_ip(): 
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return socket.gethostbyname(socket.gethostname())

def get_battery_status():
    import psutil
    b = psutil.sensors_battery()
    return (b.percent, "Cargando" if b.power_plugged else "Descargando") if b else (0, "N/A")

def get_system_stats(): 
    import psutil
    return f"CPU: {psutil.cpu_percent()}%, RAM: {psutil.virtual_memory().percent}%"

def get_uptime(): 
    return "Activo."

def get_current_datetime(): 
    now = datetime.now()
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    dia_nombre = dias[now.weekday()]
    mes_nombre = meses[now.month - 1]
    
    return now.strftime(f"Hoy es {dia_nombre} %d de {mes_nombre}. Son las %I:%M %p")

def restart_fina(): 
    os.execv(sys.executable, ['python3'] + sys.argv)

def open_app(n):
    if shutil.which(n): 
        subprocess.Popen([n], stdout=subprocess.DEVNULL)
        return f"Abriendo {n}."
    return "No encontrado."

def close_app(n):
    import psutil
    for p in psutil.process_iter(['name']):
        if n.lower() in p.info['name'].lower(): 
            p.terminate()
            return f"Cerrado {n}."
    return "No encontrado."

def change_wallpaper(m): 
    if _run_system_script("wallpaper_selector.sh", "select"): return "Cambiando fondo."
    return "No pude cambiar el fondo."

def web_search(q): 
    if not q:
        return "No escuché ningún término de búsqueda.", None
    try:
        # Intentamos abrir Google Chrome
        subprocess.Popen(["google-chrome", f"https://www.google.com/search?q={q}"])
        return f"Buscando {q} en Google.", f"https://www.google.com/search?q={q}"
    except Exception as e:
        logger.error(f"Error en web_search: {e}")
        # Intento de rescate con xdg-open si falla chrome
        try:
            import subprocess as _sp
            _sp.Popen(["xdg-open", f"https://www.google.com/search?q={q}"])
            return f"Buscando {q}.", f"https://www.google.com/search?q={q}"
        except:
            return "No pude abrir el navegador.", None


# --- LOCAL SCRIPTS ---
def _run_system_script(script_name, arg):
    """Ejecuta un script de sistema buscando en varias ubicaciones."""
    posibles = [
        os.path.join(ERGEN_ROOT, "scripts", script_name),
        os.path.join(ERGEN_ROOT, "plugins", "system", "scripts", script_name)
    ]
    
    script_path = None
    for p in posibles:
        if os.path.exists(p):
            script_path = p
            break
            
    if not script_path:
        logger.error(f"No se encontró el script de sistema: {script_name}")
        return False

    try:
        # Timeout de 5s para evitar bloqueos
        subprocess.run([script_path, arg], timeout=5, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logger.error(f"Error ejecutando {script_name} {arg}: {e}")
        return False

def increase_volume(): 
    if _run_system_script("volume_control.sh", "up"): return "Subiendo volumen."
    return "No pude subir el volumen."

def decrease_volume(): 
    if _run_system_script("volume_control.sh", "down"): return "Bajando volumen."
    return "No pude bajar el volumen."

def increase_brightness(): 
    if _run_system_script("brightness_control.sh", "up"): return "Subiendo brillo."
    return "No pude subir el brillo."

def decrease_brightness(): 
    if _run_system_script("brightness_control.sh", "down"): return "Bajando el brillo."
    return "No pude bajar el brillo."

def take_screenshot(): 
    if _run_system_script("screenshot.sh", ""): return "Captura de pantalla realizada."
    return "No pude tomar la captura."

# --- MUSIC ---
def play_music(m): subprocess.run(["audtool", "playback-play"])
def stop_music(m): subprocess.run(["audtool", "playback-stop"])
def pause_music(m): subprocess.run(["audtool", "playback-pause"])
def next_track(m): subprocess.run(["audtool", "playlist-advance"])
def music_volume_up(m): subprocess.run(["audtool", "set-volume", "100"])
def music_volume_down(m): subprocess.run(["audtool", "set-volume", "20"])

# --- TV ---
def _check_tv_deps(m=None):
    try:
        import androidtvremote2
        import pychromecast
        return True
    except ImportError:
        if m: speak("Para controlar la televisión, debes instalar las dependencias de su módulo desde la carpeta plugins.", m)
        return False

def _send_adb_key(k):
    if not _check_tv_deps(): return
    ip = get_unified_config("TV_IP", "0.0.0.0")
    if ip == "0.0.0.0": return
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', str(k)], timeout=2)

# --- AIR CONDITIONING (UNIVERSAL) ---
def _get_ac_plugin_path():
    try:
        from plugin_manager import PluginManager
        from pathlib import Path
        pm = PluginManager()
        pm.discover_plugins()
        for name, path in pm._plugins_paths.items():
            if (Path(path) / "clima.py").exists():
                return str(path)
    except Exception as e:
        print(f"Error buscando plugin de AC: {e}")
    return None

async def perform_ac_control(m, command):
    path = _get_ac_plugin_path()
    if not path:
        speak("No encontré ningún plugin de aire acondicionado instalado.", m)
        return

    script = os.path.join(path, "clima.py")
    cmd_lower = command.lower()
    args = [sys.executable, script]

    # Lógica de mapeo universal basada en MARKET_PLUGIN_STANDARDS
    if "apaga" in cmd_lower or "off" in cmd_lower:
        args += ["--power", "off"]
        msg = "Apagando el aire acondicionado."
    elif "encende" in cmd_lower or "enciende" in cmd_lower or "prende" in cmd_lower or "on" in cmd_lower:
        args += ["--power", "on"]
        msg = "Encendiendo el aire acondicionado."
    
    # Temperatura
    nums = re.findall(r'\d+', cmd_lower)
    if nums:
        temp = nums[0]
        args += ["--temp", temp]
        if "--power" not in args: args += ["--power", "on"]
        msg = f"Ajustando el aire a {temp} grados."
    
    # Modos
    if "turbo" in cmd_lower: args += ["--turbo", "on"]
    if "eco" in cmd_lower: args += ["--mode", "auto"]
    if "frío" in cmd_lower or "frio" in cmd_lower: args += ["--mode", "cool"]
    if "calor" in cmd_lower: args += ["--mode", "heat"]

    try:
        # Ejecutar en segundo plano
        subprocess.Popen(args + ["--silent"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        speak(msg if 'msg' in locals() else "Comando de aire acondicionado enviado.", m)
    except Exception as e:
        print(f"Error ejecutando clima.py: {e}")
        speak("Hubo un error al intentar controlar el aire acondicionado.", m)

def turn_on_tv(m, command=""):
    if not _check_tv_deps(m): return
    plugin = _get_tv_plugin(m)
    if not plugin: return
    
    # Si no hay comando, usar default
    cmd_text = command if command else "enciende la tele"
    
    try:
        response = plugin.handle_intent("tv_on", cmd_text)
        if response:
             speak(response, m)
    except Exception as e:
        print(f"Error en turn_on_tv con plugin: {e}")
        speak("Hubo un error al intentar encender la televisión.", m)

def turn_off_tv(m, command=""):
    if not _check_tv_deps(m): return
    plugin = _get_tv_plugin(m)
    if not plugin: return
    
    cmd_text = command if command else "apaga la tele"
    
    try:
        response = plugin.handle_intent("tv_off", cmd_text)
        if response:
             speak(response, m)
    except Exception as e:
        print(f"Error en turn_off_tv con plugin: {e}")
        speak("Hubo un error al intentar apagar la televisión.", m)

def tv_volume_up_cmd(m, s=5): 
    if not _check_tv_deps(m): return
    plugin = _get_tv_plugin(m)
    if not plugin: return
    try:
        # Loop for precision steps
        for _ in range(s):
            plugin.handle_intent("tv_volume_up", "sube el volumen")
        speak(f"Subiendo volumen {s} puntos.", m)
    except Exception as e:
        print(f"Error en tv_volume_up_cmd con plugin: {e}")
        speak("Hubo un error al intentar subir el volumen.", m)

def tv_volume_down_cmd(m, s=5): 
    if not _check_tv_deps(m): return
    plugin = _get_tv_plugin(m)
    if not plugin: return
    try:
        for _ in range(s):
            plugin.handle_intent("tv_volume_down", "baja el volumen")
        speak(f"Bajando volumen {s} puntos.", m)
    except Exception as e:
        print(f"Error en tv_volume_down_cmd con plugin: {e}")
        speak("Hubo un error al intentar bajar el volumen.", m)

def tv_mute_cmd(m, action="mute"): 
    if not _check_tv_deps(m): return
    feedback = "Silenciando televisión..." if action == "mute" else "Quitando silencio..."
    speak(feedback, m)
    plugin = _get_tv_plugin(m)
    if not plugin: return
    
    try:
        # Delegamos al plugin robusto (V888) passing STRING not DICT
        response = plugin.handle_intent("tv_mute", "silencia la televisión")
        # No repetimos el response del plugin para no sobrecargar el audio
    except Exception as e:
        print(f"Error en tv_mute_cmd con plugin: {e}")
        speak("Hubo un error al intentar controlar el silencio.", m)

def tv_channel_up_cmd(m): 
    if not _check_tv_deps(m): return
    plugin = _get_tv_plugin(m)
    if not plugin: return
    try:
        response = plugin.handle_intent("tv_channel_up", "cambia al siguiente canal")
        if response:
             speak(response, m)
    except Exception as e:
        print(f"Error en tv_channel_up_cmd con plugin: {e}")
        speak("Hubo un error al intentar cambiar al siguiente canal.", m)

def tv_channel_down_cmd(m): 
    if not _check_tv_deps(m): return
    plugin = _get_tv_plugin(m)
    if not plugin: return
    try:
        response = plugin.handle_intent("tv_channel_down", "cambia al canal anterior")
        if response:
             speak(response, m)
    except Exception as e:
        print(f"Error en tv_channel_down_cmd con plugin: {e}")
        speak("Hubo un error al intentar cambiar al canal anterior.", m)

def _get_tv_plugin_path():
    try:
        from plugin_manager import PluginManager
        from pathlib import Path
        pm = PluginManager()
        pm.discover_plugins()
        target_plugin = "tcl32s60a"
        if target_plugin not in pm._plugins_paths:
            for name, path in pm._plugins_paths.items():
                if (Path(path) / "tv.py").exists():
                    return str(path)
        else:
            return str(pm._plugins_paths[target_plugin])
    except: pass
    return None

def _get_tv_plugin(m=None):
    if not _check_tv_deps(m): return None
    path = _get_tv_plugin_path()
    if path:
        import importlib.util
        try:
            spec = importlib.util.spec_from_file_location("dynamic_tv_plugin", os.path.join(path, "tv.py"))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'TVPlugin'):
                    return module.TVPlugin(None)
        except Exception as e:
            print(f"Error cargando plugin de TV: {e}")
    
    if m: speak("No se encontró el plugin de televisión.", m)
    return None

def tv_set_channel_cmd(c, m): 
    plugin = _get_tv_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("tv_set_channel", f"pon el canal {c}")
    if response: speak(response, m)

def tv_set_input_cmd(i, m): 
    plugin = _get_tv_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("tv_set_input", f"pon la entrada {i}")
    if response: speak(response, m)

def tv_set_volume_cmd(v, m):
    plugin = _get_tv_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("tv_set_volume", f"volumen {v}")
    if response: speak(response, m)

def tv_open_app_cmd(a, m): 
    plugin = _get_tv_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("tv_open_app", f"abre {a}")
    if response: speak(response, m)
def tv_exit_app_cmd(m): 
    if not _check_tv_deps(m): return
    _send_adb_key(3)

# --- DECO (UNIVERSAL PLUGIN WRAPPER) ---
def deco_set_channel_cmd(c, m):
    plugin = _get_deco_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("deco_set_channel", f"pon el canal {c}")
    if response: speak(response, m)

def deco_volume_up_cmd(m, steps=5):
    plugin = _get_deco_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("deco_volume_up", f"subir {steps}")
    if response: speak(response, m)

def deco_volume_down_cmd(m, steps=5):
    plugin = _get_deco_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("deco_volume_down", f"bajar {steps}")
    if response: speak(response, m)

def deco_mute_cmd(m):
    plugin = _get_deco_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("deco_mute", "silencio")
    if response: speak(response, m)

def deco_set_volume_cmd(vol, m):
    plugin = _get_deco_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("deco_set_volume", f"volumen {vol}")
    if response: speak(response, m)

def deco_open_app_cmd(app, m):
    plugin = _get_deco_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("deco_open_app", f"abrir {app}")
    if response: speak(response, m)

def deco_exit_app_cmd(m):
    plugin = _get_deco_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("deco_exit_app", "salir")
    if response: speak(response, m)

def deco_set_input_cmd(inp, m):
    plugin = _get_deco_plugin(m)
    if not plugin: return
    response = plugin.handle_intent("deco_set_input", f"entrada {inp}")
    if response: speak(response, m)

def _get_deco_plugin_path():
    try:
        from plugin_manager import PluginManager
        from pathlib import Path
        import yaml
        pm = PluginManager()
        pm.discover_plugins()
        for name, path in pm._plugins_paths.items():
            yaml_path = Path(path) / "plugin.yaml"
            if yaml_path.exists():
                with open(yaml_path, "r") as f:
                    conf = yaml.safe_load(f)
                    if conf.get("category") == "Decos":
                        return str(path)
    except: pass
    return None

def _get_deco_plugin(m=None):
    path = _get_deco_plugin_path()
    if path:
        import importlib.util
        try:
            script = os.path.join(path, "deco.py")
            spec = importlib.util.spec_from_file_location("dynamic_deco_plugin", script)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                for attr in dir(module):
                    if attr.endswith("Plugin"):
                        return getattr(module, attr)(None)
        except Exception as e:
            print(f"Error cargando plugin de Deco: {e}")
    if m: speak("No se encontró el plugin de decodificador.", m)
    return None
def is_tv_on(): 
    """Verifica si la TV principal está conectada via ADB"""
    ip = get_unified_config("TV_IP")
    if not ip or ip == "0.0.0.0": return False
    try:
        # Usamos timeout muy corto para no bloquear el inicio
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=1.5)
        for line in result.stdout.split('\n'):
            if ip in line and 'device' in line and 'offline' not in line:
                return True
    except: pass
    return False

def ensure_tv_is_on(m): 
    if not is_tv_on():
        turn_on_tv(m)
    return True

# --- AI & TOOLS ---
async def get_mistral_response(prompt):
    import aiohttp
    github_token = get_unified_config("GITHUB_TOKEN")
    if not github_token: return "No tengo token de GitHub configurado para la IA."
    url = "https://models.inference.ai.azure.com/chat/completions"
    headers = {"Authorization": f"Bearer {github_token}", "Content-Type": "application/json"}
    payload = {
        "model": "Codestral-2501",
        "messages": [
            {"role": "system", "content": "Eres Fina. Responde en español."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                d = await response.json()
                return d["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Error IA: {e}")
        return "Error conectando con la IA."

async def handle_unknown_request(c, m): 
    return await get_mistral_response(c)

def wiki_summary(q, s=2):
    import wikipedia
    wikipedia.set_lang("es")
    try: 
        return wikipedia.summary(q, sentences=s)
    except Exception as e: 
        logger.debug(f"Wiki no encontró {q}: {e}")
        return "No encontrado."

def tell_joke(): 
    import pyjokes
    return pyjokes.get_joke(language="es", category="all")

def translate_text(t, d="en"):
    from deep_translator import GoogleTranslator
    try: 
        return GoogleTranslator(source='auto', target=d).translate(t)
    except: 
        return "Error traducción."


# --- REAL IMPLEMENTATIONS OF TOOLS ---

def _get_data_file():
    target = USER_DATA_PATH
    if not os.path.exists(target):
        with open(target, "w") as f: json.dump({"notes": [], "reminders": []}, f)
    return target

def create_note(content):
    if not content: return "Nota vacía."
    f = _get_data_file()
    try:
        with open(f, "r") as file: data = json.load(file)
        data["notes"].append({"content": content, "timestamp": str(datetime.now())})
        with open(f, "w") as file: json.dump(data, file, indent=2)
        return "Nota guardada correctamente."
    except Exception as e:
        return f"Error guardando nota: {e}"

def add_reminder(task, time_str, m):
    # Por ahora solo guardamos el texto, el scheduler es otro tema
    f = _get_data_file()
    try:
        with open(f, "r") as file: data = json.load(file)
        data["reminders"].append({"task": task, "time": time_str, "active": True})
        with open(f, "w") as file: json.dump(data, file, indent=2)
        return f"Recordatorio agendado: {task} a las {time_str}"
    except:
        return "Error creando recordatorio."

def list_reminders():
    f = _get_data_file()
    try:
        with open(f, "r") as file: data = json.load(file)
        reminders = [f"- {r['task']} ({r['time']})" for r in data.get("reminders", []) if r.get("active")]
        if not reminders: return "No tienes recordatorios pendientes."
        return "Tus recordatorios:\n" + "\n".join(reminders)
    except:
        return "No pude leer los recordatorios."

def backup_files():
    """Crea un backup real del proyecto"""
    import shutil
    try:
        backup_dir = os.path.expanduser("~/Fina_Backups")
        os.makedirs(backup_dir, exist_ok=True)
        filename = f"fina_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.make_archive(os.path.join(backup_dir, filename), 'zip', ERGEN_ROOT)
        return f"Copia de seguridad creada en {backup_dir}/{filename}.zip"
    except Exception as e:
        return f"Error en backup: {e}"

def get_public_ip():
    try:
        import requests
        return requests.get('https://api.ipify.org', timeout=3).text
    except:
        return "No pude obtener la IP pública."

def scan_wifi():
    # Requiere permisos, intentamos nmcli si está disponible
    try:
        r = subprocess.run(["nmcli", "-f", "SSID,BARS", "dev", "wifi"], capture_output=True, text=True)
        if r.returncode == 0:
            lines = r.stdout.split('\n')[:5] # Top 5
            return "Redes WiFi cercanas:\n" + "\n".join([l.strip() for l in lines if l.strip()])
        return "No pude escanear redes WiFi (falta nmcli o permisos)."
    except:
        return "Error escaneando WiFi."

def text_to_number_es(text):
    """Convierte números en palabras (español) a enteros"""
    text = text.lower().strip()
    dict_nums = {
        "cero": 0, "un": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
        "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
        "once": 11, "doce": 12, "trece": 13, "catorce": 14, "quince": 15,
        "dieciséis": 16, "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20,
        "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60,
        "setenta": 70, "ochenta": 80, "noventa": 90, "cien": 100, "ciento": 100,
        "doscientos": 200, "trescientos": 300, "cuatrocientos": 400, "quinientos": 500,
        "seiscientos": 600, "setecientos": 700, "ochocientos": 800, "novecientos": 900,
        "mil": 1000
    }
    
    # Intento de parseo directo
    if text in dict_nums: return dict_nums[text]
    
    # Para números compuestos (ej: "veinte y cinco")
    total = 0
    words = text.replace(" y ", " ").split()
    for w in words:
        if w in dict_nums:
            total += dict_nums[w]
        elif w.isdigit():
            total += int(w)
            
    return total if total > 0 else None

# Placeholder real para funciones costosas o no implementadas
def run_schedule_loop(*args, **kwargs): pass

def get_doorbell_status_cmd(*args, **kwargs): return "Sistema de timbre no conectado aún."
def show_doorbell_image(*args, **kwargs): pass
def show_doorbell_stream(*args, **kwargs): pass
def play_youtube(q=""): 
    subprocess.Popen(["xdg-open", f"https://www.youtube.com/results?search_query={q}"])
    return f"Buscando {q} en YouTube..."

def find_file(name):
    try:
        # Búsqueda real en home (limitada a 2 niveles para rapidez)
        cmd = ["find", os.path.expanduser("~"), "-maxdepth", "3", "-name", f"*{name}*"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        found = res.stdout.strip().split('\n')
        if found and found[0]:
            return f"Encontré: {found[0]}"
        return "No encontré el archivo."
    except:
        return "Error buscando archivo."

def get_clipboard():
    """Lee el portapapeles soportando X11 (xclip) y Wayland (wl-paste)"""
    try:
        # Intento 1: X11 con xclip
        res = subprocess.run(["xclip", "-o", "-selection", "clipboard"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0: return res.stdout
    except:
        pass

    try:
        # Intento 2: Wayland con wl-clipboard
        res = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0: return res.stdout
    except:
        pass

    return "Portapapeles vacío o inaccesible (asegúrate de tener xclip o wl-clipboard instalado)."

# --- REAL IMPLEMENTATIONS OF TOOLS (part 2) ---

def start_timer(minutes, message="¡Tiempo cumplido!", m=None):
    import threading
    
    val = float(minutes)
    sec_total = int(val * 60)
    
    # Formatear mensaje para UI (process text)
    if val < 1:
        display_text = f"TEMPORIZADOR: {sec_total} SEG"
    elif val == int(val):
        display_text = f"TEMPORIZADOR: {int(val)} MIN"
    else:
        display_text = f"TEMPORIZADOR: {val:.1f} MIN"

    # Notificar a la UI para mostrar el reloj visual
    # Enviar duración en SEGUNDOS siempre para el timer visual
    display_text = f"TEMPORIZADOR: {display_text.split(': ')[1]}"

    # Notificar a la UI para mostrar el reloj visual
    # Agregamos timestamp ID para que el frontend distinga nuevos timers
    timer_payload = {
        "duration": sec_total, 
        "label": message,
        "id": time.time()  # UNIQUE ID CRÍTICO
    }
    update_ui_state("listening", process=display_text, extra_payload={"timer": timer_payload})

    def _notify():
        speak(f"⏰ {message}", m)
        # Limpiar UI
        update_ui_state("listening", process="SISTEMA LISTO", extra_payload={"timer": None})
    
    t = threading.Timer(sec_total, _notify)
    t.start()
    return f"Temporizador iniciado en {display_text.split(': ')[1]}."

async def convert_currency(amount, from_curr, to_curr):
    import aiohttp
    try:
        # Usamos una API gratuita sin key (exchangerate-api base)
        url = f"https://api.exchangerate-api.com/v4/latest/{from_curr.upper()}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                rate = data["rates"].get(to_curr.upper())
                if rate:
                    total = amount * rate
                    return f"{amount} {from_curr} son {total:.2f} {to_curr}."
                return "Moneda no encontrada."
    except:
        return "Servicio de moneda no disponible."

async def generate_image(prompt, m=None):
    openai_key = get_unified_config("OPENAI_API_KEY")
    if not openai_key: return "No tengo clave de OpenAI configurada."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        url = response.data[0].url
        subprocess.run(["xdg-open", url])
        return "Imagen generada y abierta en navegador."
    except Exception as e:
        return f"Error generando imagen: {e}"

def read_pdf(path):
    try:
        import pypdf
        reader = pypdf.PdfReader(path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text[:2000] + "..." # Limitamos para no saturar TTS
    except ImportError:
        return "Instala 'pypdf' para leer PDFs."
    except:
        return "Error leyendo el PDF."

def scan_ports(host):
    # Escaneo rápido de puertos comunes
    common_ports = [21, 22, 80, 443, 8080, 3306]
    open_ports = []
    try:
        for port in common_ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((host, port)) == 0:
                open_ports.append(str(port))
            s.close()
        
        if open_ports: return f"Puertos abiertos en {host}: {', '.join(open_ports)}"
        return f"No encontré puertos comunes abiertos en {host}."
    except:
        return "Error escaneando."

def get_proactive_briefing(m=None):
    """Obtiene noticias de Google News RSS (Argentina) sin librerías externas pesadas"""
    try:
        import requests
        import xml.etree.ElementTree as ET
        
        url = "https://news.google.com/rss?hl=es-419&gl=AR&ceid=AR:es-419"
        timeout_val = 3.0
        
        response = requests.get(url, timeout=timeout_val)
        if response.status_code != 200:
            return "No pude conectar con el servicio de noticias."
            
        root = ET.fromstring(response.content)
        # Buscar items
        items = root.findall(".//item")
        
        headlines = []
        # Tomar 3 titulares limpios
        count = 0
        for item in items:
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                title = title_el.text
                # Limpiar nombre del medio (ej: " - Clarín")
                if " - " in title:
                    title = title.rsplit(" - ", 1)[0]
                headlines.append(title)
                count += 1
            if count >= 3: break
            
        if not headlines:
            return "No encontré titulares recientes."
            
        return "Aquí están las noticias: " + ". ".join(headlines) + "."
        
    except Exception as e:
        print(f"Error noticias: {e}")
        return "Hubo un error al obtener las noticias."

def save_voice_note(text): return create_note(f"[VOZ] {text}")

def get_daily_affirmation(*args, **kwargs):
    import random
    affirmations = [
        "Soy capaz de lograr todo lo que me proponga hoy.",
        "Mi potencial es ilimitado y mi voluntad es de hierro.",
        "Cada desafío es una oportunidad para crecer.",
        "Confío en mi intuición y tomo decisiones sabias.",
        "Merezco ser feliz y tener éxito en mis proyectos.",
        "Hoy elijo ser la mejor versión de mí mismo.",
        "Mi energía es positiva y contagia a los que me rodean.",
        "Tengo el control de mis pensamientos y de mi destino."
    ]
    return random.choice(affirmations)

def toggle_battery_saver(m, state="on"):
    """Activa/Desactiva ahorro de energía en Linux (GNOME/KDE/Generic)"""
    try:
        profile = "power-saver" if state == "on" else "balanced"
        subprocess.run(["powerprofilesctl", "set", profile], check=True)
        return f"Modo {profile} activado."
    except:
        return i18n("msg_feature_not_supported", "Función no soportada en este sistema.")

def play_ambient_sound(m, type_="lluvia"):
    """Reproduce sonidos relajantes desde streams estables"""
    streams = {
        "lluvia": "https://stream.zeno.fm/0r0xa792kwzuv", # Lofi/Rain
        "bosque": "https://ais-sa2.cdnstream1.com/2214_128.mp3",
        "oceano": "https://stream.zeno.fm/6n76h792kwzuv",
        "naturaleza": "https://ais-sa2.cdnstream1.com/2214_128.mp3"
    }
    url = streams.get(type_.lower(), streams["lluvia"])
    try:
        # Usar mpv en segundo plano para el stream
        subprocess.Popen(["mpv", "--no-video", "--volume=60", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        speak(f"Reproduciendo sonido de {type_}.", m)
    except:
        speak("No pude iniciar el sonido ambiental. Verifica que mpv esté instalado.", m)

def take_webcam_photo(m, *args, **kwargs):
    """Captura una foto usando ffmpeg"""
    try:
        photo_path = os.path.join(os.path.expanduser("~"), "Imágenes", f"fina_foto_{int(time.time())}.jpg")
        os.makedirs(os.path.dirname(photo_path), exist_ok=True)
        # Comando universal con ffmpeg
        cmd = ["ffmpeg", "-f", "v4l2", "-video_size", "1280x720", "-i", "/dev/video0", "-frames:v", "1", photo_path, "-y"]
        subprocess.run(cmd, capture_output=True, timeout=5)
        if os.path.exists(photo_path):
            return f"Foto guardada en {photo_path}", photo_path
        return "No se pudo detectar la cámara.", ""
    except Exception as e:
        logger.error(f"Error cámara: {e}")
        return "Error al acceder a la cámara.", ""

def download_instagram_reel(m, url):
    """Descarga Reels usando yt-dlp"""
    try:
        download_dir = os.path.join(os.path.expanduser("~"), "Descargas")
        os.makedirs(download_dir, exist_ok=True)
        output_template = os.path.join(download_dir, "%(title)s.%(ext)s")
        
        speak("Iniciando descarga del Reel, esto puede tardar un momento.", m)
        cmd = ["yt-dlp", "-o", output_template, "--no-playlist", url]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if res.returncode == 0:
            return "¡Listo! El Reel ha sido guardado en tu carpeta de Descargas."
        return "Hubo un error al descargar el Reel. Verifica el enlace."
    except:
        return "Fallo crítico en el motor de descarga."

def convert_md_to_html(content, *args, **kwargs):
    # Intentar usar markdown2 si está disponible
    try:
        import markdown2
        return markdown2.markdown(content)
    except:
        return f"<pre>{content}</pre>"

def generate_password(length=16, *args, **kwargs):
    import string
    import secrets
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def check_linux_updates(m, *args, **kwargs):
    try:
        res = subprocess.run(["checkupdates"], capture_output=True, text=True) # Arch
        if not res.stdout:
            res = subprocess.run(["apt-get", "-s", "upgrade"], capture_output=True, text=True) # Debian/Ubuntu
        
        updates = len(res.stdout.splitlines())
        if updates > 0:
            return f"Tienes {updates} paquetes pendientes de actualizar."
        return "Tu sistema está al día."
    except:
        return "No pude verificar las actualizaciones."

def toggle_night_mode(m, state="on"):
    try:
        if state == "on":
            subprocess.Popen(["redshift", "-O", "3500"], stdout=subprocess.DEVNULL)
        else:
            subprocess.run(["redshift", "-x"])
        return f"Modo noche {state}."
    except:
        return "Redshift no está instalado."

def update_assistant_code(m, *args, **kwargs):
    """Pull universal de cambios desde git"""
    try:
        speak("Buscando actualizaciones en el repositorio...", m)
        res = subprocess.run(["git", "pull"], capture_output=True, text=True, timeout=30)
        if "Already up to date" in res.stdout:
            return "Fina ya está en su versión más reciente."
        return "Actualización completada. Reinicia Fina para aplicar los cambios."
    except:
        return "Error al conectar con el servidor de actualizaciones."

def get_weather_forecast(m, *args, **kwargs):
    # Reutilizar lógica de get_weather pero para forecast
    return "Función de pronóstico extendido en desarrollo."

def scan_network_cmd(m):
    """Llama al escáner de red y reporta dispositivos encontrados"""
    try:
        from iot.network_scan import scan_network
        speak("Iniciando escaneo de red. Esto tomará unos segundos...", m)
        devices = scan_network()
        if not devices:
            speak("No se detectaron dispositivos adicionales en la red.", m)
            return
        
        # Filtrar conocidos (que no sean Desconocidos o ?)
        conocidos = [d for d in devices if d['vendor'] != "Desconocido"]
        if conocidos:
            msg = f"He encontrado {len(conocidos)} dispositivos conocidos: "
            vendors = list(set([d['vendor'] for d in conocidos]))
            msg += ", ".join(vendors) + "."
            speak(msg, m)
        else:
            speak(f"Escaneo finalizado. Detecté {len(devices)} dispositivos conectados, pero no pude identificar sus marcas.", m)
    except Exception as e:
        logger.error(f"Error en scan_network_cmd: {e}")
        speak("Hubo un error al intentar escanear la red.", m)

def robot_clean_cmd(m):
    """Busca un plugin de categoría 'Robots' o 'Appliances'"""
    # Lógica universal de plugins
    plugin = _get_plugin_by_category("Robots") or _get_plugin_by_category("Appliances")
    if plugin:
        response = plugin.handle_intent("robot_clean", "limpiar")
        if response: speak(response, m)
    else:
        speak("No encontré ningún robot aspirador vinculado.", m)

def lights_on_cmd(m):
    plugin = _get_plugin_by_category("Lights") or _get_plugin_by_category("SmartHome")
    if plugin:
        response = plugin.handle_intent("lights_on", "prender luces")
        if response: speak(response, m)
    else:
        speak("No detecté luces inteligentes configuradas.", m)

def lights_off_cmd(m):
    plugin = _get_plugin_by_category("Lights") or _get_plugin_by_category("SmartHome")
    if plugin:
        response = plugin.handle_intent("lights_off", "apagar luces")
        if response: speak(response, m)
    else:
        speak("No puedo apagar las luces si no hay un plugin activo.", m)

def lock_door_cmd(m):
    plugin = _get_plugin_by_category("Locks") or _get_plugin_by_category("Doors")
    if plugin:
        response = plugin.handle_intent("lock_door", "cerrar llave")
        if response: speak(response, m)
    else:
        speak("No detecto ninguna cerradura inteligente configurada.", m)

def unlock_door_cmd(m):
    plugin = _get_plugin_by_category("Locks") or _get_plugin_by_category("Doors")
    if plugin:
        response = plugin.handle_intent("unlock_door", "abrir llave")
        if response: speak(response, m)
    else:
        speak("Cerradura no encontrada.", m)

def blinds_open_cmd(m):
    plugin = _get_plugin_by_category("Blinds")
    if plugin:
        response = plugin.handle_intent("blinds_open", "abrir persianas")
        if response: speak(response, m)
    else:
        speak("Persianas no configuradas en el sistema.", m)

def start_watering_cmd(m):
    plugin = _get_plugin_by_category("Irrigation")
    if plugin:
        response = plugin.handle_intent("start_watering", "regar")
        if response: speak(response, m)
    else:
        speak("No hay un sistema de riego registrado.", m)

def check_solar_production_cmd(m):
    plugin = _get_plugin_by_category("Energy")
    if plugin:
        response = plugin.handle_intent("check_solar_production", "cuanta energia")
        if response: speak(response, m)
    else:
        speak("Inversor solar no detectado.", m)

def fridge_status_cmd(m):
    plugin = _get_plugin_by_category("Refrigerators") or _get_plugin_by_category("Appliances")
    if plugin:
        response = plugin.handle_intent("fridge_status", "estado heladera")
        if response: speak(response, m)
    else:
        speak("No encontré una heladera inteligente vinculada.", m)

def _get_plugin_by_category(category):
    """Busca un plugin en el market que pertenezca a una categoría"""
    import yaml
    market_path = os.path.join(PROJECT_ROOT, ".local_lab", "Fina-Plugins-Market-Working")
    for root, dirs, files in os.walk(market_path):
        if "plugin.yaml" in files:
            try:
                with open(os.path.join(root, "plugin.yaml"), 'r') as f:
                    data = yaml.safe_load(f)
                    if data.get("category") == category:
                        # Cargar el plugin (asumiendo que tiene plugin.py o similar)
                        # Por ahora usamos la lógica de carga dinámica similar a TV/Deco
                        # Pero simplificada para este caso
                        return _load_dynamic_plugin(root)
            except: pass
    return None

def _load_dynamic_plugin(path):
    import importlib.util
    # Buscar script principal (por ahora buscamos plugin.py)
    script_path = os.path.join(path, "plugin.py")
    if not os.path.exists(script_path): return None
    try:
        spec = importlib.util.spec_from_file_location("dynamic_plugin", script_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Buscar una clase que termine en Plugin
            for item in dir(module):
                if item.endswith("Plugin") and item != "BasePlugin":
                    cls = getattr(module, item)
                    return cls(None)
    except: pass
    return None


def self_destruct(*args, **kwargs):
    try:
        data_file = _get_data_file()
        if os.path.exists(data_file):
            os.remove(data_file)
            return "💥 Protocolo de autodestrucción ejecutado. Datos eliminados."
        return "No hay datos que destruir."
    except Exception as e:
        return f"Fallo en autodestrucción: {e}"




# --- MOBILE ASSISTANT UTILS ---
def run_mobile_message(number, msg, app="whatsapp", voice_model=None):
    # Importar speak aquí para evitar dependencia circular al inicio
    import urllib.parse
    
    logger.info(f"📱 MOBILE RUN: {app} -> {number}: {msg}")
    
    # Importador dinámico para el motor universal de Fina
    sys.path.append(os.path.join(ERGEN_ROOT, "plugins", "system"))
    from mobile_hub import UniversalMobileHub
    
    try:
        # Detectar dispositivo conectado
        adb_check = subprocess.run(["adb", "devices"], capture_output=True, text=True).stdout
        target_ip = None
        for line in adb_check.strip().split('\n'):
            if "\tdevice" in line or " device" in line:
                target_ip = line.split()[0]
                break
        
        if not target_ip:
             speak("No veo ningún celular conectado. Por favor revisa la conexión.", voice_model)
             return

        # --- MOTOR SMS UNIVERSAL (INVISIBLE) ---
        if app == "sms":
             hub = UniversalMobileHub(ip=target_ip)
             if hub.send_sms(number, msg):
                 speak("SMS enviado correctamente.", voice_model)
             else:
                 speak("El sistema de SMS falló. Revisa la señal del móvil.", voice_model)
             return
        # ---------------------------------------

        # 2. Construir URI según App y paquete
        uri = ""
        pkg = ""
        encoded_msg = urllib.parse.quote(msg)
        
        if app == "whatsapp":
            # Usar esquema nativo whatsapp:// es más robusto
            uri = f"whatsapp://send?phone={number}&text={encoded_msg}"
            pkg = "com.whatsapp" 
        elif app == "telegram":
            uri = f"tg://msg?text={encoded_msg}&to={number}"
            pkg = "org.telegram.messenger"
        elif app == "signal":
             uri = f"smsto:{number}:{encoded_msg}"
        
        # 3. Lanzar Intent
        if uri:
             adb_cmd = ["adb", "-s", target_ip, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", uri]
             
             if app == "whatsapp":
                # Forzar paquete explícito para evitar Business, permitiendo que la app resuelva la Activity
                 adb_cmd.extend(["-p", "com.whatsapp"])
             elif pkg:
                 adb_cmd.extend(["-p", pkg])
                 
             try:
                subprocess.run(adb_cmd, timeout=15)
             except: pass
             
             speak(f"Abriendo {app}...", voice_model)
             
             speak(f"He abierto {app} para tramitar el envío.", voice_model)

    except Exception as e:
        logger.error(f"Mobile Error: {e}")
        speak("Hubo un error al intentar enviar el mensaje.", voice_model)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
        if action in ["speak", "say"] and len(sys.argv) > 2:
            speak(sys.argv[2], wait=True)
        elif action == "update_ui" and len(sys.argv) > 2:
            update_ui_state("idle", process=sys.argv[2])
    else:
        print("Ergen Utils CLI: Use 'speak <msg>' or 'update_ui <msg>'")



# --- DECO PLUGIN FUNCS ---
def _check_deco_deps(m=None):
    try:
        import urllib.request
        return True
    except ImportError:
        if m: speak("Faltan dependencias para el decodificador.", m)
        return False

def _get_deco_plugin_path():
    try:
        from plugin_manager import PluginManager
        from pathlib import Path
        pm = PluginManager()
        pm.discover_plugins()
        target_plugin = "sei800tc1"
        if target_plugin not in pm._plugins_paths:
            for name, path in pm._plugins_paths.items():
                if (Path(path) / "deco.py").exists():
                    return str(path)
        else:
            return str(pm._plugins_paths[target_plugin])
    except: pass
    return None

def _get_deco_plugin(m=None):
    if not _check_deco_deps(m): return None
    path = _get_deco_plugin_path()
    if path:
        import importlib.util
        import os
        try:
            spec = importlib.util.spec_from_file_location("dynamic_deco_plugin", os.path.join(path, "deco.py"))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "DecoPlugin"):
                    return module.DecoPlugin(None)
        except Exception as e:
            print(f"Error cargando plugin de Deco: {e}")
    
    if m: speak("No se encontró el plugin del decodificador.", m)
    return None

def turn_on_deco(m, command=""):
    if not _check_deco_deps(m): return
    plugin = _get_deco_plugin(m)
    if not plugin: return
    cmd_text = command if command else "enciende el decodificador"
    try:
        response = plugin.handle_intent("deco_on", cmd_text)
        if response: speak(response, m)
    except Exception as e:
        print(f"Error en turn_on_deco con plugin: {e}")
        speak("Hubo un error al intentar encender el decodificador.", m)

def turn_off_deco(m, command=""):
    if not _check_deco_deps(m): return
    plugin = _get_deco_plugin(m)
    if not plugin: return
    cmd_text = command if command else "apaga el decodificador"
    try:
        response = plugin.handle_intent("deco_off", cmd_text)
        if response: speak(response, m)
    except Exception as e:
        print(f"Error en turn_off_deco con plugin: {e}")
        speak("Hubo un error al intentar apagar el decodificador.", m)

def deco_volume_up_cmd(m, s=5): 
    if not _check_deco_deps(m): return
    plugin = _get_deco_plugin(m)
    if plugin:
        resp = plugin.handle_intent("deco_volume_up", "sube el volumen")
        if resp: speak(resp, m)

def deco_volume_down_cmd(m, s=5): 
    if not _check_deco_deps(m): return
    plugin = _get_deco_plugin(m)
    if plugin:
        resp = plugin.handle_intent("deco_volume_down", "baja el volumen")
        if resp: speak(resp, m)

def deco_mute_cmd(m): 
    if not _check_deco_deps(m): return
    plugin = _get_deco_plugin(m)
    if plugin:
        resp = plugin.handle_intent("deco_mute", "silencia")
        if resp: speak(resp, m)

def deco_channel_up_cmd(m): 
    if not _check_deco_deps(m): return
    plugin = _get_deco_plugin(m)
    if plugin:
        resp = plugin.handle_intent("deco_channel_up", "siguiente canal")
        if resp: speak(resp, m)

def deco_channel_down_cmd(m): 
    if not _check_deco_deps(m): return
    plugin = _get_deco_plugin(m)
    if plugin:
        resp = plugin.handle_intent("deco_channel_down", "canal anterior")
        if resp: speak(resp, m)

def deco_set_channel_cmd(c, m): 
    plugin = _get_deco_plugin(m)
    if plugin:
        resp = plugin.handle_intent("deco_set_channel", f"pon el canal {c}")
        if resp: speak(resp, m)
# --- END DECO PLUGIN FUNCS ---

