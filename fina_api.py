import sys
import os
import json
import re
import subprocess
import threading
import time
from typing import List, Optional, Dict

# --- DETECCIÓN DE ENTORNO VIRTUAL [AUTO-SWITCH] ---
def get_best_python():
    vps = [
        os.path.join(os.path.expanduser("~"), ".config", "Fina", "venv", "bin", "python"),
        os.path.join(os.path.dirname(__file__), ".venv", "bin", "python"),
        sys.executable
    ]
    for p in vps:
        if os.path.exists(p): return p
    return sys.executable

best_py = get_best_python()
if "venv" in best_py and "venv" not in sys.executable:
    print(f"🔄 API: Relanzando con entorno detectado: {best_py}", flush=True)
    os.execl(best_py, best_py, *sys.argv)

# --- SILENCIAR LIBRERÍAS RUIDOSAS ---
import logging
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "0"  # Permitir descargas si faltan, pero sin avisos
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

for lib in ["httpx", "urllib3"]:
    logging.getLogger(lib).setLevel(logging.WARNING)

# --- LIMPIADOR DE PUERTOS (Evita Error 98: Address already in use) ---
def kill_process_on_port(port):
    try:
        import subprocess
        # Buscar el PID del proceso en el puerto
        result = subprocess.check_output(["lsof", "-t", f"-i:{port}"]).decode().strip()
        if result:
            pids = result.split("\n")
            for pid in pids:
                print(f"🧹 API: Limpiando proceso fantasma en puerto {port} (PID: {pid})...", flush=True)
                subprocess.run(["kill", "-9", pid])
            time.sleep(1) # Dar tiempo al kernel para liberar el socket
    except: pass

kill_process_on_port(8000)

print(f"\n--- [ARRANQUE API] {time.strftime('%Y-%m-%d %H:%M:%S')} ---", flush=True)

# --- CONFIG DIRECTORY [CENTRALIZED & ROBUST] ---
def get_config_dir():
    # 1. XDG_CONFIG_HOME
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return os.path.join(xdg_config, "Fina")
    # 2. Pathlib Home
    try:
        from pathlib import Path
        return os.path.join(str(Path.home()), ".config", "Fina")
    except:
        return os.path.expanduser("~/.config/Fina")

CONFIG_DIR = get_config_dir()
if not os.path.exists(CONFIG_DIR):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
    except: pass

# --- DIAGNÓSTICO DE ENTORNO ---
import getpass
print(f"👤 API Usuario: {getpass.getuser()}", flush=True)
print(f"🏠 API HOME: {os.environ.get('HOME')}", flush=True)
print(f"🌐 API XDG: {os.environ.get('XDG_CONFIG_HOME')}", flush=True)
print(f"📂 API Config Dir: {CONFIG_DIR}", flush=True)

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    import locale
    import importlib.util

    # Carga Robusta de config.py
    CONFIG_PY_PATH = os.path.join(CONFIG_DIR, "config.py")
    if os.path.exists(CONFIG_PY_PATH):
        try:
            spec = importlib.util.spec_from_file_location("user_config", CONFIG_PY_PATH)
            config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config)
            print(f"✅ API: config.py cargado desde {CONFIG_PY_PATH}", flush=True)
        except Exception as e:
            print(f"⚠️ [WARN] Error en config.py personalizado: {e}. Usando defaults internos.", flush=True)
            import config
    else:
        try:
            import config
            print("ℹ️ [INFO] Usando config.py interno (Template).", flush=True)
        except ImportError:
            print("⚠️ [WARN] config.py no encontrado ni en .config ni interno.", flush=True)
            config = None
except Exception as e:
    print(f"❌ [CRITICAL] Error importando librerías API: {e}", flush=True)
    sys.exit(1)

app = FastAPI(title="Fina API Ergen")

# --- CORS (CRÍTICO PARA TAURI/FETCH) ---
# Permitimos TODO para evitar "Load Failed" en local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir cualquier origen (tauri://localhost, http://localhost)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
USER_DATA_PATH = os.path.join(CONFIG_DIR, "user_data.json")

# Soporte para ambos nombres (singular y plural)
CONTACTS_PATH_PRIMARY = os.path.join(CONFIG_DIR, "contact.json")
CONTACTS_PATH_SECONDARY = os.path.join(CONFIG_DIR, "contacts.json")

