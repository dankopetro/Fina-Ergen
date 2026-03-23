import sys
import os

# -------------------------------------------------------------
# FORZAR CARGA LOCAL Y VENV DEL USUARIO (AppImage/DEB Fix)
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# CARGAR LIBRERÍAS INTEGRADAS (Bundled Libs de Recursos)
# Esto permite que Fina corra sin instalar nada vía PIP en el usuario
bundled_path = os.path.join(current_dir, "bundled_libs")
if os.path.exists(bundled_path):
    print(f"📦 Usando Librerías Integradas (Bundled): {bundled_path}", flush=True)
    sys.path.insert(0, bundled_path)
# -------------------------------------------------------------

# --- DETECCIÓN DE ENTORNO VIRTUAL [UNIVERSAL] ---
def get_best_python():
    """Busca el mejor ejecutable de Python disponible"""
    vps = [
        os.path.join(os.path.expanduser("~"), ".config", "Fina", "venv", "bin", "python"),
        os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"),
        os.path.join(os.path.expanduser("~"), ".venv", "bin", "python"),
        os.path.abspath(os.path.join("venv", "bin", "python")),
        os.path.abspath(os.path.join(".venv", "bin", "python")),
        sys.executable
    ]
    for p in vps:
        if os.path.exists(p): return p
    return sys.executable

# --- BOOTSTRAP: DESACTIVADO (Instalación vía Sistema) ---
def bootstrap_fina():
    """Ya no instalamos nada en caliente. El .DEB/.RPM maneja las dependencias."""
    print("ℹ️ Fina: Usando dependencias del sistema instaladas por el paquete (.deb/.rpm).")
    return True

# Determinar si estamos en un entorno virtual (VENV)
in_venv = sys.prefix != sys.base_prefix

best_py = get_best_python()

# Si no estamos en un venv, intentar buscar uno o crearlo
if not in_venv:
    if "venv" not in best_py:
        # Intentar bootstrap si no se detectó ningún venv existente
        if bootstrap_fina():
            best_py = get_best_python()
    
    # Si encontramos un python mejor (un venv) que no es el actual, relanzar
    if best_py != sys.executable:
        print(f"🔄 Relanzando Fina con entorno detectado: {best_py}")
        import getpass
        print(f"👤 Ejecutado por: {getpass.getuser()}")
        # Aseguramos que pasamos la ruta absoluta
        # Usamos execv con una lista de argumentos para evitar errores de firma
        os.execv(best_py, [best_py] + sys.argv)
# --------------------------------------------------

# FORZAR VISIBILIDAD DE LIBRERÍAS DEL USUARIO (Para aislamientos de AppImage)
import glob
# Buscar el site-packages dinámicamente según el mejor entorno detectado
venv_bases = [
    os.path.dirname(os.path.dirname(best_py)),
    os.path.expanduser("~/.config/Fina/venv"),
    os.path.abspath("venv"),
    os.path.abspath(".venv")
]

for base in venv_bases:
    dynamic_site_packages1 = os.path.join(base, "lib", "python3.*", "site-packages")
    dynamic_site_packages2 = os.path.join(base, "lib64", "python3.*", "site-packages")
    for pattern in [dynamic_site_packages1, dynamic_site_packages2]:
        for p in glob.glob(pattern):
            if p not in sys.path:
                sys.path.append(p)  # NO USAR INSERT(1). Causa shadow strikes a python builtin libs como typing.py.

import logging
import time
import traceback

# --- GLOBAL EXCEPTION HANDLER [CRITICAL] ---
# Esto asegura que cualquier crash al inicio se imprima en el log global
def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    print("\n[FATAL PYTHON CRASH] -------------------------", file=sys.stderr)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    print("--------------------------------------------------\n", file=sys.stderr)
    # Intentar loguear si el logger ya existe
    try:
        logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    except:
        pass

sys.excepthook = global_exception_handler
# -------------------------------------------

import json
import re
import requests
import asyncio
import subprocess
import threading

# Asegurar que el CWD es el directorio del script para encontrar config.py, etc.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from intent_classifier import detect_intent

# --- IMPORTACIÓN ORGANIZADA DE UTILITIES ---
from utils import (
    update_ui_state, logger, read_recent_unread_emails, clean_text_for_speech, 
    trim_response, clean_input, speak as utils_speak, sleep_now, change_wallpaper,
    listen, get_mistral_response, get_weather, get_weather_tomorrow, when_will_rain, 
    web_search, load_contacts, send_email, count_recent_unread_emails,
    play_music, stop_music, pause_music, next_track, music_volume_down, shutdown, reboot,
    update, add_reminder, list_reminders, run_schedule_loop, get_top_news,
    get_battery_status, wiki_summary, get_ip, get_system_stats, start_timer, 
    tell_joke, create_note, get_current_datetime, play_youtube, find_file, 
    get_clipboard, convert_currency, generate_image, self_destruct,
    read_pdf, get_weather_forecast, update_assistant_code, get_time_based_greeting, 
    get_uptime, scan_ports, get_public_ip, scan_wifi, save_voice_note, 
    get_daily_affirmation, toggle_battery_saver, play_ambient_sound, take_webcam_photo,
    backup_files, download_instagram_reel, convert_md_to_html, generate_password, 
    check_linux_updates, handle_unknown_request, decrease_volume, decrease_brightness, 
    increase_volume, increase_brightness, take_screenshot, toggle_night_mode, 
    translate_text, close_app, open_app, turn_on_tv, turn_off_tv, music_volume_up,
    tv_volume_up_cmd, tv_volume_down_cmd, tv_channel_up_cmd, tv_channel_down_cmd, 
    tv_open_app_cmd, tv_exit_app_cmd, tv_set_channel_cmd, tv_mute_cmd, is_tv_on, 
    tv_set_volume_cmd, tv_set_input_cmd,
    turn_on_deco, turn_off_deco, deco_volume_up_cmd, deco_volume_down_cmd, 
    deco_channel_up_cmd, deco_channel_down_cmd, deco_set_channel_cmd, deco_mute_cmd,
    deco_set_volume_cmd, deco_open_app_cmd, deco_exit_app_cmd, deco_set_input_cmd,
    ensure_tv_is_on, get_doorbell_status_cmd, show_doorbell_image, 
    show_doorbell_stream, send_ui_command, check_system_dependencies, is_code_worthy,
    perform_ac_control, scan_network_cmd, robot_clean_cmd, lights_on_cmd, lights_off_cmd,
    lock_door_cmd, unlock_door_cmd, blinds_open_cmd, start_watering_cmd, check_solar_production_cmd,
    fridge_status_cmd, fridge_inventory_cmd, fridge_set_temp_cmd, lights_set_brightness_cmd,
    blinds_close_cmd, lock_status_cmd, robot_status_cmd, appliance_status_cmd, energy_status_cmd,
    CONFIG_DIR, SETTINGS_PATH, USER_DATA_PATH, CONTACTS_PATH, CONFIG_PY_PATH, load_config,
    get_proactive_briefing, text_to_number_es, suspend, stop_voice_engine, i18n,
    get_unified_config, get_sys_lang, get_idiom
)
config, CONFIG_FOUND = load_config()

# --- DIAGNÓSTICO INICIAL ---
import getpass
print(f"🧠 Cerebro de Fina Iniciado... (V3.5.9-6 ({time.strftime('%d/%m/%Y %H:%M')}))", flush=True)
print(f"👤 Corriendo como: {getpass.getuser()}", flush=True)
if os.getuid() == 0:
    print("⚠️  [ADVERTENCIA] Fina está siendo ejecutada como ROOT.", flush=True)
    print("   Esto impedirá leer archivos en /home/usuario/.config/Fina si no se configuró así.", flush=True)
print(f"📂 Carpeta de Configuración detectada: {CONFIG_DIR}", flush=True)
print(f"📄 Archivo Settings: {'Encontrado' if os.path.exists(SETTINGS_PATH) else 'NOT FOUND'}", flush=True)
print(f"---------------------------------\n", flush=True)

# --- SYSTEM CHECK ---
check_system_dependencies()

# update_ui_state removido (ahora importado de utils)

def speak(text, model=None, sink=None, wait=True):
    """Local wrapper to delegate speech and UI updates to utils"""
    if not text: return
    
    # 2. Actual Voice Output (will update UI in background worker for sync)
    try:
        if sink:
            utils_speak(text, model, sink=sink, wait=wait)
        else:
            utils_speak(text, model, wait=wait)
        # Small sleep to allow worker thread to take context if needed
        time.sleep(0.05)
    except Exception as e:
        print(f"Error en voz: {e}")

# Las variables EMAIL, MISTRAL, etc. ya usan el get_unified_config importado de utils

# Credenciales de Email (Prioridad UI)
EMAIL_USER = get_unified_config("EMAIL_USER")
EMAIL_PASSWORD = get_unified_config("EMAIL_PASSWORD")
imap_server = get_unified_config("IMAP_SERVER", "imap.gmail.com") 

# API Keys (Prioridad UI)
MISTRAL_API_KEY = get_unified_config("MISTRAL_API_KEY")
GITHUB_TOKEN = get_unified_config("GITHUB_TOKEN")
ELEVENLABS_API_KEY = get_unified_config("ELEVENLABS_API_KEY")

# Memoria de último contacto para comandos como "mandale otro"
last_contact_resolved = {"name": None, "number": None}

