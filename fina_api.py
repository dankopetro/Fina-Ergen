import sys
import os
import json
import re
import subprocess
import threading
import time
from typing import List, Optional, Dict

# --- LOGGING DIAGNÓSTICO ---
# Dejamos que el script de bash maneje los logs (tee)
print(f"\n--- [ARRANQUE API] {time.strftime('%Y-%m-%d %H:%M:%S')} ---", flush=True)

# --- CONFIG DIRECTORY [CENTRALIZED] ---
CONFIG_DIR = os.path.expanduser("~/.config/Fina")
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR, exist_ok=True)

# Inyectar CONFIG_DIR al inicio de sys.path para que 'import config' lo encuentre allí
if CONFIG_DIR not in sys.path:
    sys.path.insert(0, CONFIG_DIR)

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    import locale
    import getpass
    # Intentamos importar config, si falla no matamos la API, usamos defaults
    try:
        import config
    except ImportError:
        print("⚠️ [WARN] config.py no encontrado en .config/Fina. Usando valores por defecto.", flush=True)
        config = None
except Exception as e:
    print(f"❌ [CRITICAL] Error importando librerías: {e}", flush=True)
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
CONTACTS_PATH = os.path.join(CONFIG_DIR, "contact.json")
CHANNELS_PATH = os.path.join(PROJECT_ROOT, "channels.json") # Mantener canales en root por ahora
USER_DATA_PATH = os.path.join(CONFIG_DIR, "user_data.json")

print(f"✅ Rutas de usuario activas: {CONFIG_DIR}", flush=True)

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
    """Retorna los contactos desde .config/Fina/contact.json"""
    if not os.path.exists(CONTACTS_PATH):
        return {}
    try:
        with open(CONTACTS_PATH, "r", encoding="utf-8") as f:
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
        "version": "3.5.4"
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
