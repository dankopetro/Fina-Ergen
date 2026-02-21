import sys
import os

# -------------------------------------------------------------
# FORZAR CARGA LOCAL (Plugins, Utils)
# Evita cargar versiones viejas instaladas en site-packages
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    print(f"🔧 Forzando carga local desde: {current_dir}")
    sys.path.insert(0, current_dir)
# -------------------------------------------------------------

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
# Importamos update_ui_state y logger desde utils para evitar duplicación
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
    ensure_tv_is_on,    tv_set_input_cmd, get_doorbell_status_cmd, show_doorbell_image, 
    show_doorbell_stream, send_ui_command,
    CONFIG_DIR, SETTINGS_PATH, USER_DATA_PATH, CONTACTS_PATH, CONFIG_PY_PATH, load_config
)
from auth.fingerprint_auth import authenticate_user
from auth.voice_auth import VoiceAuthenticator
from fina_plugin_integration import setup_plugins
# --- CONFIG LOADING [SAFE] ---
config, CONFIG_FOUND = load_config()

# update_ui_state removido (ahora importado de utils)

def speak(text, model=None, sink=None):
    """Local wrapper to delegate speech and UI updates to utils"""
    if not text: return
    
    # 2. Actual Voice Output (will update UI in background worker for sync)
    try:
        if sink:
            utils_speak(text, model, sink=sink)
        else:
            utils_speak(text, model)
        # Small sleep to allow worker thread to take context if needed
        time.sleep(0.05)
    except Exception as e:
        print(f"Error en voz: {e}")

EMAIL_USER = config.EMAIL_USER
EMAIL_PASSWORD = config.EMAIL_PASSWORD
imap_server = 'imap.gmail.com' 

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
                    if len(qw) < 3: continue
                    ratio = difflib.SequenceMatcher(None, part, qw).ratio()
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
        from utils import text_to_number_es
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
FINA_VERSION = "Fina Ergen v 3.5.2"
FINA_AUTHOR = "Dankopetro"
FINA_CREATED = "el 30 de Enero de 2026 a las 20:07"

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
# Autonomía total: Phoenix solo mira dentro de su carpeta
GLOBAL_ROOT = PROJECT_ROOT

# Voice model paths - now relative to project directory
# Modelos de voz en español
VOICE_MODELS = {
    "ElevenLabs": "ElevenLabs",                                                        # ElevenLabs API
    "Daniela": os.path.join(PROJECT_ROOT, "voice_models", "es_AR-daniela-high.onnx"),  # Argentina - Femenina
    "Claude": os.path.join(PROJECT_ROOT, "voice_models", "es_MX-claude-high.onnx"),    # México - Masculina
    "Laura": os.path.join(PROJECT_ROOT, "voice_models", "es_MX-laura-high.onnx"),      # México - Femenina
    "Miro": os.path.join(PROJECT_ROOT, "voice_models", "miro_es-ES.onnx"),             # España - Masculina
}

# Default voice model - Daniela (voz femenina argentina)
DEFAULT_VOICE = os.path.join(PROJECT_ROOT, "voice_models", "es_AR-daniela-high.onnx")

# Voice change functionality
current_voice_index = 0
voice_model_names = list(VOICE_MODELS.keys())
# Set Daniela as the default
if "Daniela" in voice_model_names:
    current_voice_index = voice_model_names.index("Daniela")

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

# --- Setup checks for required files ---
if not CONFIG_FOUND:
    print("\n⚠️ AVISO: Fina Ergen está en MODO INICIAL.")
    print("  - No se encontró config.py. Esto es normal si es la primera vez.")
    print("  - El sistema funcionará con capacidades limitadas hasta ser configurado.")
    # No salimos: sys.exit(1) removido

