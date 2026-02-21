import os
import sys
import requests
import json

# Add project root to sys path to import config
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
sys.path.insert(0, project_dir)

try:
    from config import GITHUB_TOKEN
    import utils # For load_config
    config, _ = utils.load_config()
    TOKEN = config.GITHUB_TOKEN if hasattr(config, 'GITHUB_TOKEN') and config.GITHUB_TOKEN != "your_github_token_here" else GITHUB_TOKEN
except ImportError:
    print("Error importing config")
    sys.exit(1)

if not TOKEN or TOKEN == "your_github_token_here":
    print("Error: No valid GitHub token found in config.py")
    sys.exit(1)

REPO_OWNER = "dankopetro"
REPO_NAME = "Fina-Ergen"
API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def update_release_notes():
    # Obtener todas las releases
    print(f"Obteniendo releases de {REPO_OWNER}/{REPO_NAME}...")
    response = requests.get(API_URL, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"Error cargando releases: {response.text}")
        return
        
    releases = response.json()
    
    # Texto a añadir a TODAS las releases antiguas y nuevas
    appimage_explanation = """
### 📦 ¿Qué archivo descargar?
Encontrarás dos versiones de AppImage en los assets de cada versión:

1.  **fina-ergen_v..._amd64.AppImage (RECOMENDADO)**: Versión optimizada con compresión **XZ**. Es más liviana (pesa mucho menos) y tiene parches de compatibilidad críticos para resolver problemas de íconos y falta de librerías (`libfuse2`) en sistemas operativos modernos como Ubuntu 24.04+ y Linux Mint 22+.
2.  **fina-ergen_v..._x86_64.AppImage**: Versión estándar (sin comprimir/parchear) generada directamente por Tauri (solo usar si la otra da problemas).
"""

    for release in releases:
        tag = release['tag_name']
        release_id = release['id']
        body = release.get('body', '') or ''
        
        # Evitar duplicar el texto si ya lo añadimos antes
        if "¿Qué archivo descargar?" in body:
            print(f"La release {tag} ya contiene la explicación. Saltando...")
            continue
            
        print(f"Actualizando la release {tag}...")
        
        # Añadir la explicación al final
        new_body = body + "\n\n---\n" + appimage_explanation
        
        # Opcional: Notas específicas de la versión
        if tag == "v3.5.4-12":
            new_body = new_body.replace("---", "### 🛠️ Novedades de esta Versión:\n*   **Universalidad Total**: Se han eliminado todas las rutas locales fijas. Fina ahora detecta su ubicación y recursos dinámicamente.\n*   **Persistencia Segura**: Tus ajustes, contactos y perfiles de voz ahora se guardan en `~/.config/Fina/`, permitiendo actualizar la aplicación sin perder tus datos.\n*   **Gestión de Plugins Avanzada**: Soporte para instalación de plugins en la carpeta del usuario. ¡Tus extensiones te siguen a donde vayas!\n*   **Optimización de Recursos**: El sistema de Android (Waydroid/Weston) ahora solo se activa si tienes un timbre configurado, ahorrando mucha memoria y CPU.\n*   **Clima en Tiempo Real**: Sincronización inmediata al arranque.\n\n---")
            
        elif tag == "v3.5.4-8" or tag == "v3.5.4-7":
            new_body = new_body.replace("---", "### 🛠️ Novedades de esta Versión:\n*   **Mejora de Portabilidad de UI**: Refactorización profunda cómo Vue se comunica con el backend de Python, sustituyendo comandos de terminal duros por llamadas correctas a las API.\n*   **Mejoras en Plugins**: Optimizaciones en los detectores de clima y timbres.\n\n---")
            
        # Petición PATCH para actualizar
        update_url = f"{API_URL}/{release_id}"
        patch_data = {"body": new_body}
        
        update_response = requests.patch(update_url, headers=HEADERS, json=patch_data)
        
        if update_response.status_code == 200:
            print(f"✅ Release {tag} actualizada correctamente.")
        else:
            print(f"❌ Error actualizando {tag}: {update_response.text}")

if __name__ == "__main__":
    update_release_notes()
    print("\nProceso finalizado.")
