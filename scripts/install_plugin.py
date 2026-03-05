#!/usr/bin/env python3
import sys
import os
import urllib.request
import urllib.error
import json
import shutil
import base64

def error_exit(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        error_exit("Faltan argumentos (category, subpath)")

    category = sys.argv[1]
    subpath = sys.argv[2]
    
    # Github API tree URL para el market
    repo = "dankopetro/Fina-Plugins-Market"
    
    print(f"Instalando plugin {subpath} desde categoría {category}...")
    
    # --- DINAMIC PATH FOR PORTABILITY ---
    def get_config_dir():
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return os.path.join(xdg_config, "Fina")
        return os.path.join(os.path.expanduser("~"), ".config", "Fina")

    config_dir = get_config_dir()
    
    # Mapeo de categoría Github -> Carpeta local
    dir_map = {
        "TVs": "tv",
        "Decos": "decos",
        "Doorbells": "doorbell",
        "AirConditioning": "ac"
    }
    
    local_cat = dir_map.get(category)
    if not local_cat:
        error_exit(f"Categoría desconocida: {category}")
        
    # Destino real: ~/.config/Fina/plugins/local_cat/modelo
    parts = subpath.split('/')
    if len(parts) < 2:
        error_exit("Ruta de subpath inválida. Formato esperado: Marca/Modelo")
        
    brand = parts[0]
    model = parts[1]
    
    # En la estructura Fina, ignoramos la marca y usamos el modelo directo
    dest_dir = os.path.join(config_dir, "plugins", local_cat, model)
    os.makedirs(dest_dir, exist_ok=True)
    
    api_url = f"https://api.github.com/repos/{repo}/contents/{category}/{subpath}"
    
    req = urllib.request.Request(api_url)
    req.add_header('User-Agent', 'Fina-Installer')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    
    try:
        with urllib.request.urlopen(req) as response:
            contents = json.loads(response.read().decode('utf-8'))
            
            for item in contents:
                if item["type"] == "file":
                    file_name = item["name"]
                    download_url = item["download_url"]
                    if not download_url:
                        continue
                    
                    file_dest = os.path.join(dest_dir, file_name)
                    print(f"Descargando {file_name}...")
                    
                    file_req = urllib.request.Request(download_url)
                    file_req.add_header('User-Agent', 'Fina-Installer')
                    with urllib.request.urlopen(file_req) as f_res:
                        with open(file_dest, "wb") as f_out:
                            f_out.write(f_res.read())
                    
                    # Hacer ejecutables los .py y .sh
                    if file_name.endswith('.py') or file_name.endswith('.sh'):
                        os.chmod(file_dest, 0o755)
                        
            print(f"✅ Plugin instalado con éxito en {dest_dir}")
            
    except urllib.error.HTTPError as e:
        error_exit(f"Fallo HTTP al contactar GitHub Market: {e.code} - {e.reason}")
    except Exception as e:
        error_exit(f"Fallo al instalar: {e}")

if __name__ == "__main__":
    main()