# --- PROACTIVE CONTACT RESOLUTION ---
async def resolve_contact_proactive(query, contacts, voice_model, model_for_listen):
    global last_contact_resolved
    import difflib
    query_lower = (query or "").lower()
    
    # 0. Soporte para "al mismo", "a el", "a ella" si tenemos memoria
    if any(x in query_lower for x in ["mismo", "él", "ella", "otro"]) and last_contact_resolved["number"]:
        print(f"🔄 Usando memoria de contacto: {last_contact_resolved['name']}")
        return last_contact_resolved["name"], last_contact_resolved["number"]

    # 1. Búsqueda por coincidencia exacta (siempre manda)
    for name, num in contacts.items():
        if name.lower() in query_lower:
            last_contact_resolved = {"name": name, "number": num}
            return name, num
            
    # 2. Limpiar query de ruidos para búsqueda difusa
    stop_words = ["llama", "a", "al", "de", "enviá", "enviar", "mensaje", "mandale", "dile", "decile", "por", "whatsapp", "sms", "fina"]
    query_words = [w for w in query_lower.split() if w not in stop_words]
    
    scored_matches = []
    for name, num in contacts.items():
        name_lower = name.lower()
        name_parts = name_lower.split()
        score = 0
        
        for part in name_parts:
            if len(part) < 3: continue
            # ¿Parte del nombre está en el comando?
            if part in query_words:
                score += 10
            else:
                # Búsqueda difusa por cada palabra del comando
                for qw in query_words:
                    if not isinstance(qw, str) or len(qw) < 3: continue
                    a_str = str(part)
                    b_str = str(qw)
                    ratio = difflib.SequenceMatcher(None, a_str, b_str).ratio()
                    if ratio > 0.8: score += 8
                    elif ratio > 0.6: score += 4
                    
        if score > 0:
            scored_matches.append((score, name, num))
            
    if not scored_matches:
        return None, None
        
    # Ordenar por puntaje
    scored_matches.sort(key=lambda x: x[0], reverse=True)
    best_score = scored_matches[0][0]
    
    # Filtrar candidatos viables (similares al mejor puntaje)
    final_candidates = [c for c in scored_matches if c[0] >= best_score * 0.7]
    
    res_name, res_num = None, None
    if len(final_candidates) == 1:
        score, name, num = final_candidates[0]
        # Si no estamos súper seguros (puntaje bajo), preguntamos
        if score < 15:
            speak(f"¿Te referís a {name}?", voice_model)
            if (listen(model_for_listen) or "").lower() in ["sí", "si", "claro", "dale", "bueno"]:
                res_name, res_num = name, num
        else:
            res_name, res_num = name, num
        
    else:
        # Múltiples opciones: Enumerar
        final_candidates = final_candidates[:4] # Máximo 4 para no cansar
        msg = f"Encontré {len(final_candidates)} posibles: "
        for i, (s, name, num) in enumerate(final_candidates):
            msg += f"{i+1}: {name}. "
        msg += "¿Cuál querés?"
        speak(msg, voice_model)
        
        choice = (listen(model_for_listen) or "").lower()
        if not choice or "cancela" in choice: return None, None
        
        # 1. Intentar por número
        pass
        idx = text_to_number_es(choice)
        if idx and 1 <= idx <= len(final_candidates):
            res_name, res_num = final_candidates[idx-1][1], final_candidates[idx-1][2]
            
        # 2. Intentar por nombre/apellido en la respuesta
        else:
            for s, name, num in final_candidates:
                if name.lower() in choice:
                    res_name, res_num = name, num
                    break

    if res_name and res_num:
        last_contact_resolved = {"name": res_name, "number": res_num}
        return res_name, res_num
                
    return None, None

# --- Metadata del Sistema ---
FINA_VERSION = "Fina Ergen v 3.5.9-5"
FINA_AUTHOR = "Dankopetro"
FINA_CREATED = "el 04 de Marzo de 2026 a las 12:15"

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# Autonomía total: Phoenix solo mira dentro de su carpeta
GLOBAL_ROOT = PROJECT_ROOT

def get_all_voice_models():
    """Escanea y construye el diccionario de voces disponibles dinámicamente"""
    # Voces embebidas por defecto
    models = {
        "ElevenLabs": "ElevenLabs",
        "Amy (Inglés)": os.path.join(CONFIG_DIR, "voice_models", "en_US-amy-low.onnx"),
        "Aldo (M): Español": os.path.join(CONFIG_DIR, "voice_models", "es_MX-ald-medium.onnx"),
        "Daniela (F): Español AR": os.path.join(CONFIG_DIR, "voice_models", "es_AR-daniela-high.onnx"),
        "Claude (Español)": os.path.join(CONFIG_DIR, "voice_models", "es_MX-claude-high.onnx"),
        "Laura (Español)": os.path.join(CONFIG_DIR, "voice_models", "es_MX-laura-high.onnx"),
        "Miro (Español)": os.path.join(CONFIG_DIR, "voice_models", "miro_es-ES.onnx"),
    }
    
    # 1. Buscar en Carpeta de Usuario (~/.config/Fina/voice_models)
    # 2. Buscar en Ruta personalizada de la Interfaz
    user_custom_path = get_unified_config("VOICE_MODELS_PATH")
    
    search_dirs = [os.path.join(CONFIG_DIR, "voice_models"), os.path.join(PROJECT_ROOT, "voice_models")]
    if user_custom_path and os.path.exists(user_custom_path) and os.path.isdir(user_custom_path):
        search_dirs.append(user_custom_path)
    
    for s_dir in search_dirs:
        if os.path.exists(s_dir):
            try:
                for f in os.listdir(s_dir):
                    if f.endswith(".onnx"):
                        # Crear un nombre amigable
                        nice_name = f.replace(".onnx", "").replace("-", " ").replace("_", " ").title()
                        path = os.path.join(s_dir, f)
                        if nice_name not in models:
                             models[nice_name] = path
            except: pass
            
    return models

# Carga dinámica al arrancar
VOICE_MODELS = get_all_voice_models()

# PRIORIDAD: 1. VOICE_MODEL de settings, 2. Daniela, 3. Primera disponible
selected_voice_id = get_unified_config("VOICE_MODEL")
DEFAULT_VOICE = None

if selected_voice_id:
    # Buscar si el ID está en los valores o si coincide con alguna clave (formato amigable)
    for name, path in VOICE_MODELS.items():
        if selected_voice_id in path or selected_voice_id.lower() in name.lower():
            DEFAULT_VOICE = path
            break

if not DEFAULT_VOICE:
    DEFAULT_VOICE = VOICE_MODELS.get("Aldo (M): Español", list(VOICE_MODELS.values())[0])

# Funcionalidad de cambio de voz
voice_model_names = list(VOICE_MODELS.keys())
current_voice_index = voice_model_names.index("Aldo (M): Español") if "Aldo (M): Español" in voice_model_names else 0

def cycle_voice_model():
    """Cycle to the next voice model"""
    global current_voice_index
    current_voice_index = (current_voice_index + 1) % len(voice_model_names)
    voice_name = voice_model_names[current_voice_index]
    voice_path = VOICE_MODELS[voice_name]
    return voice_path, voice_name

def get_current_voice_info():
    """Get current voice model path and name"""
    voice_name = voice_model_names[current_voice_index]
    voice_path = VOICE_MODELS[voice_name]
    return voice_path, voice_name


# Setup checks for required files ---
if not CONFIG_FOUND:
    print("\n⚠️ AVISO: Fina Ergen está en MODO INICIAL.")
    print("  - No se encontró config.py. Esto es normal si es la primera vez.")
    print("  - El sistema funcionará con capacidades limitadas hasta ser configurado.")
    # No salimos: sys.exit(1) removido

# Logger Setup (Centralized in Ergen Root)
# Logger Setup Centralizado en utils.py
# Simplemente obtenemos el logger (utils ya configuró el root)
logger = logging.getLogger("FinaPlugins")
logger.setLevel(logging.DEBUG)
 # Ya importado arriba
logger.info(f"--- FINA ERGEN MAIN INICIADO ---")