if os.path.exists(CONTACTS_PATH_PRIMARY):
    CONTACTS_PATH = CONTACTS_PATH_PRIMARY
else:
    CONTACTS_PATH = CONTACTS_PATH_SECONDARY

# Estrategia para Canales: 1. Usuario, 2. Interno/Config, 3. Raíz
CHANNELS_PATH_USER = os.path.join(CONFIG_DIR, "channels.json")
CHANNELS_PATH_INTERNAL = os.path.join(PROJECT_ROOT, "config", "channels.json")
CHANNELS_PATH_FALLBACK = os.path.join(PROJECT_ROOT, "channels.json")

if os.path.exists(CHANNELS_PATH_USER):
    CHANNELS_PATH = CHANNELS_PATH_USER
elif os.path.exists(CHANNELS_PATH_INTERNAL):
    CHANNELS_PATH = CHANNELS_PATH_INTERNAL
else:
    CHANNELS_PATH = CHANNELS_PATH_FALLBACK

CHANNELS_PATH_TELECENTRO_USER = os.path.join(CONFIG_DIR, "channels_telecentro.json")
CHANNELS_PATH_TELECENTRO_INTERNAL = os.path.join(PROJECT_ROOT, "config", "channels_telecentro.json")

if os.path.exists(CHANNELS_PATH_TELECENTRO_USER):
    CHANNELS_PATH_TELECENTRO = CHANNELS_PATH_TELECENTRO_USER
else:
    CHANNELS_PATH_TELECENTRO = CHANNELS_PATH_TELECENTRO_INTERNAL

# DIAGNÓSTICO DE PERMISOS (Crítico para AppImage Sidecar)
import getpass
current_user = getpass.getuser()
print(f"👤 API Corriendo como: {current_user}", flush=True)
print(f"📂 Config Dir: {CONFIG_DIR} (Acceso R:{os.access(CONFIG_DIR, os.R_OK)})", flush=True)
print(f"📄 Settings: {SETTINGS_PATH} (Existe: {os.path.exists(SETTINGS_PATH)}, Readable: {os.access(SETTINGS_PATH, os.R_OK) if os.path.exists(SETTINGS_PATH) else 'N/A'})", flush=True)
print(f"👥 Contacts: {CONTACTS_PATH} (Existe: {os.path.exists(CONTACTS_PATH)})", flush=True)
print(f"📺 Channels Standard: {CHANNELS_PATH} (Existe: {os.path.exists(CHANNELS_PATH)})", flush=True)

if os.path.exists(CHANNELS_PATH_TELECENTRO_USER):
    print(f"📡 Canales Telecentro: {CHANNELS_PATH_TELECENTRO_USER} (USUARIO)", flush=True)
elif os.path.exists(CHANNELS_PATH_TELECENTRO_INTERNAL):
    print(f"📡 Canales Telecentro: {CHANNELS_PATH_TELECENTRO_INTERNAL} (INTERNO)", flush=True)

print(f"✅ Rutas unificadas: {CONFIG_DIR}", flush=True)

# --- Models ---
class TV(BaseModel):
    name: str
    ip: str
    mac: str
    enabled: bool
    primary: bool

class Settings(BaseModel):
    tvs: List[TV]
    apis: Dict[str, str]
    paths: Dict[str, str]
    channels: Dict[str, List]
    tv_apps: Dict[str, str]

class StateUpdate(BaseModel):
    status: str 
    intensity: float = 0.0
    process: Optional[str] = None 
    temp: Optional[str] = None

    class Config:
        extra = "allow"

# --- Global State ---
current_fina_state = {
    "status": "idle", 
    "intensity": 0.0, 
    "process": "SISTEMA LISTO",
    "temp": "--°C",
    "pending_command": None  # Nuevo: para comandos que la UI debe ejecutar
}

scan_state = {"active": False, "progress": 0, "last_result": {}}
enroll_info = {"active": False, "message": "Esperando...", "progress": 0}

# --- Helper Functions ---
def load_settings_data():
    if not os.path.exists(SETTINGS_PATH):
        # Crear default si no existe
        return {"tvs": [], "apis": {}, "paths": {}, "tv_apps": {}}
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando settings: {e}", flush=True)
        return {}