# Logger Setup (Centralized in Ergen Root)
# Logger Setup Centralizado en utils.py
# Simplemente obtenemos el logger (utils ya configuró el root)
# logger = logging.getLogger("FinaMain") # Ya importado arriba
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
        update_ui_state("idle", "Inicializando sistemas...")
        print("DEBUG: [1] Inicializando Intents...")
        
        # 1. Precargar Intents (Sentence Transformers es pesado)
        from intent_classifier import _initialize_model, detect_intent
        _initialize_model()
        print("DEBUG: [1] Intents Cargados.")
        # "Warm-up" del clasificador
        detect_intent("hola", confidence_threshold=0.1)
        
        # 2. Precargar Vosk
        print("DEBUG: [2] Cargando Vosk...")
        import utils
        utils.load_vosk_model("es")
        print("DEBUG: [2] Vosk Cargado.")

        # --- INICIALIZAR PLUGINS ---
        print("🔌 Inicializando Plugins...")
        plugin_integration = None
        try:
            # Usamos una lambda para pasar la voz por defecto y el sink opcional
            plugin_integration = setup_plugins(speak_callback=lambda text, sink=None: speak(text, DEFAULT_VOICE, sink=sink))
        except Exception as e:
            logger.error(f"Error inicializando plugins: {e}")
        # ---------------------------
        
        # 3. Saludo inicial una vez todo está en memoria
        # update_ui_state("speaking", "Sistema listo")
        
        # 4. Inicializar motor de Biometría de Voz (Robusto)
        print("🧠 Inicializando reconocimiento de voz...")
        voice_auth = None
        try:
            voice_auth = VoiceAuthenticator()
            print("✅ Biometría cargada.")
        except Exception as e:
            print(f"⚠️ Biometría falló (saltando): {e}")
        
        # 5. (Verificación de TV eliminada para mejorar velocidad de arranque)
        
        # 6. Watchdog y Monitor de Timbre son gestionados por el script de arranque global
        # para evitar procesos duplicados.

        
        # Secuencia de inicialización completa
        if CONFIG_FOUND:
            speak("Sistemas listos. Diga Fina para empezar.", DEFAULT_VOICE)
        else:
            # Mensaje de bienvenida para usuario nuevo
            msg = "Bienvenido a Fina Ergen. No detecto tu archivo de configuración. Por favor, consulta el manual de usuario para configurarme por primera vez. Me quedaré en modo de espera limitado."
            print(f"📢 {msg}")
            # Intentar usar la primera voz disponible si la de AR no está
            speak(msg, DEFAULT_VOICE)
            
        update_ui_state("idle", None)
    except Exception as e:
        logger.error(f"Error en inicialización: {e}")
        # Asegurar que al menos el estado no quede roto
        update_ui_state("idle", "ERROR EN ARRANQUE")

    proactive_briefing_given = False
    user_is_authenticated = False
    while True:
        model = "tiny"

        # Wake word loop (esperando "Fina")
        while True:
            update_ui_state("idle", None)
            selected_voice_model, current_voice_name = get_current_voice_info()
            audio_input = listen(model, language="es")  # Cambio a español
            if not audio_input:
                continue
            
            update_ui_state("listening", "Escuchando...")
            command = audio_input.lower()
            intent, confidence = detect_intent(command)
            
            # Verificar wake word con sensibilidad original (para que escuche de lejos)
            if intent == "wake_up" and confidence > 0.6:
                if not user_is_authenticated:
                    update_ui_state("authenticating", "Esperando autenticación...")
                    temp_voice_model, _ = get_current_voice_info()
                    if authenticate_user(voice_model=temp_voice_model, speak_func=speak):
                        user_is_authenticated = True
                        update_ui_state("speaking", "Autenticación Exitosa")
                        speak("Autenticación Exitosa", temp_voice_model)
                    else:
                        speak("Autenticación fallida.", temp_voice_model)
                        continue
                
                # Si ya está autenticado o acaba de autenticarse con éxito
                update_ui_state("speaking", "Esperando Comando...")
                speak("Esperando Comando...", temp_voice_model if 'temp_voice_model' in locals() else selected_voice_model)
                break 
            else:
                # Si se detectó ruido pero no fue la palabra clave con confianza
                if len(command.split()) > 0:
                   speak("Intente de nuevo.", selected_voice_model)
                continue

        # Always reset to Daniela after wake-up
        if "Daniela" in voice_model_names:
            current_voice_index = voice_model_names.index("Daniela")
        selected_voice_model, current_voice_name = get_current_voice_info()
        # No repetimos el saludo si ya dijimos "Esperando comando" o lo combinamos
        # speak(get_time_based_greeting(), selected_voice_model)
        
        # Proactive briefing (Restaurado y limpiado)
        if not proactive_briefing_given:
            try:
                # Eliminada la actualización redundante previa.
                # update_ui_state("speaking", "¿Querés las noticias?") <- ESTA ERA LA DUPLICADA
                
                speak("¿Querés que te cuente las noticias?", selected_voice_model)
                
                update_ui_state("listening", "Esperando respuesta...")
                response = listen(model, language="es")
                if response:
                    intent_response, _ = detect_intent(response.lower())
                    if intent_response == "yes":
                        from utils import get_proactive_briefing
                        update_ui_state("speaking", "Preparando noticias...")
                        # Usar la nueva función robusta
                        briefing = get_proactive_briefing(selected_voice_model)
                        speak(briefing, selected_voice_model)
                    else:
                        speak("Entendido, continuemos.", selected_voice_model)
            except Exception as e:
                logger.warning(f"Could not deliver proactive briefing: {e}")
            proactive_briefing_given = True

        # Main conversation loop
        consecutive_failures = 0
        while True:
            # Mantener el texto anterior (respuesta de Fina) mientras escuchamos
            update_ui_state("listening", None)
            
            # Listen WITH audio capture for verification
            listen_result = listen(model, language="es", timeout=20, return_audio=True)
            
            if not listen_result or listen_result[0] is None:
                # Si no hay comando (timeout), volvemos al estado idle (Azul Profundo)
                # update_ui_state("speaking", "Me quedo atenta")
                speak("Descanso el oido pero me quedo atenta por si me necesitás. Hasta luego.", selected_voice_model)
                update_ui_state("idle", None)
                break # Rompemos el bucle de conversación para volver al wake_word loop
            
            command, audio_data = listen_result
            
            # LOG: Mostrar lo que Fina escuchó (FLUSH IMPORTANTE PARA TEE)
            logger.info(f"🎤 ESCUCHÉ: '{command}'")
            print(f"🎤 ESCUCHÉ: '{command}'", flush=True) # Redundancia para garantizar visibilidad
            sys.stdout.flush() # Doble seguridad
            
            # Verify Speaker (Passive)
            is_admin = False
            score = 0.0
            if voice_auth:
                try:
                    # Siempre verificar contra Administrador que es el admin
                    is_admin, score = voice_auth.verify_user("admin", audio_data)
                except Exception as e: 
                    # logger.error(f"Error verificando voz pasiva: {e}")
                    pass
            
            current_user = "Administrador" if is_admin else "Invitado"
            print(f"🎤 Hablante: {current_user} (Confianza: {score:.2f})")
            
            update_ui_state("speaking", "Procesando...")
            commandFinal = command.lower()

            # --- CORRECCIÓN INTENCIONES DISCORDANTES ---
            # Si dice "Soy Administrador", NO es sleep. Es una afirmación de identidad.
            if "soy admin" in commandFinal or "abre sesion" in commandFinal:
                if is_admin:
                    speak(f"Hola Administrador. Te reconozco. ¿Qué necesitas?", selected_voice_model)
                else:
                    speak("Tu voz no coincide con la de Administrador. Acceso denegado.", selected_voice_model)
                continue
            # -------------------------------------------

            # --- VERIFICAR PLUGINS ---
            if plugin_integration:
                plugin_intent = plugin_integration.match_plugin_intent(commandFinal)
                if plugin_intent:
                    print(f"🔌 Plugin Intent Detectado: {plugin_intent}")
                    try:
                        plugin_integration.handle_intent(plugin_intent, commandFinal)
                    except Exception as e:
                         pass
                    continue # Saltar detección normal
            # -------------------------

            intent, confidence = detect_intent(commandFinal)
            print("Intent:", intent)

            if intent == "exit_fina":
                # SEGURIDAD: Solo Administrador puede apagar el sistema completo.
                if not is_admin:
                    speak("Protocolo de seguridad activo. Valida tu identidad con huella para apagar el sistema.", selected_voice_model)
                    if not authenticate_user(voice_model=selected_voice_model, speak_func=speak):
                        speak("Acceso denegado. No se puede apagar el sistema.", selected_voice_model)
                        continue
                
                # Acceso Concedido
                selected_voice_model, _ = get_current_voice_info()
                # update_ui_state("speaking", "Apagando Sistemas")
                speak("Autorización confirmada. Apagando todos los sistemas.", selected_voice_model)
                update_ui_state("idle", "shutdown")
                print("🛑 EJECUTANDO PROTOCOLO DE APAGADO TOTAL (AUTORIZADO)...")
                
                # 1. Avisar a la API (Estado Shutdown)
                try: requests.get("http://127.0.0.1:8000/api/shutdown", timeout=0.5)
                except: pass
                
                # 2. Matar todo explícitamente usando cleanup.sh
                try:
                    print("🔪 Ejecutando purga con Janitor...")
                    janitor_script = os.path.join(PROJECT_ROOT, "scripts", "janitor.py")
                    python_venv = "python3"
                    subprocess.run([python_venv, janitor_script], check=False)
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
                    speak("Estoy aquí por si me necesitas. Descanso.", selected_voice_model)
                    update_ui_state("idle", "Diga 'Fina' para empezar")
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
                speak("No te entendí. Intente de nuevo.", selected_voice_model)
                continue
            
            # --- Fin Lógica Ruido ---


            # Core system functions
            if intent == "about":
                info_text = f"Soy {FINA_VERSION}. Fui creada por {FINA_AUTHOR} {FINA_CREATED}. Mi arquitectura modular ha sido completamente renovada."
                update_ui_state("speaking", FINA_VERSION)
                speak(info_text, selected_voice_model)
                continue
            elif intent == "exit" or intent == "sleep":
                # SEGURIDAD DE HIERRO PARA SALIDA (Multifactor)
                authenticated = False
                attempts = 0
                max_attempts = 3
                
                speak(f"Solicitud de salida detectada. Iniciando verificación de identidad.", selected_voice_model)
                
                while attempts < max_attempts:
                    attempts += 1
                    update_ui_state("authenticating", f"Verificando Voz ({attempts}/{max_attempts})")
                    
                    if attempts > 1:
                        speak(f"Intento {attempts}. Hable ahora.", selected_voice_model)
                    
                    # Verificación de voz real
                    # Escuchar para obtener muestra de voz
                    # Necesitamos capturar audio fresco para verificar
                    audio_sample = None
                    try:
                        # Escuchar brevemente (5s)
                        result_listen = listen(model, timeout=5, return_audio=True)
                        if result_listen:
                            audio_sample = result_listen[1]
                    except:
                        pass

                    # Verificación de voz real
                    if voice_auth and audio_sample is not None:
                         is_valid, score = voice_auth.verify_user("admin", audio_sample)
                         if is_valid:
                             authenticated = True
                             break
                    
                    # Si falló la auth o no hubo audio
                    if not authenticated:
                        if attempts < max_attempts:
                            speak("Voz no reconocida. Reintentando.", selected_voice_model)
                        else:
                            speak("Fallo crítico de reconocimiento de voz. Iniciando protocolos de emergencia.", selected_voice_model)

                # Si falla la voz tras 3 intentos, pasamos a Huella + Contraseña
                if not authenticated:
                    speak("Por favor, use su huella dactilar para continuar.", selected_voice_model)
                    update_ui_state("authenticating", "Esperando Huella...")
                    
                    # authenticate_user maneja huella y contraseña (fallback interno)
                    # Pero el usuario pidió explícitamente "Huella MÁS contraseña" con reglas estrictas
                    if authenticate_user(voice_model=selected_voice_model, speak_func=speak):
                        authenticated = True
                    else:
                        speak("Autenticación fallida totalmente. El sistema permanecerá activo.", selected_voice_model)
                        update_ui_state("idle", "Diga 'Fina' para empezar")
                        continue

                if authenticated:
                    speak("Identidad confirmada plenamente. Hasta luego Administrador.", selected_voice_model)
                    # No cerramos el programa con return para que pueda despertar con "Fina"
                    sleep_now(selected_voice_model)
                else:
                    speak("Acceso denegado. El sistema permanecerá activo por seguridad.", selected_voice_model)
                    update_ui_state("idle", "Diga 'Fina' para empezar")
                    continue

            elif intent == "train_voice":
                speak("Iniciando modo de entrenamiento de voz. Preparate para hablar.", selected_voice_model)
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
                    speak("Apagando el sistema, Administrador.", selected_voice_model)
                    shutdown(selected_voice_model)
                elif authenticate_user(voice_model=selected_voice_model, speak_func=speak):  # Autenticación con huella fallback
                    speak("¿Realmente queres apagar el sistema?", selected_voice_model)
                    command = listen(model, language="es")
                    intent , confidence = detect_intent(command)
                    if intent == "yes":
                        shutdown(selected_voice_model)
                    else:
                        speak("Entendido!", selected_voice_model)
                else:
                    speak("Autenticación fallida. Acceso denegado.", selected_voice_model)
            elif intent == "restart_pc":
                if is_admin:
                    speak("Reiniciando el sistema, Administrador.", selected_voice_model)
                    reboot(selected_voice_model)
                elif authenticate_user(voice_model=selected_voice_model, speak_func=speak):
                    speak("¿Realmente querés reiniciar la computadora?", selected_voice_model)
                    command = listen(model, language="es")
                    intent_confirm, _ = detect_intent(command)
                    if intent_confirm == "yes":
                        reboot(selected_voice_model)
                    else:
                        speak("Entendido!", selected_voice_model)
                else:
                    speak("Autenticación fallida.", selected_voice_model)
            elif intent == "suspend":
                # Suspender (require auth)
                from utils import suspend
                suspend(selected_voice_model)
            elif intent == "play_music":
                play_music(selected_voice_model)
            elif intent == "stop_music":
                stop_music(selected_voice_model)
            
            elif intent == "hangup_doorbell":
                speak("Cortando comunicación con el timbre...", selected_voice_model)
                try:
                    subprocess.run(["python3", os.path.join(PROJECT_ROOT, "scripts", "hangup_doorbell.py")], check=False)
                except Exception as e:
                    logger.error(f"Error colgado timbre: {e}")
            
            elif intent == "ac_control":
                # Verificar dependencias del plugin
                try:
                    import msmart
                except ImportError:
                    speak("Para controlar el aire acondicionado, precisás instalar las dependencias de ese módulo desde la carpeta plugins clima.", selected_voice_model)
                    continue
                
                # Lógica simple de extracción de comandos para el aire
                cmd_script = os.path.join(GLOBAL_ROOT, "iot", "clima.py")
                py_path = sys.executable
                
                if "apaga" in commandFinal or "cerrar" in commandFinal:
                    speak("Apagando el aire acondicionado...", selected_voice_model)
                    subprocess.run([py_path, cmd_script, "--power", "off"], check=False)
                elif "prende" in commandFinal or "encender" in commandFinal:
                    speak("Encendiendo el aire acondicionado...", selected_voice_model)
                    subprocess.run([py_path, cmd_script, "--power", "on"], check=False)
                elif "turbo" in commandFinal:
                    speak("Activando el modo turbo...", selected_voice_model)
                    subprocess.run([py_path, cmd_script, "--turbo", "on"], check=False)
                else:
                    # Intentar buscar un número (temperatura)
                    temps = re.findall(r'\d+', commandFinal)
                    if temps:
                        t = temps[0]
                        speak(f"Configurando el aire en {t} grados.", selected_voice_model)
                        subprocess.run([py_path, cmd_script, "--temp", t], check=False)
                    else:
                        speak("No entendí qué querés que haga con el aire.", selected_voice_model)
            
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
                from utils import load_contacts
                
                # 1. Contacto
                contacts = load_contacts()
                target_name, target_number = await resolve_contact_proactive(commandFinal, contacts, selected_voice_model, model)
                
                if not target_number:
                    speak("¿A quién le envío el mensaje?", selected_voice_model)
                    target_name_raw = listen(model, language="es")
                    if target_name_raw:
                        target_name, target_number = await resolve_contact_proactive(target_name_raw, contacts, selected_voice_model, model)
                        
                    if not target_number:
                        speak("No encontré el contacto. Operación cancelada.", selected_voice_model)
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
                    msg_body = listen(model, language="es")
                
                if msg_body and len(msg_body) > 1:
                    speak(f"Enviando mensaje a {target_name} por {app_to_use}...", selected_voice_model)
                    # Delegar al motor de la UI (Tauri) para usar el mismo método que la Agenda
                    send_ui_command("fina-send-message", {
                        "number": target_number, 
                        "message": msg_body, 
                        "app": app_to_use
                    })
                else:
                    speak("Cancelado. No se capturó ningún mensaje.", selected_voice_model)

            elif intent == "make_call":
                from utils import load_contacts
                
                contacts = load_contacts()
                target_name, target_number = await resolve_contact_proactive(commandFinal, contacts, selected_voice_model, model)
                
                if not target_number:
                     speak("¿A quién llamo?", selected_voice_model)
                     target_name_raw = listen(model, language="es")
                     if target_name_raw:
                        target_name, target_number = await resolve_contact_proactive(target_name_raw, contacts, selected_voice_model, model)
                
                if not target_number:
                    speak("No encontré el contacto.", selected_voice_model)
                    continue
                
                if target_number:
                    speak(f"Llamando a {target_name}...", selected_voice_model)
                    # Usar intent de llamada
                    adb_cmd = ["adb", "shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{target_number}"]
                    # Nota: ACTION_CALL requiere permiso CALL_PHONE en el manifest de la app que lanza (que es shell), 
                    # usualmente shell tiene permisos. Si falla, usar DIAL.
                    subprocess.run(adb_cmd)
                else:
                    speak("No encontré el contacto.", selected_voice_model)

            elif intent == "read_email":
                speak("Revisando tu bandeja de entrada...", selected_voice_model)
                unread = count_recent_unread_emails(imap_server, EMAIL_USER, EMAIL_PASSWORD, 7)
                speak(f"Tienes {unread} correos no leídos en los últimos 7 días", selected_voice_model)
                speak("¿Quieres que los lea?", selected_voice_model)
                reply = listen(model, language="es")
                if detect_intent(reply.lower())[0] == "yes":
                    from_, subject, date_, unread_msg_nums = read_recent_unread_emails(imap_server, EMAIL_USER, EMAIL_PASSWORD, 7, 4)
                    command = f"Summarize this mail \n_from_: {from_} \ndate: {date_}\nSubject: {subject}"
                    response = await get_mistral_response(command)
                    speak(clean_text_for_speech(response), selected_voice_model)

            elif intent == "send_email":
                contacts = load_contacts()
                speak("¿A quién querés enviar el correo?", selected_voice_model)
                name = clean_input(listen(model, language="es"))
                email = contacts.get(name)
                if email:
                    speak("¿Asunto?", selected_voice_model)
                    subject = listen(model, language="es")
                    speak("¿Cuerpo del mensaje?", selected_voice_model)
                    body = listen(model, language="es")
                    speak("¿Querés que revise faltas de ortografía'?", selected_voice_model)
                    if detect_intent(listen(model, language="es").lower())[0] == "yes":
                        body = await get_mistral_response(f"Fix grammar: {body}")
                    send_email(EMAIL_USER, EMAIL_PASSWORD, email, subject, body)
                    speak(f"Correo enviado a {name}.", selected_voice_model)
                else:
                    speak(f"No se encontró correo para {name}.", selected_voice_model)

            # Web search
            elif intent == "web_search":
                speak("¿Qué tengo buscar?", selected_voice_model)
                query = listen(model, language="es")
                output, link = web_search(query)
                speak(output, selected_voice_model)

            # Assistant Utility Features
            elif intent == "change_wallpaper":
                change_wallpaper(selected_voice_model)

            elif intent == "add_reminder":
                speak("¿Qué debo recordarte?", selected_voice_model)
                task = listen(model, language="es")
                speak("¿Cuándo debo recordártelo? (ejemplo: 14:30)", selected_voice_model)
                time_str = listen(model, language="es")
                result = add_reminder(task, time_str, selected_voice_model)
                speak(result, selected_voice_model)

            elif intent == "list_reminders":
                result = list_reminders()
                speak(result, selected_voice_model)

            elif intent == "news":
                from utils import get_proactive_briefing
                # Usar la nueva función robusta basada en RSS
                news = get_proactive_briefing(selected_voice_model)
                speak(news, selected_voice_model)

            elif intent == "battery_status":
                percentage , status = get_battery_status()
                speak(f"Batería restante {percentage} y {status}", selected_voice_model)

            elif intent == "wiki_summary":
                speak("¿Qué debo buscar en Wikipedia?", selected_voice_model)
                query = listen(model, language="es")
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
                speak("¿Qué texto debo traducir?", selected_voice_model)
                text = listen(model, language="es")
                speak("¿A qué idioma?", selected_voice_model)
                lang = listen(model, language="es")
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
                    from utils import text_to_number_es
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
                    speak("¿Cuántos minutos?", selected_voice_model)
                    resp_text = listen(model, language="es")
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
                        msg = f"Iniciando en {round(minutes, 1)} minutos."
                        
                    start_timer(minutes * 60, "¡Tiempo cumplido!", selected_voice_model)
                else:
                    speak("No entendí el tiempo para el temporizador.", selected_voice_model)

            elif intent == "joke":
                speak(tell_joke(), selected_voice_model)

            elif intent == "create_note":
                speak("¿Qué debo escribir?", selected_voice_model)
                note = listen(model, language="es")
                result = create_note(note)
                speak(result, selected_voice_model)

            elif intent == "current_datetime":
                speak(get_current_datetime(), selected_voice_model)

            elif intent == "youtube_search":
                speak("¿Qué busco en YouTube?", selected_voice_model)
                query = listen(model, language="es")
                # Open YouTube search in Chrome browser
                search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                try:
                    subprocess.Popen(["google-chrome", search_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    speak(f"Abriendo búsqueda de YouTube en Chrome: {query}", selected_voice_model)
                except FileNotFoundError:
                    # Fallback to default browser
                    subprocess.run(f'firefox "{search_url}"', shell=True)
                    speak(f"Abriendo búsqueda de YouTube: {query}", selected_voice_model)

            elif intent == "find_file":
                speak("¿Qué archivo estás buscando?", selected_voice_model)
                filename = listen(model, language="es")
                path = find_file(filename)
                speak(path, selected_voice_model)

            elif intent == "clipboard":
                content = get_clipboard()
                speak(f"El portapapeles contiene: {content}", selected_voice_model)

            elif intent == "convert_currency":
                speak("¿Cuánto y qué moneda?", selected_voice_model)
                info = listen(model, language="es")
                parts = info.split()
                if len(parts) == 3:
                    amount, from_curr, to_curr = parts
                    result = await convert_currency(amount, from_curr.upper(), to_curr.upper())
                    speak(result, selected_voice_model)
                else:
                    speak("Por favor di la cantidad, moneda origen y destino.", selected_voice_model)

            elif intent == "generate_image":
                speak("¿Qué imagen debo generar?", selected_voice_model)
                prompt = listen(model, language="es")
                image_url = await generate_image(prompt)
                speak(f"Imagen generada: {image_url}", selected_voice_model)

            elif intent == "delete_notes":
                result = self_destruct()
                speak(result, selected_voice_model)

            elif intent == "read_pdf":
                speak("Introduce la ruta del archivo PDF", selected_voice_model)
                path = listen(model, language="es")
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
                speak("¿Qué IP o host escaneo?", selected_voice_model)
                host = listen(model, language="es")
                result = scan_ports(host)
                speak(result, selected_voice_model)

            elif intent == "public_ip":
                ip = get_public_ip()
                speak(f"Tu IP pública es {ip}", selected_voice_model)

            elif intent == "wifi_scan":
                result = scan_wifi()
                speak(result, selected_voice_model)

            elif intent == "save_voice_note":
                speak("Di tu nota.", selected_voice_model)
                text = listen(model, language="es")
                result = save_voice_note(text)
                speak(result, selected_voice_model)

            elif intent == "motivation":
                speak(get_daily_affirmation(), selected_voice_model)

            elif intent == "battery_saver":
                speak("¿Activo o desactivo el ahorro de batería?", selected_voice_model)
                mode = listen(model, language="es").lower()
                result = toggle_battery_saver(mode)
                speak(result, selected_voice_model)

            elif intent == "play_ambient":
                speak("¿Qué sonido ambiental? (lluvia, bosque, océano)", selected_voice_model)
                type_ = listen(model, language="es")
                result = play_ambient_sound(type_)
                speak(result, selected_voice_model)

            elif intent == "take_screenshot":
                result = take_screenshot()
                speak(result, selected_voice_model)

            elif intent == "take_photo":
                speak("Listo?", selected_voice_model)
                user_status = listen(model="tiny", language="es")
                intent , confidence = detect_intent(user_status)
                if intent == "yes":
                    speak("cheese!", selected_voice_model)
                    result, path = take_webcam_photo()
                    speak(result, selected_voice_model)
                    speak("¿Querés que abra tu foto?", selected_voice_model)
                    user_choice = listen(model="tiny", language="es")
                    intent , confidence = detect_intent(user_choice)
                    if intent == "yes":
                        command = f'firefox {path}'
                        subprocess.run(command, shell = True, check = True)
                        speak("por favor revisa firefox", selected_voice_model)
                    else:
                        speak("okay", selected_voice_model)
                else:
                    speak("okay", selected_voice_model)

            elif intent == "backup_files":
                result = backup_files()
                speak(result, selected_voice_model)

            elif intent == "download_instagram":
                speak("Pegue la URL del reel de Instagram.", selected_voice_model)
                url = listen(model, language="es")
                result = download_instagram_reel(url)
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
                speak("Lo siento, aún no puedo controlar el brillo del televisor.", selected_voice_model)
            
            elif intent == "tv_decrease_brightness":
                speak("Lo siento, aún no puedo controlar el brillo del televisor.", selected_voice_model)
            
            elif intent == "lights_increase_brightness":
                speak("No tengo luces inteligentes configuradas para aumentar el brillo.", selected_voice_model)
            
            elif intent == "lights_decrease_brightness":
                speak("No tengo luces inteligentes configuradas para disminuir el brillo.", selected_voice_model)
            
            elif intent == "open_spotify":
                try:
                    subprocess.Popen(["harmonymusic"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    speak("Abriendo Harmony Music", selected_voice_model)
                except FileNotFoundError:
                    speak("Harmony Music no está instalado", selected_voice_model)
                except Exception as e:
                    logger.error(f"Error launching Harmony Music: {e}")
                    speak("No pude abrir Harmony Music", selected_voice_model)
            
            elif intent == "open_audio_editor":
                try:
                    subprocess.Popen(["audacity"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    speak("Abriendo Audacity", selected_voice_model)
                except FileNotFoundError:
                    speak("Audacity no está instalado", selected_voice_model)
                except Exception as e:
                    logger.error(f"Error launching Audacity: {e}")
                    speak("No pude abrir Audacity", selected_voice_model)
            
            elif intent == "open_app":
                speak("¿Qué aplicación quieres abrir?", selected_voice_model)
                app_name = listen(model, language="es")
                result = open_app(app_name)
                speak(result, selected_voice_model)
            
            elif intent == "close_app":
                speak("¿Qué aplicación quieres cerrar?", selected_voice_model)
                app_name = listen(model, language="es")
                result = close_app(app_name)
                speak(result, selected_voice_model)
            
            elif intent == "turn_on_tv":
                turn_on_tv(selected_voice_model, commandFinal)
            
            elif intent == "turn_off_tv":
                turn_off_tv(selected_voice_model, commandFinal)

            elif intent == "tv_volume_up":
                steps = 5
                # Intentar buscar un número en el comando

                numbers = re.findall(r'\d+', commandFinal)
                if numbers:
                    try:
                        steps = int(numbers[0])
                        # Limitar a un máximo razonable para no reventar los oídos
                        steps = min(steps, 20)
                    except:
                        pass
                tv_volume_up_cmd(selected_voice_model, steps)
            
            elif intent == "tv_volume_down":
                steps = 5
                numbers = re.findall(r'\d+', commandFinal)
                if numbers:
                    try:
                        steps = int(numbers[0])
                        steps = min(steps, 20)
                    except:
                        pass
                tv_volume_down_cmd(selected_voice_model, steps)

            elif intent == "tv_mute":
                tv_mute_cmd(selected_voice_model)
            
            elif intent == "tv_unmute":
                tv_mute_cmd(selected_voice_model)
            
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
                        speak("¿Qué canal pongo?", selected_voice_model)
                        num_response = listen(model, language="es")
                        if num_response:
                             # Intentar buscar número o usar texto completo
                             more_nm = re.findall(r'\d+[.,]?\d*', num_response.replace(" punto ", "."))
                             if more_nm:
                                 tv_set_channel_cmd(more_nm[0], selected_voice_model)
                             else:
                                 # Asumir que respondió con el nombre
                                 tv_set_channel_cmd(num_response, selected_voice_model)
            
            elif intent == "tv_open_app":
                speak("¿Qué aplicación en la tele?", selected_voice_model)
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
                   app_response = listen(model, language="es")
                   if app_response:
                       tv_open_app_cmd(app_response, selected_voice_model)
            
            elif intent == "tv_exit_app":
                tv_exit_app_cmd(selected_voice_model)
                
# main entry point
def handle_exit(signum, frame):
    """Manejador para la terminación limpia del programa."""
    logger.info("Solicitud de terminación recibida. Cerrando el asistente...")
    print("\n¡Hasta luego!")
    
    # Detener motor de voz
    try:
        from utils import stop_voice_engine
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
        missing = config.validate_config()
        if missing:
            logger.warning(f"Algunas características pueden no funcionar: faltan configuraciones para {missing}")
            print(f"[ADVERTENCIA] Algunas características pueden no funcionar: faltan configuraciones para {missing}")
    except Exception as e:
        logger.error(f"Error en la validación de configuración: {e}")
        print("Error crítico de configuración: Faltan claves de API o son inválidas. Por favor verifica tu archivo config.py.")
        sys.exit(1)
        
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
