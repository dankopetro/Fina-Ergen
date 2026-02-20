import os
import sys
import shutil
import requests
import zipfile
import io

def install_plugin(category, subpath):
    repo_url = "https://github.com/dankopetro/Fina-Plugins-Market/archive/refs/heads/main.zip"
    plugins_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "plugins")
    
    print(f"Buscando plugin: {category}/{subpath}...")
    
    try:
        # Download ZIP
        r = requests.get(repo_url)
        if r.status_code != 200:
            print(f"ERROR: No se pudo descargar el repositorio ({r.status_code})")
            return
            
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            # The root folder in the zip is usually Fina-Plugins-Market-main
            root = z.namelist()[0]
            # Construct target path in zip
            # Example: Fina-Plugins-Market-main/TVs/TCL/tcl32s60a/
            target_zip_path = f"{root}{category}/{subpath}/"
            
            # Find all files belonging to this plugin
            plugin_files = [f for f in z.namelist() if f.startswith(target_zip_path)]
            
            if not plugin_files:
                print(f"ERROR: No se encontró el plugin en la ruta {target_zip_path}")
                return
                
            # Final destination: plugins/<subpath_name>
            plugin_name = os.path.basename(subpath.rstrip('/'))
            dest_dir = os.path.join(plugins_dir, category.lower(), plugin_name)
            
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            os.makedirs(dest_dir, exist_ok=True)
            
            print(f"Instalando en {dest_dir}...")
            
            for f in plugin_files:
                if f.endswith('/'): continue # Skip directories
                
                # Get relative path from target_zip_path
                relative_path = f[len(target_zip_path):]
                dest_file = os.path.join(dest_dir, relative_path)
                
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                with open(dest_file, 'wb') as df:
                    df.write(z.read(f))
            
            print(f"SUCCESS: Plugin {plugin_name} instalado correctamente.")
            
    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 install_plugin.py <Category> <SubPath>")
        sys.exit(1)
        
    install_plugin(sys.argv[1], sys.argv[2])