def save_settings_data(data):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error guardando settings: {e}", flush=True)

# --- Endpoints ---
@app.get("/api/state")
async def get_fina_state():
    global current_fina_state
    # Devolvemos el estado y LIMPIAMOS el comando para que no se ejecute dos veces
    state_to_return = current_fina_state.copy()
    current_fina_state["pending_command"] = None
    return state_to_return

@app.post("/api/state")
async def update_fina_state(state: StateUpdate):
    global current_fina_state
    # Actualizar estado global con TODO lo que venga (incluido timer)
    update_data = state.dict(exclude_unset=True)
    current_fina_state.update(update_data)
    return current_fina_state

@app.post("/api/command")
async def queue_command(command: dict):
    global current_fina_state
    current_fina_state["pending_command"] = command
    print(f"📥 Comando encolado: {command.get('name')}", flush=True)
    return {"status": "queued"}

@app.get("/api/shutdown")
async def shutdown_api():
    print("⚠️ Orden de apagado recibida", flush=True)
    def kill():
        time.sleep(1)
        os._exit(0)
    threading.Thread(target=kill).start()
    return {"message": "Bye"}

@app.get("/api/userdata")
async def get_user_data():
    if not os.path.exists(USER_DATA_PATH):
        return {"notes": [], "reminders": []}
    try:
        with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando user_data: {e}", flush=True)
        return {"notes": [], "reminders": []}

@app.get("/api/settings")
async def get_settings():
    """Retorna los ajustes desde .config/Fina/settings.json"""
    return load_settings_data()

@app.get("/api/contacts")
async def get_contacts():
    """Retorna los contactos desde .config/Fina/contact.json (o contacts.json)"""
    path = CONTACTS_PATH_PRIMARY if os.path.exists(CONTACTS_PATH_PRIMARY) else CONTACTS_PATH_SECONDARY
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando contactos: {e}", flush=True)
        return {}

@app.get("/api/plugins")
async def get_plugins():
    """Retorna la lista de plugins instalados (Sistema + Usuario)"""
    try:
        from plugin_manager import PluginManager
        pm = PluginManager()
        return pm.list_plugins()
    except Exception as e:
        print(f"❌ Error listando plugins: {e}", flush=True)
        return []

@app.get("/api/network/scan")
async def scan_network():
    """Ejecuta el escáner de red y devuelve la lista de dispositivos detectados"""
    try:
        scan_script = os.path.join(PROJECT_ROOT, "iot", "network_scan.py")
        if not os.path.exists(scan_script):
            return {"error": f"Script no encontrado: {scan_script}", "devices": []}
        result = subprocess.run(
            [sys.executable, scan_script],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f"❌ Error escáner red: {result.stderr}", flush=True)
            return {"error": result.stderr, "devices": []}
        devices = json.loads(result.stdout)
        print(f"✅ Red escaneada: {len(devices)} dispositivos", flush=True)
        return {"devices": devices}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout: el escaneo tardó demasiado.", "devices": []}
    except Exception as e:
        print(f"❌ Error en scan_network: {e}", flush=True)
        return {"error": str(e), "devices": []}

@app.get("/api/system/info")
async def get_system_info():
    """Devuelve rutas críticas para que el frontend sepa qué usar"""
    return {
        "python_path": sys.executable,
        "project_root": PROJECT_ROOT,
        "config_dir": CONFIG_DIR,
        "version": "3.5.4-18"
    }

# --- Static ---
if os.path.exists(os.path.join(PROJECT_ROOT, "static")):
    app.mount("/", StaticFiles(directory=os.path.join(PROJECT_ROOT, "static"), html=True), name="static")

# --- Boot Logic ---
if __name__ == "__main__":
    print("🚀 Iniciando Uvicorn en 0.0.0.0:8000...", flush=True)
    # Ejecutamos Uvicorn
    # IMPORTANTE: log_config=None para que use nuestros handlers si quisieramos, 
    # pero aquí confiamos en que stdout ya está redirigido a API_BOOT.log
    uvicorn.run(app, host="0.0.0.0", port=8000)
