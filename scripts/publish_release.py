import os
import re
import requests
import sys

def get_config_token():
    config_path = "/home/claudio/Descargas/Fina-Ergen/config.py"
    if not os.path.exists(config_path):
        return None
    with open(config_path, "r") as f:
        content = f.read()
        match = re.search(r'GITHUB_TOKEN\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
    return None

def get_repo_info():
    # Retorna (owner, repo) extraído del remote de git
    try:
        import subprocess
        remote = subprocess.check_output(["git", "remote", "get-url", "origin"]).decode().strip()
        # Formatos: https://github.com/owner/repo.git o git@github.com:owner/repo.git
        match = re.search(r'github\.com[:/]([^/]+)/([^.]+)(\.git)?', remote)
        if match:
            return match.group(1), match.group(2)
    except:
        pass
    return "dankopetro", "Fina-Ergen"

def get_release_notes(version):
    notes_path = "/home/claudio/Descargas/Fina-Ergen/TEXTOS_PARA_GITHUB_RELEASES.txt"
    if not os.path.exists(notes_path):
        return f"Release {version}"
    
    with open(notes_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Buscar el bloque que empieza con ========== PARA LA VERSIÓN v... ==========
    # y termina antes del siguiente bloque o final del archivo
    pattern = rf"========== PARA LA VERSIÓN {version} ==========\n(.*?)(?=== PARA LA VERSIÓN|$)"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return f"Release {version}"

def publish(version):
    token = get_config_token()
    if not token:
        print("Error: No se encontró GITHUB_TOKEN en config.py")
        return

    owner, repo = get_repo_info()
    notes = get_release_notes(version)
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Buscar el release por tag
    url_get = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{version}"
    res = requests.get(url_get, headers=headers)
    
    if res.status_code == 200:
        release_id = res.json()["id"]
        # 2. Actualizar el release existente
        url_patch = f"https://api.github.com/repos/{owner}/{repo}/releases/{release_id}"
        payload = {"body": notes}
        res_patch = requests.patch(url_patch, json=payload, headers=headers)
        if res_patch.status_code == 200:
            print(f"✅ Notas de la versión {version} actualizadas en GitHub exitosamente.")
        else:
            print(f"❌ Error al actualizar release: {res_patch.status_code} - {res_patch.text}")
    else:
        # 3. Si no existe, intentar crear uno nuevo (opcional, pero mejor avisar)
        print(f"⚠️ No se encontró un release con el tag {version}. Asegúrate de que el tag exista en GitHub.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 publish_release.py <version>")
        sys.exit(1)
    
    version_arg = sys.argv[1]
    publish(version_arg)
