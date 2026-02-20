
import json
import os
import sys

# Simular entorno del plugin
class MockContext:
    pass

# Cargar settings reales
def load_settings():
    path = os.path.join(os.getcwd(), "config", "settings.json")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando settings: {e}")
        return {"tvs": []}

def get_target_tv(settings, command, intent_name="tv_on"):
    tvs = settings.get("tvs", [])
    if isinstance(tvs, dict):
        tvs_list = [{"name": k, **v} for k, v in tvs.items()]
    else:
        tvs_list = tvs
    
    print(f"DEBUG: TVs cargadas: {[t.get('name') for t in tvs_list]}")
    
    command_low = command.lower()

    # 1. BÚSQUEDA EXPLÍCITA
    for tv in tvs_list:
        name = tv.get("name", "").lower()
        room = tv.get("room", "").lower()
        
        print(f"Checking TV: Name='{name}', Room='{room}' against Command='{command_low}'")
        
        if (name and name in command_low) or (room and room in command_low):
            print(f"✅ MATCH FOUND: {tv.get('name')} ({tv.get('ip')})")
            return tv

    print("⚠️ NO MATCH FOUND. Falling to default logic...")
    return None

if __name__ == "__main__":
    settings = load_settings()
    command = "enciende el deco"
    print(f"Testing command: '{command}'")
    target = get_target_tv(settings, command)
    
    if target:
        print(f"\nRESULTADO: El plugin HABRÍA seleccionado: {target.get('name')} - {target.get('ip')}")
        if target.get('ip') == "192.168.0.9":
             print("🎉 ÉXITO TOTAL: El deco fue identificado correctamente.")
        else:
             print("❌ ERROR: Seleccionó el dispositivo incorrecto.")
    else:
        print("\n❌ FALLO: El plugin no supo qué dispositivo era y hubiera usado defaults.")
