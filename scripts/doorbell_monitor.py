
import time
import subprocess
import os
import sys
import logging

# Configuración
DOORBELL_IP = "192.168.0.5"
CHECK_INTERVAL = 3.0
VIRTUAL_SINK_NAME = "FinaVoice"

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Añadir path al proyecto para utils
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# Importar utils o definir fallbacks
try:
    from utils import speak, show_doorbell_stream
except ImportError:
    def speak(text, model=None):
        print(f"🗣️ (Fallback) {text}")
        subprocess.run(f"espeak '{text}'", shell=True)
    def show_doorbell_stream(model=None):
        pass

def setup_virtual_audio():
    """Configura el sink virtual para audio limpio"""
    try:
        # 1. Verificar/Crear SINK
        cmd_check_sink = f"pactl list short sinks | grep {VIRTUAL_SINK_NAME}"
        if subprocess.run(cmd_check_sink, shell=True, stdout=subprocess.DEVNULL).returncode != 0:
            print("🎛️ Creando Audio Virtual (Sink)...")
            cmd_create = f"pactl load-module module-null-sink sink_name={VIRTUAL_SINK_NAME} sink_properties=device.description=Fina_Virtual_Mic"
            subprocess.run(cmd_create, shell=True)

        # 2. Verificar/Crear LOOPBACK (Para que escuches lo que pasa en el virtual)
        # Buscamos un módulo loopback que tenga nuestro sink como source
        cmd_check_loop = f"pactl list short modules | grep module-loopback | grep {VIRTUAL_SINK_NAME}.monitor"
        if subprocess.run(cmd_check_loop, shell=True, stdout=subprocess.DEVNULL).returncode != 0:
            print("🎛️ Creando Audio Virtual (Loopback)...")
            # Dejar que PulseAudio decida el sink de salida (default)
            cmd_loop = f"pactl load-module module-loopback source={VIRTUAL_SINK_NAME}.monitor"
            subprocess.run(cmd_loop, shell=True, stderr=subprocess.DEVNULL)
            
        # 3. Restaurar Microfono Default
        try:
            # Intentar buscar MICRÓFONO INTERNO (PCI) primero
            mic_cmd = "pactl list short sources | grep 'input' | grep -v 'monitor' | grep 'pci' | head -n1 | cut -f2"
            res = subprocess.run(mic_cmd, shell=True, stdout=subprocess.PIPE).stdout.decode().strip()
            
            # Si no hay interno, buscar CUALQUIERA (USB, etc.)
            if not res:
                mic_cmd = "pactl list short sources | grep 'input' | grep -v 'monitor' | head -n1 | cut -f2"
                res = subprocess.run(mic_cmd, shell=True, stdout=subprocess.PIPE).stdout.decode().strip()

            if res:
                 subprocess.run(f"pactl set-default-source {res}", shell=True)
                 print(f"🎤 Default Source restaurado a: {res}")
        except Exception as ex:
             print(f"⚠️ No se pudo restaurar default mic: {ex}")
            
    except Exception as e:
        print(f"⚠️ Error setup audio: {e}")

def is_online(ip):
    try:
        res = subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0
    except:
        return False

def get_audio_ids():
    """Devuelve (virtual_source, mic_source) o (None, '58')"""
    try:
        # Virtual Source (Monitor del Null Sink)
        v_cmd = f"pactl list short sources | grep '{VIRTUAL_SINK_NAME}.monitor' | cut -f1"
        virtual = subprocess.check_output(v_cmd, shell=True).decode().strip()
        
        # Mic Físico (Input analógico default)
        m_cmd = "pactl list short sources | grep 'analog-stereo' | grep 'input' | head -n1 | cut -f1"
        mic = subprocess.check_output(m_cmd, shell=True).decode().strip()
        
        return virtual, mic
    except:
        return None, "58"

def find_waydroid_stream():
    """Intenta encontrar el ID del stream de grabación de Waydroid"""
    for _ in range(10): # 5 intentos rápidos (0.1s * 10 = 1s total) - Ajustado a 10 para dar margen
        try:
            output = subprocess.check_output("pactl list source-outputs", shell=True).decode()
            if "Waydroid" in output:
                # Parseo bruto pero efectivo
                blocks = output.split("Salida de fuente #")
                for block in blocks:
                    if "Waydroid" in block:
                        return block.split("\n")[0].strip()
        except:
            pass
        time.sleep(0.1)
    return None

