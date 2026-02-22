import sys
import json
import os

# Script seguro para guardar ajustes recibiendo JSON como argumento
# Uso: python3 save_settings.py "JSON_STRING"

if len(sys.argv) < 2:
    print(json.dumps({"status": "error", "message": "No data provided"}))
    sys.exit(1)

try:
    json_str = sys.argv[1]
    # Validar que sea JSON válido antes de guardar
    data = json.loads(json_str)
    
    # Ruta Universal: ~/.config/Fina/settings.json
    def get_config_dir():
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return os.path.join(xdg_config, "Fina")
        try:
            from pathlib import Path
            return os.path.join(str(Path.home()), ".config", "Fina")
        except:
            return os.path.expanduser("~/.config/Fina")

    config_path = os.path.join(get_config_dir(), "settings.json")
    
    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(json.dumps({"status": "success"}))

except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
    sys.exit(1)