async def main():
    """Main interaction loop"""

    # DEBUG LOG DE ARRANQUE
    with open("/tmp/fina_main_debug.log", "w") as f:
        f.write(f"Iniciando Fina Ergen Main...\n")
        f.write(f"CWD: {os.getcwd()}\n")
        f.write(f"PROJECT_ROOT: {PROJECT_ROOT}\n")
        f.write(f"Python: {sys.executable}\n")

    try:
        import utils
        # Obtenemos el idioma principal del usuario (Auto-detección si no existe)
        sys_lang = utils.get_sys_lang()
        
        # En la primera ejecución guardamos el idioma detectado para que la UI lo use
        if not utils.get_unified_config("FINA_LANGUAGE"):
            try:
                if os.path.exists(SETTINGS_PATH):
                    with open(SETTINGS_PATH, 'r') as f:
                        data = json.load(f)
                    if "apis" not in data: data["apis"] = {}
                    data["apis"]["FINA_LANGUAGE"] = sys_lang
                    with open(SETTINGS_PATH, 'w') as f:
                        json.dump(data, f, indent=4)
                    print(f"🌍 Idioma '{sys_lang.upper()}' auto-detectado y guardado.")
            except: pass
        
        import threading
        # --- INICIO DE FEEDBACK VISUAL INMEDIATO ---
        update_ui_state("idle", "Iniciando Fina Ergen...")
        time.sleep(0.3)
        
        # --- CARGA ASÍNCRONA DE MOTORES PESADOS (FONDO) ---
        print("🚀 Lanzando carga de motores en segundo plano...", flush=True)
        def load_engines():
            try:
                update_ui_state("idle", "Cargando modelos de lenguaje...")
                from intent_classifier import _initialize_model, detect_intent
                _initialize_model()
                detect_intent("hola", confidence_threshold=0.1)
                print("✅ Motores de Intentos listos.", flush=True)
            except Exception as e:
                logger.error(f"Error en hilos de motores: {e}")

            try:
                update_ui_state("idle", "Sincronizando reconocimiento de voz...")
                utils.load_vosk_model(sys_lang)
                print("✅ Vosk listo.", flush=True)
            except Exception as e:
                logger.error(f"Error cargando Vosk en fondo: {e}")

        threading.Thread(target=load_engines, daemon=True).start()

        # --- INICIALIZACIÓN DE PLUGINS Y BIOMETRÍA ---
        print("🔌 Inicializando plugins y biometría...", flush=True)
        update_ui_state("idle", "Conectando hardware y biometría...")
        time.sleep(0.3)
        
        plugin_integration = None
        voice_auth = None
        authenticate_user = None

        try:
            # Importar modulos de autenticación y plugins
            from auth.fingerprint_auth import authenticate_user
            from auth.voice_auth import VoiceAuthenticator
            from fina_plugin_integration import setup_plugins
            
            # Inicializar plugins de inmediato
            plugin_integration = setup_plugins(speak_callback=lambda text, sink=None: speak(text, DEFAULT_VOICE, sink=sink))
            
            # Forzar actualización inicial de estado (Clima, etc)
            if plugin_integration:
                try:
                    def ac_update_worker():
                        # Esperamos para la primera actualización para no saturar el arranque
                        time.sleep(10)
                        while True:
                            try:
                                if plugin_integration:
                                    plugin_integration.handle_intent("ac_control", "status")
                            except: pass
                            time.sleep(300) # Cada 5 min (background polling)
                    threading.Thread(target=ac_update_worker, daemon=True).start()
                except: pass

            # Background System Stats Worker
            def system_stats_worker():
                import psutil
                while True:
                    try:
                        # CPU
                        cpu_p = psutil.cpu_percent(interval=1.0)
                        # RAM
                        mem = psutil.virtual_memory()
                        # DISK
                        disk = psutil.disk_usage('/')
                        # UPTIME
                        with open('/proc/uptime', 'r') as f:
                            uptime_seconds = float(f.readline().split()[0])
                        uptime_h = int(uptime_seconds // 3600)
                        uptime_m = int((uptime_seconds % 3600) // 60)
                        
                        stats = {
                            "cpu": {"percent": cpu_p},
                            "ram": {"percent": mem.percent, "used": round(mem.used / (1024**3), 2), "total": round(mem.total / (1024**3), 2)},
                            "disk": {"percent": disk.percent, "free": round(disk.free / (1024**3), 2)},
                            "uptime": f"{uptime_h}h {uptime_m}m"
                        }
                        update_ui_state("idle", extra_payload={"system_stats": stats})
                    except: pass
                    time.sleep(10) # Frecuencia moderada para no saturar
            threading.Thread(target=system_stats_worker, daemon=True).start()

            # Inicializar biometría
            try:
                voice_auth = VoiceAuthenticator()
                print("✅ Biometría cargada.")
            except Exception as e:
                print(f"⚠️ Biometría falló (saltando): {e}")
                
        except ImportError as e:
            msg = f"Faltan dependencias críticas: {e}."
            print(f"❌ {msg}")

        # --- VERIFICACIÓN DE MODELOS PARA NOVATOS ---
        vosk_model_name, _ = utils.VOSK_MODELS.get(sys_lang, utils.VOSK_MODELS["en"])
        vosk_path = os.path.join(os.path.expanduser("~"), ".config", "Fina", "model", vosk_model_name)
        
        # EL ALERT SOLO SI REALMENTE NO HAY NADA DE NADA
        models_missing = (not DEFAULT_VOICE or not os.path.exists(DEFAULT_VOICE)) and (not os.path.exists(vosk_path))
        manual_lock = os.path.join(CONFIG_DIR, ".manual_opened")
        # El aviso de modelos solo si DE VERDAD no hay config ni modelos.
        show_alert = models_missing and not CONFIG_FOUND

        if show_alert:
            msg_novato = utils.i18n("novice_alert", "¡HOLA! NECESITO MIS MODELOS (VER MANUAL)")
            update_ui_state("idle", msg_novato)
            print(f"💡 Alerta Inicial Novato.")
            if not os.path.exists(manual_lock):
                import webbrowser
                lang = sys_lang
                base_name = "Manual_Guia_Configuracion_Fina" if lang == "es" else "Manual_Configuration_Guide_Fina_EN"
                manual_html = os.path.join(PROJECT_ROOT, "docs", f"{base_name}.html")
                if os.path.exists(manual_html):
                    webbrowser.open(f"file://{manual_html}")
                with open(manual_lock, "w") as f: f.write("done")
        
        # --- SALUDO INICIAL (CON VERIFICACIÓN DE FUNCIONES) ---
        if not show_alert:
            update_ui_state("idle", i18n("ui_loading_data", "Sincronizando datos..."))
            
            ready_weather = threading.Event()
            ready_ac = threading.Event()
            
            # 1. Determinar si AC está configurado
            ac_configured = False
            try:
                if os.path.exists(SETTINGS_PATH):
                    with open(SETTINGS_PATH, 'r') as f:
                        import json
                        data = json.load(f)
                        ac_configured = bool(data.get("apis", {}).get("AC_IP"))
            except: pass
            
            if not ac_configured: ready_ac.set()
            
            # 2. Registrar Listener AC (Y propagar a la UI)
            if plugin_integration:
                # Memoria persistente para evitar reseteos a cero del AC
                last_ac_payload = {}
                
                def handle_ac_update(payload):
                    nonlocal last_ac_payload
                    # Si el payload nuevo trae ceros en energía pero el viejo tenía valores, mantenemos el viejo
                    if last_ac_payload and payload.get("total_kwh", 0) == 0 and last_ac_payload.get("total_kwh", 0) > 0:
                        payload["total_kwh"] = last_ac_payload["total_kwh"]
                        payload["monthly_kwh"] = last_ac_payload["monthly_kwh"]
                    
                    last_ac_payload = payload.copy()
                    
                    # Actualizamos visualmente el panel de AC
                    update_ui_state("idle", extra_payload={"ac_status": payload})
                    ready_ac.set()
                
                plugin_integration.register_event_listener("ac-status-update", handle_ac_update)
                
                # Forzar actualización inicial
                def ac_boot_update():
                    if plugin_integration:
                        # Llamamos directo a una acción silenciosa para no hablar durante el arranque
                        plugin_integration.plugin_manager.execute_plugin_action("Clima", "clima.py --status --silent")
                threading.Thread(target=ac_boot_update, daemon=True).start()

            # 3. Verificar Clima (si hay internet)
            def check_weather_readiness():
                try:
                    import asyncio
                    asyncio.run(utils.get_weather())
                except: pass
                finally: ready_weather.set()
            
            try:
                import socket
                socket.create_connection(("8.8.8.8", 53), timeout=1.5)
                threading.Thread(target=check_weather_readiness, daemon=True).start()
            except:
                ready_weather.set()

            # 4. Verificación paralela de Clima y AC (con feedback)
            # Esperamos hasta 3 segundos para que los datos aparezcan en el panel
            wait_start = time.time()
            print("⏳ Sincronizando Clima y AC...", flush=True)
            while time.time() - wait_start < 3.0: 
                if ready_weather.is_set() and ready_ac.is_set():
                    break
                update_ui_state("idle", "Obteniendo datos meteorológicos y de dispositivos...")
                time.sleep(0.1)
            
            # 5. Estabilización Universal de CPU 
            try:
                import psutil
                # Un pequeño respiro tras la carga masiva de modelos
                cpu_usage = psutil.cpu_percent(interval=0.1)
                if cpu_usage > 65:
                    print(f"⚙️ Alerta Alta Carga de CPU ({cpu_usage}%): Esperando estabilización...", flush=True)
                    # Solo esperamos si es realmente necesario y por poco tiempo
                    time.sleep(1.0)
            except: pass
                
            # 6. Check de Arranque de Android (Waydroid/Weston) para Timbre
            try:
                import psutil, subprocess
                m8_active = False
                if plugin_integration:
                    m8_active = any(p.get('name') == 'M8' for p in plugin_integration.get_loaded_plugins())
                
                if m8_active:
                    print("🤖 Sistema de Timbre detectado. Sincronizando arranque de Android...", flush=True)
                    waydroid_start = time.time()
                    waydroid_msgs = [
                        "Iniciando Virtualización Android...",
                        "Conectando con el núcleo (ADB)...",
                        "Despertando sistema de Timbre...",
                        "Cargando escritorio Android...",
                        "Aguardando estabilidad de UI..."
                    ]
                    
                    while time.time() - waydroid_start < 60: # Max 60 segundos para no colgarse
                        current_msg = waydroid_msgs[int((time.time() - waydroid_start) // 5) % len(waydroid_msgs)]
                        update_ui_state("idle", current_msg)
                        
                        try:
                            waydroid_ip = get_unified_config("WAYDROID_IP") or "127.0.0.1"
                            # ADB connect y check de boot síncrono para el loop
                            res = subprocess.run(f"adb connect {waydroid_ip}:5555 >/dev/null 2>&1; adb shell getprop sys.boot_completed", shell=True, capture_output=True, text=True, timeout=2.0)
                            if "1" in res.stdout:
                                update_ui_state("idle", "¡Android Listo!")
                                print("✅ Android (Timbre) operativo.", flush=True)
                                break
                        except: pass
                        time.sleep(2)
            except: pass

            update_ui_state("idle", "Sintonizando voz natural...")
            time.sleep(0.5) # Reducido de 2.0s
            update_ui_state("idle", "Sistemas en línea.")
            time.sleep(0.2) # Reducido de 0.5s
            update_ui_state("idle", None)
            
        if CONFIG_FOUND:
            import getpass
            username_config = get_unified_config("USER_NAME")
            if not username_config or username_config.lower() == "administrador":
                username_config = getpass.getuser()
            username = (username_config or "Usuario").capitalize()
            greeting = get_time_based_greeting()
            idiom = get_idiom("welcome")
            username_clean = username.split()[0] # Solo el primer nombre para más naturalidad
            
            # Combinar saludo, modismo y mensaje de sistema
            full_msg = f"{greeting} {username_clean}. {idiom} {utils.i18n('systems_ready', 'Sistemas listos.')}"
            
            update_ui_state("idle", utils.i18n("sys_ready_short", "SISTEMA LISTO"))
            speak(full_msg, DEFAULT_VOICE)
        else:
            msg = utils.i18n("systems_ready_no_conf", "Bienvenido. Por favor, consulta el manual para configurarme.")
            update_ui_state("idle", utils.i18n("sys_ready_short", "SISTEMA LISTO"))
            speak(msg, DEFAULT_VOICE)
            
    except Exception as e:
        logger.error(f"Error general en arranque: {e}")
        update_ui_state("idle", i18n("ui_startup_error", "ERROR EN ARRANQUE"))

    proactive_briefing_given = False
    user_is_authenticated = False
    # ----------------------------------------

    while True:
        model = "tiny"

        # Wake word loop (esperando "Fina")
        while True:
            update_ui_state("idle", None)
            selected_voice_model, current_voice_name = get_current_voice_info()
            audio_input = listen(model, language=sys_lang)  # Cambio a español
            if not audio_input:
                continue
            
            update_ui_state("listening", utils.i18n("listening", "Escuchando..."))
            command = audio_input.lower()
            intent, confidence = detect_intent(command)
            
            # Verificar wake word con sensibilidad original (para que escuche de lejos)
            if intent == "wake_up" and confidence > 0.6:
                if not user_is_authenticated:
                    update_ui_state("authenticating", utils.i18n("auth_waiting", "Esperando autenticación..."))
                    temp_voice_model, _ = get_current_voice_info()
                    # Verificamos si la función existe antes de llamarla
                    if authenticate_user and authenticate_user(voice_model=temp_voice_model, speak_func=speak):
                        user_is_authenticated = True
                        update_ui_state("speaking", utils.i18n("auth_success", "Autenticación Exitosa"))
                        speak("Autenticación Exitosa", temp_voice_model)
                    else:
                        speak(i18n("msg_auth_failed", "Autenticación fallida."), temp_voice_model)
                        continue
                
                # Si ya está autenticado o acaba de autenticarse con éxito
                wait_msg = i18n("ui_waiting_command", "Esperando Comando...")
                update_ui_state("speaking", wait_msg)
                speak(wait_msg, selected_voice_model)
                break 
            else:
                # Si se detectó ruido pero no fue la palabra clave con confianza
                if len(command.split()) > 0:
                   speak(i18n("msg_try_again", "Intente de nuevo."), selected_voice_model)
                continue

        # Always reset to Ald after wake-up
        if "Aldo (M): Español" in voice_model_names:
            current_voice_index = voice_model_names.index("Aldo (M): Español")
        selected_voice_model, current_voice_name = get_current_voice_info()
        # No repetimos el saludo si ya dijimos "Esperando comando" o lo combinamos
        # speak(get_time_based_greeting(), selected_voice_model)
        
        # Proactive briefing (Restaurado y limpiado)
        if not proactive_briefing_given:
            try:
                # Eliminada la actualización redundante previa.
                # update_ui_state("speaking", "¿Querés las noticias?") <- ESTA ERA LA DUPLICADA
                
                speak(i18n("msg_news_query", "¿Querés que te cuente las noticias?"), selected_voice_model)
                
                update_ui_state("listening", utils.i18n("waiting_response", "Esperando respuesta..."))
                response = listen(model, language=sys_lang)
                if response:
                    intent_response, _ = detect_intent(response.lower())
                    if intent_response == "yes":
                        update_ui_state("idle", i18n("ui_system_ready_diga_fina", "SISTEMA LISTO. Diga Fina."))
                        update_ui_state("speaking", i18n("ui_preparing_news", "Preparando noticias..."))
                        # Usar la nueva función robusta
                        briefing = get_proactive_briefing(selected_voice_model)
                        speak(briefing, selected_voice_model)
                    else:
                        speak(i18n("msg_understood_continue", "Entendido, continuemos."), selected_voice_model)
            except Exception as e:
                logger.warning(f"Could not deliver proactive briefing: {e}")
            proactive_briefing_given = True

        # Main conversation loop
        consecutive_failures = 0
        while True:
            # Mantener el texto anterior (respuesta de Fina) mientras escuchamos
            update_ui_state("listening", None)
            
            # Listen WITH audio capture for verification
            listen_result = listen(model, language=sys_lang, timeout=20, return_audio=True)
            
            if not listen_result or listen_result[0] is None:
                # Si no hay comando (timeout), volvemos al estado idle (Azul Profundo)
                # update_ui_state("speaking", "Me quedo atenta")
                speak(i18n("msg_resting_listening", "Descanso el oido pero me quedo atenta por si me necesitás. Hasta luego."), selected_voice_model)
                update_ui_state("idle", None)
                break # Rompemos el bucle de conversación para volver al wake_word loop
            
            command, audio_data = listen_result
            
            # LOG: Mostrar lo que Fina escuchó (FLUSH IMPORTANTE PARA TEE)
            logger.info(f"🎤 ESCUCHÉ: '{command}'")
            print(f"🎤 ESCUCHÉ: '{command}'", flush=True) # Redundancia para garantizar visibilidad
            sys.stdout.flush() # Doble seguridad
            
            # Identify Speaker (Passive)
            identified_user = None
            score = 0.0
            if voice_auth:
                try:
                    # Identificar entre todos los perfiles disponibles
                    identified_user, score = voice_auth.identify_user(audio_data)
                except Exception as e: 
                    # logger.error(f"Error identificando voz pasiva: {e}")
                    pass
            
            # Si se identifica un usuario, lo capitalizamos para el log
            current_user = identified_user.capitalize() if identified_user else "Invitado"
            is_admin = (identified_user is not None) # Por ahora, cualquier voz conocida se trata con privilegios de usuario
            print(f"🎤 Hablante: {current_user} (Confianza: {score:.2f})")
            
            # Fina ahora DIRÁ el modismo de procesamiento para que el usuario sepa que está trabajando
            commandFinal = command.lower()
            thinking_msg = utils.get_idiom("thinking", "Procesando...")
            if len(commandFinal) > 4:
                # Lo ponemos en la cola sin bloquear para que la detección de intent siga en paralelo
                speak(thinking_msg, selected_voice_model, wait=False)
            else:
                update_ui_state("speaking", thinking_msg)

            # --- CORRECCIÓN INTENCIONES DISCORDANTES ---
            # Si dice "Soy Claudio", "Soy Yo", etc., NO es una búsqueda ni otra cosa.
            identity_phrases = ["soy yo", "quién soy", "quien soy", "me conoces", "me conocés", "soy admin", "abre sesion", "abre sesión"]
            if any(p in commandFinal for p in identity_phrases):
                if identified_user:
                    speak(f"Hola {identified_user.capitalize()}. Te reconozco perfectamente. ¿Qué necesitás?", selected_voice_model)
                else:
                    speak(i18n("msg_voice_mismatch", "Tu voz no coincide con ningún perfil registrado. Acceso denegado."), selected_voice_model)
                continue
            # -------------------------------------------

            # --- VERIFICAR PLUGINS ---
            if plugin_integration:
                plugin_intent = plugin_integration.match_plugin_intent(commandFinal)
                if plugin_intent:
                    print(f"🔌 Plugin Intent Detectado: {plugin_intent}")
                    try:
                        plugin_integration.handle_intent(plugin_intent, commandFinal)
                    except Exception:
                        pass
                    continue # Saltar detección normal
            # -------------------------

            # --- OVERRIDE DE SEGURIDAD PARA COMANDOS DE SUEÑO Y SALIDA (Evitar MFA) ---
            if any(p in commandFinal.lower() for p in ["descansa", "descansá", "ponete a dormir", "vete a dormir", "dormí", "duerme"]):
                intent = "sleep"
                confidence = 1.0
            elif any(p in commandFinal.lower() for p in ["desconectate", "desconéctate", "apagar sistema", "apagar todo"]):
                intent = "exit_fina"
                confidence = 1.0
            else:
                intent, confidence = detect_intent(commandFinal)
            print("Intent:", intent)

            if intent == "exit_fina":
                # SEGURIDAD: Solo Administrador puede apagar el sistema completo.
                if not is_admin:
                    speak(i18n("msg_security_protocol_shutdown", "Protocolo de seguridad activo. Valida tu identidad con huella para apagar el sistema."), selected_voice_model)
                    if not authenticate_user(voice_model=selected_voice_model, speak_func=speak):
                        speak(i18n("msg_access_denied_shutdown", "Acceso denegado. No se puede apagar el sistema."), selected_voice_model)
                        continue
                
                # Acceso Concedido
                selected_voice_model, _ = get_current_voice_info()
                # update_ui_state("speaking", "Apagando Sistemas")
                speak(i18n("msg_auth_confirmed_shutdown", "Autorización confirmada. Apagando todos los sistemas."), selected_voice_model)
                update_ui_state("idle", "shutdown")
                print("🛑 EJECUTANDO PROTOCOLO DE APAGADO TOTAL (AUTORIZADO)...")
                
                # 1. Avisar a la API (Estado Shutdown)
                try: requests.get("http://127.0.0.1:18000/api/shutdown", timeout=0.5)
                except: pass
                
                # 2. Matar todo explícitamente usando janitor.py (si existe)
                try:
                    janitor_script = os.path.join(PROJECT_ROOT, "scripts", "janitor.py")
                    if os.path.exists(janitor_script):
                        print("🔪 Ejecutando purga con Janitor...")
                        python_venv = "python3"
                        subprocess.run([python_venv, janitor_script], check=False)
                    else:
                        print("⚠️ janitor.py no encontrado, saltando purga estricta.")
                except Exception as e: 
                    print(f"Error llamando cleanup: {e}")

                if plugin_integration:
                    plugin_integration.cleanup()
                
                # Salir.
                os._exit(0)

            selected_voice_model, current_voice_name = get_current_voice_info()
            
            # --- Lógica de Gestión de Conversación y Ruido ---
            
            # Si se detectó un comando válido (Intent), ejecutamos y reseteamos el contador de fallos
            if intent:
                consecutive_failures = 0
                
            # Si NO hay intent (Vosk escuchó algo, pero no es un comando conocido)
            else:
                consecutive_failures += 1
                logger.info(f"⚠️ Comando no reconocido ({consecutive_failures}/3). Texto: '{commandFinal}'")

                # Si fallamos 3 veces seguidas (por ruido o incomprensión), nos vamos a dormir.
                if consecutive_failures >= 3:
                    speak(i18n("msg_i_am_here", "Estoy aquí por si me necesitas. Descanso."), selected_voice_model)
                    update_ui_state("idle", utils.i18n("idle_msg", "Diga 'Fina' para empezar"))
                    break # ROMPER BUCLE -> Volver a esperar "Fina"

                # Análisis del tipo de fallo para dar feedback adecuado:
                
                # Caso A: Ruido corto (< 5 letras) -> Ignorar SILENCIOSAMENTE.
                # (El ventilador suele generar palabras cortas como 'ah', 'eh', 'the')
                if len(commandFinal) < 5:
                    print("🔇 Ruido corto ignorado.")
                    continue 

                # Caso B: Frase articulada pero sin sentido -> Feedback Verbal.
                # Si el usuario habló pero no le entendimos, le avisamos (comportamiento clásico).
                
                # Excepción: Si parece una pregunta para la IA, intentamos responder en lugar de error.
                if is_code_worthy(commandFinal) or len(commandFinal.split()) > 3:
                     # Intentar IA Generativa (Chat)
                     print("🤔 Intentando procesar como charla/pregunta...")
                     
                     # Si la IA responde "Lo siento...", contamos como fallo.
                     # Pero por ahora confiamos en que responderá algo útil.
                     # NO reseteamos fallos aquí para que si charlamos tonterías mucho tiempo sin comandos, igual se duerma eventualmente? 
                     # No, si charla, es interacción válida. Reseteamos.
                     consecutive_failures = 0 
                     
                     if is_code_worthy(commandFinal):
                        print("¡Escribiendo script de python para realizar la tarea!")
                        response = await handle_unknown_request(commandFinal, selected_voice_model)
                        speak(response, selected_voice_model)
                     else:
                        print("¡No fue un comando digno de código!")
                        system_prompt = f"Eres Fina, un asistente útil. Estás hablando con {current_user}."
                        prompt_with_context = f"[Usuario: {current_user}] {commandFinal}"
                        
                        response = await get_mistral_response(prompt_with_context)
                        clean_response = clean_text_for_speech(response)
                        short_response = trim_response(clean_response)
                        speak(short_response, selected_voice_model)
                     
                     continue # Continuar escuchando

                # Caso C: Frase media que no es IA ni comando -> "No te entendí"
                speak(i18n("msg_not_understood_retry", "No te entendí. Intente de nuevo."), selected_voice_model)
                continue
            
            # --- Fin Lógica Ruido ---


            # Core system functions
            if intent == "about":
                info_text = f"Soy {FINA_VERSION}. Fui creada por {FINA_AUTHOR} {FINA_CREATED}. Mi arquitectura modular ha sido completamente renovada."
                update_ui_state("speaking", FINA_VERSION)
                speak(info_text, selected_voice_model)
                continue
            elif intent == "sleep":
                # Dormir ahora no requiere autenticación según pedido del usuario
                sleep_now(selected_voice_model, detect_intent_func=detect_intent)
                continue

            elif intent == "train_voice":
                speak(i18n("msg_voice_train_start", "Iniciando modo de entrenamiento de voz. Preparate para hablar."), selected_voice_model)
                train_script = os.path.join(GLOBAL_ROOT, "train_voice.py")
                subprocess.Popen(["python3", train_script], 
                               env=os.environ, start_new_session=True)
                continue
            elif intent == "change_voice":
                new_voice_path, new_voice_name = cycle_voice_model()
                speak(f"Voz cambiada a {new_voice_name}", new_voice_path)
                continue
            elif intent == "shutdown":
                if is_admin:
                    speak(i18n("msg_shutdown_admin", "Apagando el sistema, Administrador."), selected_voice_model)
                    shutdown(selected_voice_model)
                elif authenticate_user(voice_model=selected_voice_model, speak_func=speak):  # Autenticación con huella fallback
                    speak(i18n("msg_shutdown_query", "¿Realmente queres apagar el sistema?"), selected_voice_model)
                    command = listen(model, language=sys_lang)
                    intent , confidence = detect_intent(command)
                    if intent == "yes":
                        shutdown(selected_voice_model)
                    else:
                        speak(i18n("msg_understood_excl", "Entendido!"), selected_voice_model)
                else:
                    speak(i18n("msg_auth_failed_denied", "Autenticación fallida. Acceso denegado."), selected_voice_model)
            elif intent == "restart_pc":
                if is_admin:
                    speak(i18n("msg_reboot_admin", "Reiniciando el sistema, Administrador."), selected_voice_model)
                    reboot(selected_voice_model)
                elif authenticate_user(voice_model=selected_voice_model, speak_func=speak):
                    speak(i18n("msg_reboot_query", "¿Realmente querés reiniciar la computadora?"), selected_voice_model)
                    command = listen(model, language=sys_lang)
                    intent_confirm, _ = detect_intent(command)
                    if intent_confirm == "yes":
                        reboot(selected_voice_model)
                    else:
                        speak(i18n("msg_understood_excl", "Entendido!"), selected_voice_model)
                else:
                    speak(i18n("msg_auth_failed", "Autenticación fallida."), selected_voice_model)
            elif intent == "suspend":
                # Suspender (require auth)
                suspend(selected_voice_model)
            elif intent == "play_music":
                play_music(selected_voice_model)
            elif intent == "stop_music":
                stop_music(selected_voice_model)
            
            elif intent == "hangup_doorbell":
                speak(i18n("msg_doorbell_hangup", "Cortando comunicación con el timbre..."), selected_voice_model)
                try:
                    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "hangup_doorbell.py")], check=False)
                except Exception as e:
                    logger.error(f"Error colgado timbre: {e}")
            
            elif intent == "pause_music":
                pause_music(selected_voice_model)
            
            elif intent == "next_track":
                next_track(selected_voice_model)
            
            elif intent == "music_volume_down":
                music_volume_down(selected_voice_model)
            
            elif intent == "music_volume_up":
                music_volume_up(selected_voice_model)
            elif intent == "get_weather":
                weather_info = await get_weather()
                speak(weather_info, selected_voice_model)
            
            elif intent == "weather_tomorrow":
                weather_info = await get_weather_tomorrow()
                speak(weather_info, selected_voice_model)
            
            elif intent == "when_will_rain":
                rain_info = await when_will_rain()
                speak(rain_info, selected_voice_model)

            # Email
            
            # --- MOBILE MESSAGING ---
            elif intent == "send_message":
                
                # 1. Contacto
                contacts = load_contacts()
                target_name, target_number = await resolve_contact_proactive(commandFinal, contacts, selected_voice_model, model)
                
                if not target_number:
                    speak(i18n("msg_sms_recipient_query", "¿A quién le envío el mensaje?"), selected_voice_model)
                    target_name_raw = listen(model, language=sys_lang)
                    if target_name_raw:
                        target_name, target_number = await resolve_contact_proactive(target_name_raw, contacts, selected_voice_model, model)
                        
                    if not target_number:
                        speak(i18n("msg_contact_not_found_cancel", "No encontré el contacto. Operación cancelada."), selected_voice_model)
                        continue

                # 2. App
                app_to_use = "whatsapp" # Default
                if "telegram" in commandFinal: app_to_use = "telegram"
                if "signal" in commandFinal: app_to_use = "signal"
                if "sms" in commandFinal or "texto" in commandFinal: app_to_use = "sms"
                
                # 3. Mensaje
                msg_body = ""
                # Intentar extraer "dile que..." del comando inicial SOLO si mencionamos un contacto conocido
                markers = ["dile que ", "diciendo que ", "que diga ", "mensaje "]
                for m in markers:
                    if m in commandFinal:
                        possible_msg = commandFinal.split(m, 1)[1].strip()
                        # LIMPIEZA: Si el mensaje resultante es solo el nombre del contacto o "a [nombre]", lo ignoramos
                        # Esto evita que "envia un mensaje a PC Producciones" detecte "a PC Producciones" como el texto a enviar.
                        clean_msg = possible_msg.lower().replace(f"a {target_name.lower()}", "").replace(target_name.lower(), "").strip()
                        # Quitar también palabras de relleno comunes al final del comando
                        clean_msg = clean_msg.replace("por whatsapp", "").replace("por sms", "").replace("whatsapp", "").strip()
                        
                        if len(clean_msg) > 1:
                            msg_body = clean_msg
                        break
                
                # Si no hay cuerpo de mensaje, PREGUNTAR (como le gusta al usuario)
                if not msg_body or len(msg_body) < 2:
                    speak(f"¿Qué querés que le diga a {target_name}?", selected_voice_model)
                    msg_body = listen(model, language=sys_lang)
                
                if msg_body and len(msg_body) > 1:
                    speak(f"Enviando mensaje a {target_name} por {app_to_use}...", selected_voice_model)
                    # Delegar al motor de la UI (Tauri) para usar el mismo método que la Agenda
                    send_ui_command("fina-send-message", {
                        "number": target_number, 
                        "message": msg_body, 
                        "app": app_to_use
                    })
                else:
                    speak(i18n("msg_cancel_no_msg", "Cancelado. No se capturó ningún mensaje."), selected_voice_model)

            elif intent == "make_call":
                
                contacts = load_contacts()
                target_name, target_number = await resolve_contact_proactive(commandFinal, contacts, selected_voice_model, model)
                
                if not target_number:
                     speak(i18n("msg_call_recipient_query", "¿A quién llamo?"), selected_voice_model)
                     target_name_raw = listen(model, language=sys_lang)
                     if target_name_raw:
                        target_name, target_number = await resolve_contact_proactive(target_name_raw, contacts, selected_voice_model, model)
                
                if not target_number:
                    speak(i18n("msg_contact_not_found", "No encontré el contacto."), selected_voice_model)
                    continue
                
                if target_number:
                    speak(f"Llamando a {target_name}...", selected_voice_model)
                    # Usar intent de llamada
                    adb_cmd = ["adb", "shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{target_number}"]
                    # Nota: ACTION_CALL requiere permiso CALL_PHONE en el manifest de la app que lanza (que es shell), 
                    # usualmente shell tiene permisos. Si falla, usar DIAL.
                    subprocess.run(adb_cmd)
                else:
                    speak(i18n("msg_contact_not_found", "No encontré el contacto."), selected_voice_model)

            elif intent == "read_email":
                speak(i18n("msg_checking_inbox", "Revisando tu bandeja de entrada..."), selected_voice_model)
                unread = count_recent_unread_emails(imap_server, EMAIL_USER, EMAIL_PASSWORD, 7)
                speak(f"Tienes {unread} correos no leídos en los últimos 7 días", selected_voice_model)
                speak(i18n("msg_read_emails_query", "¿Quieres que los lea?"), selected_voice_model)
                reply = listen(model, language=sys_lang)
                if detect_intent(reply.lower())[0] == "yes":
                    from_, subject, date_, unread_msg_nums = read_recent_unread_emails(imap_server, EMAIL_USER, EMAIL_PASSWORD, 7, 4)
                    command = f"Summarize this mail \n_from_: {from_} \ndate: {date_}\nSubject: {subject}"
                    response = await get_mistral_response(command)
                    speak(clean_text_for_speech(response), selected_voice_model)

            elif intent == "send_email":
                contacts = load_contacts()
                speak(i18n("msg_email_recipient_query", "¿A quién querés enviar el correo?"), selected_voice_model)
                name = clean_input(listen(model, language=sys_lang))
                email = contacts.get(name)
                if email:
                    speak(i18n("msg_email_subject_query", "¿Asunto?"), selected_voice_model)
                    subject = listen(model, language=sys_lang)
                    speak(i18n("msg_email_body_query", "¿Cuerpo del mensaje?"), selected_voice_model)
                    body = listen(model, language=sys_lang)
                    speak(i18n("msg_check_grammar_query", "¿Querés que revise faltas de ortografía'?"), selected_voice_model)
                    if detect_intent(listen(model, language=sys_lang).lower())[0] == "yes":
                        body = await get_mistral_response(f"Fix grammar: {body}")
                    send_email(EMAIL_USER, EMAIL_PASSWORD, email, subject, body)
                    speak(f"Correo enviado a {name}.", selected_voice_model)
                else:
                    speak(f"No se encontró correo para {name}.", selected_voice_model)

            # Web search
            elif intent == "web_search":
                speak(i18n("msg_web_search_query", "¿Qué tengo que buscar?"), selected_voice_model)
                query = listen(model, language=sys_lang)
                if query:
                    # En utils.py, web_search ahora devuelve (mensaje, link)
                    result = web_search(query)
                    if isinstance(result, tuple) and len(result) == 2:
                        output, link = result
                        speak(output, selected_voice_model)
                    else:
                        # Fallback por si acaso
                        speak(f"Buscando {query} en Google.", selected_voice_model)
                else:
                    speak("No te escuché, búsqueda cancelada.", selected_voice_model)

            # Assistant Utility Features
            elif intent == "change_wallpaper":
                change_wallpaper(selected_voice_model)

            elif intent == "add_reminder":
                speak(i18n("msg_reminder_content_query", "¿Qué debo recordarte?"), selected_voice_model)
                task = listen(model, language=sys_lang)
                speak(i18n("msg_reminder_time_query", "¿Cuándo debo recordártelo? (ejemplo: 14:30)"), selected_voice_model)
                time_str = listen(model, language=sys_lang)
                result = add_reminder(task, time_str, selected_voice_model)
                speak(result, selected_voice_model)

            elif intent == "list_reminders":
                result = list_reminders()
                speak(result, selected_voice_model)

            elif intent == "news":
                # Usar la nueva función robusta basada en RSS
                news = get_proactive_briefing(selected_voice_model)
                speak(news, selected_voice_model)

            elif intent == "battery_status":
                percentage , status = get_battery_status()
                speak(f"Batería restante {percentage} y {status}", selected_voice_model)

            elif intent == "wiki_summary":
                speak(i18n("msg_wiki_query", "¿Qué debo buscar en Wikipedia?"), selected_voice_model)
                query = listen(model, language=sys_lang)
                result = wiki_summary(query)
                speak(result, selected_voice_model)

            elif intent == "get_ip":
                speak(get_ip(), selected_voice_model)

            elif intent == "get_stats":
                stats = get_system_stats()
                speak(stats, selected_voice_model)

            elif intent == "location_context":
                # Extraer la habitación dicha para responder con contexto
                locs = ["dormitorio", "living", "cocina", "baño", "sala", "comedor", "habitación", "pieza", "patio", "lavadero"]
                found_loc = "esa habitación"
                cmd_lower = commandFinal.lower()
                for l in locs:
                    if l in cmd_lower:
                        # Pequeño ajuste gramatical
                        if l in ["cocina", "sala", "habitación", "pieza"]:
                            found_loc = "la " + l
                        else:
                            found_loc = "el " + l
                        break
                speak(f"¿Qué quieres que haga en {found_loc}?", selected_voice_model)

            elif intent == "translate":
                speak(i18n("msg_translate_query", "¿Qué texto debo traducir?"), selected_voice_model)
                text = listen(model, language=sys_lang)
                speak(i18n("msg_translate_lang", "¿A qué idioma?"), selected_voice_model)
                lang = listen(model, language=sys_lang)
                translated = translate_text(text, lang)
                speak(translated, selected_voice_model)

            elif intent == "start_timer":
                minutes = 0.0
                text_to_process = commandFinal.lower()
                
                # Helper para extraer valor
                def extract_val(txt):
                    # 1. Digitos
                    nums = re.findall(r'(\d+)', txt)
                    if nums: return float(nums[0])
                    # 2. Palabras
                    val = text_to_number_es(txt)
                    if val: return float(val)
                    return 0.0

                val = extract_val(text_to_process)
                
                # Si encontró valor en el comando inicial
                if val > 0:
                    if "segundo" in text_to_process:
                        minutes = val / 60.0
                    else:
                        minutes = val
                else:
                    # Preguntar si no se entendió
                    speak(i18n("msg_timer_minutes", "¿Cuántos minutos?"), selected_voice_model)
                    resp_text = listen(model, language=sys_lang)
                    if resp_text:
                        val_resp = extract_val(resp_text)
                        if val_resp > 0:
                            # Asumimos minutos si pregunta "¿cuantos minutos?"
                            # Pero si el usuario dice "30 segundos", intentar respetar
                            if "segundo" in resp_text.lower():
                                minutes = val_resp / 60.0
                            else:
                                minutes = val_resp
                
                if minutes > 0:
                    # Feedback hablado de lo que entendió
                    sec_display = int(minutes * 60)
                    if sec_display < 60:
                        msg = f"Iniciando en {sec_display} segundos."
                    else:
                        try:
                            val_round = float(minutes)
                            msg = f"Iniciando en {round(val_round, 1)} minutos."
                        except:
                            msg = f"Iniciando en {minutes} minutos."
                        
                    start_timer(minutes * 60, "¡Tiempo cumplido!", selected_voice_model)
                else:
                    speak(i18n("msg_timer_err", "No entendí el tiempo para el temporizador."), selected_voice_model)

            elif intent == "joke":
                speak(tell_joke(), selected_voice_model)

            elif intent == "create_note":
                speak(i18n("msg_note_content", "¿Qué debo escribir?"), selected_voice_model)
                note = listen(model, language=sys_lang)
                result = create_note(note)
                speak(result, selected_voice_model)

            elif intent == "current_datetime":
                speak(get_current_datetime(), selected_voice_model)

            elif intent == "youtube_search":
                speak(i18n("msg_youtube_query", "¿Qué busco en YouTube?"), selected_voice_model)
                query = listen(model, language=sys_lang)
                # Open YouTube search in Chrome browser
                search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                try:
                    subprocess.Popen(["google-chrome", search_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    speak(i18n("msg_youtube_opening_chrome").format(query=query), selected_voice_model)
                except FileNotFoundError:
                    # Fallback to default browser
                    subprocess.run(f'firefox "{search_url}"', shell=True)
                    speak(i18n("msg_youtube_opening_firefox").format(query=query), selected_voice_model)

            elif intent == "find_file":
                speak(i18n("msg_find_file_query", "¿Qué archivo estás buscando?"), selected_voice_model)
                filename = listen(model, language=sys_lang)
                path = find_file(filename)
                speak(path, selected_voice_model)

            elif intent == "clipboard":
                content = get_clipboard()
                speak(f"El portapapeles contiene: {content}", selected_voice_model)

            elif intent == "convert_currency":
                speak(i18n("msg_currency_query", "¿Cuánto y qué moneda?"), selected_voice_model)
                info = listen(model, language=sys_lang)
                parts = info.split()
                if len(parts) == 3:
                    amount, from_curr, to_curr = parts
                    result = await convert_currency(amount, from_curr.upper(), to_curr.upper())
                    speak(result, selected_voice_model)
                else:
                    speak(i18n("msg_currency_err", "Por favor di la cantidad, moneda origen y destino."), selected_voice_model)

            elif intent == "generate_image":
                speak(i18n("msg_image_gen_query", "¿Qué imagen debo generar?"), selected_voice_model)
                prompt = listen(model, language=sys_lang)
                image_url = await generate_image(prompt)
                speak(f"Imagen generada: {image_url}", selected_voice_model)

            elif intent == "delete_notes":
                result = self_destruct()
                speak(result, selected_voice_model)

            elif intent == "read_pdf":
                speak(i18n("msg_pdf_path_query", "Introduce la ruta del archivo PDF"), selected_voice_model)
                path = listen(model, language=sys_lang)
                text = read_pdf(path)
                speak(text[:500], selected_voice_model)  # Read a preview

            elif intent == "update_assistant":
                result = update_assistant_code()
                speak(result, selected_voice_model)

            elif intent == "greeting":
                speak(get_time_based_greeting(), selected_voice_model)

            elif intent == "uptime":
                speak(get_uptime(), selected_voice_model)

            elif intent == "port_scan":
                speak(i18n("msg_scan_target_query", "¿Qué IP o host escaneo?"), selected_voice_model)
                host = listen(model, language=sys_lang)
                result = scan_ports(host)
                speak(result, selected_voice_model)

            elif intent == "public_ip":
                ip = get_public_ip()
                speak(f"Tu IP pública es {ip}", selected_voice_model)

            elif intent == "wifi_scan":
                result = scan_wifi()
                speak(result, selected_voice_model)

            elif intent == "save_voice_note":
                speak(i18n("msg_voice_note_query", "Di tu nota."), selected_voice_model)
                text = listen(model, language=sys_lang)
                result = save_voice_note(text)
                speak(result, selected_voice_model)

            elif intent == "motivation":
                speak(get_daily_affirmation(), selected_voice_model)

            elif intent == "battery_saver":
                speak(i18n("msg_battery_saver_query", "¿Activo o desactivo el ahorro de batería?"), selected_voice_model)
                mode = listen(model, language=sys_lang).lower()
                result = toggle_battery_saver(mode)
                speak(result, selected_voice_model)

            elif intent == "play_ambient":
                speak(i18n("msg_ambient_sound_query", "¿Qué sonido ambiental? (lluvia, bosque, océano)"), selected_voice_model)
                type_ = listen(model, language=sys_lang)
                result = play_ambient_sound(selected_voice_model, type_)
                # El speak ya sucede dentro de la función para el feedback imediato

            elif intent == "take_screenshot":
                result = take_screenshot()
                speak(result, selected_voice_model)

            elif intent == "take_photo":
                speak(i18n("msg_ready_photo", "Listo?"), selected_voice_model)
                user_status = listen(model="tiny", language=sys_lang)
                intent , confidence = detect_intent(user_status)
                if intent == "yes":
                    speak(i18n("msg_cheese", "cheese!"), selected_voice_model)
                    result, path = take_webcam_photo(selected_voice_model)
                    speak(result, selected_voice_model)
                    speak(i18n("msg_open_photo_query", "¿Querés que abra tu foto?"), selected_voice_model)
                    user_choice = listen(model="tiny", language=sys_lang)
                    intent , confidence = detect_intent(user_choice)
                    if intent == "yes":
                        command = f'firefox {path}'
                        subprocess.run(command, shell = True, check = True)
                        speak(i18n("msg_check_firefox", "por favor revisa firefox"), selected_voice_model)
                    else:
                        speak(i18n("msg_ok", "okay"), selected_voice_model)
                else:
                    speak(i18n("msg_ok", "okay"), selected_voice_model)

            elif intent == "backup_files":
                result = backup_files()
                speak(result, selected_voice_model)

            elif intent == "download_instagram":
                speak(i18n("msg_instagram_reel_query", "Pegue la URL del reel de Instagram."), selected_voice_model)
                url = listen(model, language=sys_lang)
                result = download_instagram_reel(selected_voice_model, url)
                speak(result, selected_voice_model)

            elif intent == "toggle_night_mode":
                result = toggle_night_mode()
                speak(result, selected_voice_model)
            elif intent == "increase_volume":
                speak(increase_volume(), selected_voice_model)
            elif intent == "decrease_volume":
                speak(decrease_volume(), selected_voice_model)
            elif intent == "increase_brightness":
                speak(increase_brightness(), selected_voice_model)
            elif intent == "decrease_brightness":
                speak(decrease_brightness(), selected_voice_model)

            elif intent == "tv_increase_brightness":
                speak(i18n("msg_tv_brightness_err", "Lo siento, aún no puedo controlar el brillo del televisor."), selected_voice_model)
            
            elif intent == "tv_decrease_brightness":
                speak(i18n("msg_tv_brightness_err", "Lo siento, aún no puedo controlar el brillo del televisor."), selected_voice_model)
            
            elif intent == "lights_increase_brightness":
                lights_set_brightness_cmd(selected_voice_model, level=80)
            
            elif intent == "lights_decrease_brightness":
                lights_set_brightness_cmd(selected_voice_model, level=20)
            
            elif intent == "open_spotify":
                try:
                    subprocess.Popen(["harmonymusic"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    speak(i18n("msg_harmonymusic_opening", "Abriendo Harmony Music"), selected_voice_model)
                except FileNotFoundError:
                    speak(i18n("msg_harmonymusic_not_found", "Harmony Music no está instalado"), selected_voice_model)
                except Exception as e:
                    logger.error(f"Error launching Harmony Music: {e}")
                    speak(i18n("msg_harmonymusic_error", "No pude abrir Harmony Music"), selected_voice_model)
            
            elif intent == "open_audio_editor":
                try:
                    subprocess.Popen(["audacity"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    speak(i18n("msg_audacity_opening", "Abriendo Audacity"), selected_voice_model)
                except FileNotFoundError:
                    speak(i18n("msg_audacity_not_found", "Audacity no está instalado"), selected_voice_model)
                except Exception as e:
                    logger.error(f"Error launching Audacity: {e}")
                    speak(i18n("msg_audacity_error", "No pude abrir Audacity"), selected_voice_model)
            
            elif intent == "open_app":
                speak(i18n("msg_app_open_query", "¿Qué aplicación quieres abrir?"), selected_voice_model)
                app_name = listen(model, language=sys_lang)
                result = open_app(app_name)
                speak(result, selected_voice_model)
            
            elif intent == "close_app":
                speak(i18n("msg_app_close_query", "¿Qué aplicación quieres cerrar?"), selected_voice_model)
                app_name = listen(model, language=sys_lang)
                result = close_app(app_name)
                speak(result, selected_voice_model)
            
            elif intent == "turn_on_tv":
                turn_on_tv(selected_voice_model, commandFinal)
            
            elif intent == "turn_off_tv":
                turn_off_tv(selected_voice_model, commandFinal)

            elif intent == "tv_volume_up":
                steps = text_to_number_es(commandFinal) or 5
                tv_volume_up_cmd(selected_voice_model, steps)
            
            elif intent == "tv_volume_down":
                steps = text_to_number_es(commandFinal) or 5
                tv_volume_down_cmd(selected_voice_model, steps)

            elif intent == "tv_mute":
                tv_mute_cmd(selected_voice_model, action="mute")
            
            elif intent == "tv_unmute":
                tv_mute_cmd(selected_voice_model, action="unmute")
            
            elif intent == "tv_channel_up":
                tv_channel_up_cmd(selected_voice_model)
            
            elif intent == "tv_channel_down":
                tv_channel_down_cmd(selected_voice_model)

            elif intent == "tv_open_app":
                # Extract app name from command
                ignored_words = ["abre", "pon", "inicia", "ejecuta", "quiero", "ver", "en", "la", "tele", "tv", "television", "aplicación", "el", "la"]
                target = commandFinal
                for word in ignored_words:
                    target = target.replace(word, " ")
                target = target.strip()
                tv_open_app_cmd(target, selected_voice_model)

            elif intent == "tv_exit_app":
                tv_exit_app_cmd(selected_voice_model)
                
            elif intent == "turn_on_deco":
                turn_on_deco(selected_voice_model, commandFinal)
            
            elif intent == "turn_off_deco":
                turn_off_deco(selected_voice_model, commandFinal)

            elif intent == "deco_volume_up":
                steps = 5
                numbers = re.findall(r'\d+', commandFinal)
                if numbers:
                    try:
                        steps = min(int(numbers[0]), 20)
                    except: pass
                deco_volume_up_cmd(selected_voice_model, steps)
            
            elif intent == "deco_volume_down":
                steps = 5
                numbers = re.findall(r'\d+', commandFinal)
                if numbers:
                    try:
                        steps = min(int(numbers[0]), 20)
                    except: pass
                deco_volume_down_cmd(selected_voice_model, steps)
            
            elif intent == "deco_mute" or intent == "deco_unmute":
                deco_mute_cmd(selected_voice_model)
            
            elif intent == "deco_channel_up":
                deco_channel_up_cmd(selected_voice_model)
            
            elif intent == "deco_channel_down":
                deco_channel_down_cmd(selected_voice_model)
            
            elif intent == "deco_set_channel":
                # Buscar número directo
                numbers = re.findall(r'\d+[.,]?\d*', commandFinal.replace(" punto ", "."))
                if numbers:
                    channel = numbers[0]
                    deco_set_channel_cmd(channel, selected_voice_model)
                else:
                    triggers = ["pon el canal", "cambia al canal", "vete al canal", "quiero ver el canal", "ir al canal", "selecciona el canal", "ponerme en el canal", "pon", "ver"]
                    channel_name = commandFinal
                    for t in triggers:
                        if channel_name.startswith(t):
                            channel_name = channel_name.replace(t, "", 1).strip()
                            break
                    if channel_name:
                         deco_set_channel_cmd(channel_name, selected_voice_model)
                    else:
                        speak(i18n("msg_deco_channel_query", "¿Qué canal pongo?"), selected_voice_model)

            elif intent == "tv_set_input":
                target_input = commandFinal.replace("pon el", "").replace("pon la", "").replace("cambia a la entrada", "").replace("entrada", "").strip()
                tv_set_input_cmd(target_input, selected_voice_model)
            elif intent == "check_doorbell":
                get_doorbell_status_cmd(selected_voice_model)
            elif intent == "show_doorbell_camera":
                show_doorbell_image(selected_voice_model)
            elif intent == "show_doorbell_stream":
                show_doorbell_stream(selected_voice_model)
            
            elif intent == "tv_set_channel":
                # 1. Buscar número directo (Prioridad)
                numbers = re.findall(r'\d+[.,]?\d*', commandFinal.replace(" punto ", "."))
                if numbers:
                    channel = numbers[0]
                    tv_set_channel_cmd(channel, selected_voice_model)
                else:
                    # 2. Si no hay número, asumir que es el nombre del canal
                    # Limpiamos las frases gatillo para quedarnos con el nombre
                    # Frases en intents.json: "pon el canal", "cambia al canal", "vete al canal", "quiero ver el canal"
                    triggers = [
                        "pon el canal", "cambia al canal", "vete al canal", 
                        "quiero ver el canal", "ir al canal", "selecciona el canal", 
                        "ponerme en el canal", "pon", "ver"
                    ]
                    
                    channel_name = commandFinal
                    for t in triggers:
                        if channel_name.startswith(t):
                            channel_name = channel_name.replace(t, "", 1).strip()
                            break
                    
                    if channel_name:
                         tv_set_channel_cmd(channel_name, selected_voice_model)
                    else:
                        speak(i18n("msg_tv_channel_query", "¿Qué canal pongo?"), selected_voice_model)
                        num_response = listen(model, language=sys_lang)
                        if num_response:
                             # Intentar buscar número o usar texto completo
                             more_nm = re.findall(r'\d+[.,]?\d*', num_response.replace(" punto ", "."))
                             if more_nm:
                                 tv_set_channel_cmd(more_nm[0], selected_voice_model)
                             else:
                                 # Asumir que respondió con el nombre
                                 tv_set_channel_cmd(num_response, selected_voice_model)
            
            elif intent == "tv_open_app":
                speak(i18n("msg_tv_app_query", "¿Qué aplicación en la tele?"), selected_voice_model)
                # Parse app from previous command if possible, or ask
                # The intent detection often misses the slots, so it is safer to ask or try to parse 'command'
                # If command was 'abre youtube en la tele', we can try to extract 'youtube'
                
                target_app = None
                words = commandFinal.split()
                if "youtube" in words: target_app = "youtube"
                elif "netflix" in words: target_app = "netflix"
                elif "spotify" in words: target_app = "spotify"
                elif "prime" in words: target_app = "prime"
                elif "disney" in words: target_app = "disney"
                elif "flow" in words: target_app = "flow"
                elif "lista" in words: target_app = "lista"
                
                if target_app:
                   tv_open_app_cmd(target_app, selected_voice_model)
                else:
                   # Fallback: ask specifically
                   app_response = listen(model, language=sys_lang)
                   if app_response:
                       tv_open_app_cmd(app_response, selected_voice_model)
            
            elif intent == "tv_exit_app":
                tv_exit_app_cmd(selected_voice_model)

            elif intent == "tv_set_volume":
                # Buscar número directo
                numbers = re.findall(r'\d+', commandFinal)
                if numbers:
                    tv_set_volume_cmd(int(numbers[0]), selected_voice_model)
                else:
                    speak("¿A qué nivel de volumen quieres poner la tele?", selected_voice_model)
            
            elif intent == "deco_set_volume":
                # Buscar número directo
                numbers = re.findall(r'\d+', commandFinal)
                if numbers:
                    deco_set_volume_cmd(int(numbers[0]), selected_voice_model)
                else:
                    speak("¿A qué nivel quieres poner el volumen del deco?", selected_voice_model)

            elif intent == "deco_open_app":
                 # Extraer app
                ignored_words = ["abre", "pon", "inicia", "ejecuta", "quiero", "ver", "en", "el", "deco", "decodificador", "aplicación"]
                target = commandFinal
                for word in ignored_words:
                    target = target.replace(word, " ")
                target = target.strip()
                if target:
                    deco_open_app_cmd(target, selected_voice_model)
                else:
                    speak("¿Qué aplicación quieres abrir en el decodificador?", selected_voice_model)

            elif intent == "deco_exit_app":
                deco_exit_app_cmd(selected_voice_model)

            elif intent == "deco_set_input":
                target_input = commandFinal.replace("pon el deco en", "").replace("pon la", "").replace("cambia a la entrada", "").replace("entrada", "").strip()
                deco_set_input_cmd(target_input, selected_voice_model)

            elif intent == "ac_control":
                # Llama a la función asíncrona de control de aire universal
                asyncio.create_task(perform_ac_control(selected_voice_model, commandFinal))

            elif intent == "scan_iot":
                scan_network_cmd(selected_voice_model)

            elif intent == "robot_clean":
                robot_clean_cmd(selected_voice_model)

            elif intent == "lights_on":
                lights_on_cmd(selected_voice_model)

            elif intent == "lights_off":
                lights_off_cmd(selected_voice_model)

            elif intent == "lock_door":
                lock_door_cmd(selected_voice_model)

            elif intent == "unlock_door":
                unlock_door_cmd(selected_voice_model)

            elif intent == "open_blinds":
                blinds_open_cmd(selected_voice_model)

            elif intent == "close_blinds":
                blinds_close_cmd(selected_voice_model)

            elif intent == "start_watering":
                start_watering_cmd(selected_voice_model)

            elif intent == "check_solar_production":
                energy_status_cmd(selected_voice_model)

            elif intent == "fridge_status":
                fridge_status_cmd(selected_voice_model)

            elif intent == "fridge_inventory":
                fridge_inventory_cmd(selected_voice_model)

            elif intent == "set_fridge_temp":
                # Extraer temperatura del comando
                nums = re.findall(r'\d+', commandFinal)
                if nums:
                    fridge_set_temp_cmd(selected_voice_model, nums[0])
                else:
                    speak("¿Qué temperatura quieres poner?", selected_voice_model)

            elif intent == "lock_status":
                lock_status_cmd(selected_voice_model)

            elif intent == "robot_status":
                robot_status_cmd(selected_voice_model)

            elif intent == "appliance_status":
                appliance_status_cmd(selected_voice_model)
                
# main entry point
def handle_exit(signum, frame):
    """Manejador para la terminación limpia del programa."""
    logger.info("Solicitud de terminación recibida. Cerrando el asistente...")
    print("\n¡Hasta luego!")
    
    # Detener motor de voz
    try:
        stop_voice_engine()
        logger.info("Motor de voz detenido")
    except Exception as e:
        logger.error(f"Error deteniendo motor de voz: {e}")
    
    # Matar procesos de Piper y Aplay que puedan quedar huérfanos
    try:
        subprocess.run(["pkill", "-9", "piper"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-9", "aplay"], stderr=subprocess.DEVNULL)
    except: pass
    
    # Limpiar procesos hijos huérfanos (crucial para plugins)
    try:
        subprocess.run(["pkill", "-P", str(os.getpid())], stderr=subprocess.DEVNULL)
    except: pass
    
    logger.info("Asistente detenido correctamente")
    
    sys.exit(0)

if __name__ == "__main__":
    import signal
    
    # Configurar manejadores de señales
    signal.signal(signal.SIGINT, handle_exit)  # Captura Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit)  # Captura señales de terminación
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Manejo limpio de Ctrl+C
        handle_exit(None, None)
    except Exception as e:
        logger.error(f"Excepción no manejada en el bucle principal: {e}", exc_info=True)
        print("Ocurrió un error crítico. Por favor revisa los logs para más detalles.")
        sys.exit(1)
    finally:
        # Cualquier limpieza adicional iría aquí
        logger.info("Asistente detenido correctamente")