def ensure_android_environment():
    """Verifica si Waydroid/Weston están corriendo. Si no, los inicia."""
    try:
        # Chequear si waydroid session está activa
        # Buscamos procesos de waydroid
        check = subprocess.run("pgrep -f 'waydroid session'", shell=True, stdout=subprocess.DEVNULL)
        
        if check.returncode != 0:
            print("🚀 Iniciando infraestructura Android (Weston + Waydroid)...")
            # Definir entorno gráfico explícito para Weston
            env = os.environ.copy()
            env["DISPLAY"] = ":0"
            env["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"
            
            # Ejecutar el script de arranque en segundo plano
            script_path = os.path.join(PROJECT_ROOT, "scripts", "start_hidden_system.sh")
            subprocess.Popen(["bash", script_path], 
                           env=env, # Inyectar display
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           start_new_session=True)
            
            # Darle tiempo para arrancar (es pesado)
            print("⏳ Esperando 15s a que el sistema Android arranque...")
            time.sleep(15)
        else:
            print("✅ Infraestructura Android ya detectada.")

    except Exception as e:
        print(f"⚠️ Error verificando entorno Android: {e}")

def monitor_loop():
    # 0. Retraso de cortesía para dejar que Fina (main.py) arranque su audio primero
    print("⏳ Esperando 20s para no saturar audio al inicio...")
    time.sleep(20)

    # 1. Asegurar infraestructura
    ensure_android_environment()
    
    setup_virtual_audio()
    print(f"🕵️ Vigilando timbre {DOORBELL_IP}...")
    
    # ESTADO INICIAL: Chequear si ya está online al arrancar
    # Si ya está online, asumimos que es estado basal o residual y NO activamos.
    # Solo activaremos cuando pase de Offline -> Online.
    if is_online(DOORBELL_IP):
        print("⚠️ Timbre detectado ONLINE al inicio. Esperando a que se duerma para armar sistema...")
        was_online = True
    else:
        print("✅ Timbre dormido. Sistema ARMADO.")
        was_online = False

    last_seen = 0
    consecutive_failures = 0
    
    while True:
        try:
            online = is_online(DOORBELL_IP)
            
            if online:
                # Si volvemos a estar online, reseteamos el contador de fallos
                consecutive_failures = 0
                
                now = time.time()
                # Flanco de subida (Se conectó)
                if not was_online:
                    print("\n🔔 ¡TIMBRE ACTIVADO! (Offline -> Online)")
                    
                    # Cooldown 45s (Suficiente para nueva visita, protegido por anti-rebote)
                    if (now - last_seen) > 45:
                        print("🚀 INICIANDO SECUENCIA DE ATENCIÓN...")
                        
                        # 1. Feedback Auditivo Local
                        speak("Atención. Alguien toca el timbre.", None)
                        
                        # 2. Despertar y Preparar Entorno (ADB) 
                        # SOLO CONECTAR AHORA, NO ANTES.
                        print("🥷 Activando Modo Ninja (ADB)...")
                        try:
                            # Kill server preventivo si estaba zombie
                            # subprocess.run("adb disconnect 192.168.240.112:5555", shell=True, stdout=subprocess.DEVNULL)
                            
                            # Conectar con timeout preventivo para no colgar el sistema
                            subprocess.run("timeout 5 adb connect 192.168.240.112:5555", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            
                            # Wake & Unlock con timeouts
                            subprocess.run("timeout 3 adb -s 192.168.240.112:5555 shell input keyevent 224", shell=True, timeout=5)
                            subprocess.run("timeout 3 adb -s 192.168.240.112:5555 shell wm dismiss-keyguard", shell=True, timeout=5)
                            subprocess.run("timeout 3 adb -s 192.168.240.112:5555 shell input swipe 300 700 300 100", shell=True, timeout=5)
                        except Exception as adb_e:
                            print(f"⚠️ Error preparando ADB Waydroid: {adb_e}")
                        
                        # Scrcpy (Video) -> AHORA ANTES PARA VER QUÉ PASA
                        try:
                            print("🖥️ Abriendo ventana de video DEPURACIÓN...")
                            # Matar instancias previas para evitar acumulación
                            subprocess.run("pkill -f 'scrcpy.*Timbre Fina'", shell=True, stderr=subprocess.DEVNULL)
                            
                            # Reutilizamos el env con DISPLAY
                            env = os.environ.copy()
                            env["DISPLAY"] = ":0"
                            env["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"
                            
                            subprocess.Popen([
                                "scrcpy", "-s", "192.168.240.112:5555",
                                "--window-title", "Timbre Fina", 
                                "--always-on-top", 
                                "--window-width", "400",  
                                "--window-borderless",    
                                "--window-x", "800",
                                "--window-y", "100"
                            ], 
                            env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        except Exception as e:
                            print(f"❌ Error lanzando scrcpy: {e}")

                        # Lanzar App Tuya
                        subprocess.run("timeout 5 adb -s 192.168.240.112:5555 shell monkey -p com.tuya.smart -c android.intent.category.LAUNCHER 1", shell=True, stdout=subprocess.DEVNULL, timeout=7)
                        
                        # 3. Intentar Atender (Clicks PRECISOS)
                        print("⏳ Esperando carga de app (8s)...")
                        time.sleep(8)
                        
                        success = True # ASUMIMOS ÉXITO PARA SEGUIR (Modo Depuración)
                        
                        # RE-INSERTAMOS INTENTOS DE CLICK (Para que veas al fantasma actuar)
                        for i in range(3):
                            print(f"👉 Intento #{i+1}...")
                            subprocess.run("timeout 3 adb -s 192.168.240.112:5555 shell input tap 325 157", shell=True, timeout=5)
                            time.sleep(0.5)
                            subprocess.run("timeout 3 adb -s 192.168.240.112:5555 shell input keyevent 5", shell=True, timeout=5)
                            time.sleep(1.5)
                        
                        if success:

                            # Esperar a que conecte audio/video
                            print("⏳ Estabilizando llamada (8s)...")
                            time.sleep(8)
                            
                            # 4. Secuencia de Audio (PTT + Hablar) - LÓGICA DE TEST_VIRTUAL_STUDIO
                            print("🎙️ Iniciando Secuencia de Audio...")
                            
                            # A. INICIAR GRABACIÓN (PTT) PRIMERO
                            # Esto asegura que exista un stream de audio para enrutar
                            print("👇 Presionando PTT (Blanco)...")
                            # AUMENTADO A 10 SEGUNDOS para evitar cortes
                            ptt_process = subprocess.Popen(["adb", "-s", "192.168.240.112:5555", "shell", "input", "swipe", "228", "643", "228", "643", "10000"])
                            
                            print("⏳ Esperando stream de audio (1.5s)...")
                            time.sleep(1.5) # Tiempo vital para que la app abra el micrófono
                            
                            # B. BUSCAR Y ENRUTAR (Código adaptado de test_virtual_studio.py)
                            waydroid_id = None
                            try:
                                # 1. Buscar ID Virtual
                                virtual_source = subprocess.check_output("pactl list short sources | grep 'FinaVoice.monitor' | cut -f1", shell=True).decode().strip()
                                
                                # 2. Buscar Waydroid ID
                                for _ in range(10): # Loop de búsqueda
                                    try:
                                        output = subprocess.check_output("pactl list source-outputs", shell=True).decode()
                                        if "Waydroid" in output:
                                            blocks = output.split("Salida de fuente #")
                                            for block in blocks:
                                                if "Waydroid" in block:
                                                    waydroid_id = block.split("\n")[0].strip()
                                                    break
                                        if waydroid_id: break
                                    except: pass
                                    time.sleep(0.2)
                                
                                if waydroid_id and virtual_source:
                                    print(f"🔌 Enrutando Stream #{waydroid_id} -> Virtual #{virtual_source}")
                                    subprocess.run(f"pactl move-source-output {waydroid_id} {virtual_source}", shell=True)
                                else:
                                    print(f"⚠️ No se pudo enrutar (WID: {waydroid_id}, VID: {virtual_source})")
                                    
                            except Exception as e:
                                print(f"❌ Error en enrutamiento: {e}")

                            # C. HABLAR
                            h = int(time.strftime("%H"))
                            saludo = "Buenos días" if 6 <= h < 12 else "Buenas tardes" if 12 <= h < 20 else "Buenas noches"
                            mensaje = f"{saludo}. En unos minutos serás atendido. Gracias."
                            
                            print(f"🗣️ Fina: '{mensaje}'")
                            
                            os.environ["PULSE_SINK"] = VIRTUAL_SINK_NAME
                            try:
                                speak(mensaje, None)
                            except Exception as e:
                                print(f"❌ Error TTS: {e}")
                            finally:
                                if "PULSE_SINK" in os.environ: del os.environ["PULSE_SINK"]
                            
                            # D. BUFFER DE SEGURIDAD
                            print("⏳ Esperando transmisión final (1.5s)...")
                            time.sleep(1.5) # Dejar que el 'Gracias' viaje por la red
                            
                            # Esperar fin de PTT (Si terminamos antes de los 10s, esto no corta, solo espera si faltara.
                            # Para cortar antes, necesitaríamos matar el proceso, pero mejor dejar que corra el swipe completo o matarlo explícitamente si es muy largo)
                            # En este caso, como aumentamos a 10s, si Fina termina en 5s, el botón seguiría presionado 5s más de silencio.
                            # Para ser eficientes: Matamos el swipe si ya terminamos.
                            
                            ptt_process.terminate() # Soltar botón explícitamente
                            print("👆 PTT Soltado (Forzado).")
                            
                            # Restaurar audio (limpieza best-effort)
                            if waydroid_id:
                                try:
                                    mic = subprocess.check_output("pactl list short sources | grep 'analog-stereo' | grep 'input' | head -n1 | cut -f1", shell=True).decode().strip()
                                    if mic:
                                        subprocess.run(f"pactl move-source-output {waydroid_id} {mic}", shell=True)
                                except: pass
                                
                            # CORTAR LA LLAMADA -> DESHABILITADO
                            # YA NO CORTAMOS AUTOMÁTICAMENTE. EL USUARIO LO HARÁ POR VOZ ("Corta el timbre")
                            print("⏸️ Llamada ABIERTA. Esperando comando de corte...")
                            
                            # Notificar al usuario (visible en pantalla principal)
                            subprocess.run(["notify-send", "🔔 TIMBRE", "Llamada activa. Di 'Corta el timbre' para finalizar."], stderr=subprocess.DEVNULL)
                            
                            print("✅ Ciclo de atención finalizado (Llamada sigue activa).")
                            print("⏳ Esperando 60s antes de volver a monitorear (aunque seguirá online)...")
                            
                            # ACTUALIZACIÓN CRÍTICA: 
                            # Actualizamos last_seen AHORA, para que el cooldown cuente desde ESTE momento.
                            # Esto evita que una llamada larga active inmediatamente un nuevo evento si el timbre parpadea en la red.
                            last_seen = time.time() 
                            
                            time.sleep(60)
                        
                        # No enviamos notificación de "Atendido" final, ya que sigue activo.
                        
                    else:
                        print("⏳ Ignorando (Cooldown).")
                    
                    # Actualizamos last_seen también aquí para mantener el estado "visto" si sigue online
                    if online:
                         # Si es solo refresco de estado (sin evento), mantenemos last_seen fresco si no se disparó evento
                         # PERO CUIDADO: Si estamos en cooldown, no queremos resetear last_seen constantemente alejándolo?
                         # No, last_seen es "última vez que vi el timbre online".
                         # La logica de cooldown de arriba usa (now - last_seen).
                         # Si actualizo last_seen en cada loop, (now - last_seen) siempre será ~3 segundos. NUNCA disparará.
                         # ERROR EN MI LÓGICA ANTERIOR.
                         
                         # CORRECCIÓN DE LÓGICA DE COOLDOWN:
                         # last_seen debería ser "última vez que SE ACTIVÓ EL EVENTO".
                         # NO "última vez que lo vi online".
                         pass

                    was_online = True
            
            else:
                # OFFLINE DETECTADO
                # LÓGICA ANTI-REBOTE: Requiere 3 fallos consecutivos
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    if was_online:
                        print("\n💤 Timbre desconectado (Confirmado).")
                        was_online = False
                else:
                    pass
            
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"❌ Error en bucle principal: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_loop()
