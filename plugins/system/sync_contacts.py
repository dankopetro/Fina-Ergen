
import subprocess
import re
import json
import os
import sys

# Ruta absoluta basada en la ubicación del script
def get_config_dir():
    # Prioridad XDG
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return os.path.join(xdg_config, "Fina")
    # Rescate Home
    try:
        from pathlib import Path
        return os.path.join(str(Path.home()), ".config", "Fina")
    except:
        return os.path.expanduser("~/.config/Fina")

CONFIG_DIR = get_config_dir()
CONFIG_PATH = os.path.join(CONFIG_DIR, "contact.json")
# Soporte para plural
if not os.path.exists(CONFIG_PATH) and os.path.exists(os.path.join(CONFIG_DIR, "contacts.json")):
    CONFIG_PATH = os.path.join(CONFIG_DIR, "contacts.json")

def clean_number(num):
    # Remove separators: spaces, dashes, parens
    cleaned = re.sub(r'[\s\-\(\)\.]', '', num)
    return cleaned

def sync_contacts():
    print("📱 Sincronizando contactos del celular...")
    
    # 1. Verificar dispositivo conectado
    try:
        check = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        if "device" not in check.stdout or "List" not in check.stdout:
            print("⚠️ No hay dispositivo conectado.")
            return
    except:
        return

    # 2. Obtener contactos via ADB Content Provider
    # Proyección: display_name (Nombre), data1 (Número)
    cmd = ["adb", "shell", "content", "query", "--uri", "content://com.android.contacts/data/phones", "--projection", "display_name:data1"]
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        output = res.stdout
    except Exception as e:
        print(f"Error ejecutando ADB: {e}")
        return

    # 3. Parsear salida
    # Formato típico: "Row: 0 display_name=Juan Perez, data1=+54911..."
    extracted_contacts = {}
    
    lines = output.strip().split('\n')
    for line in lines:
        if "display_name=" in line:
            try:
                # Regex robusto para capturar valores
                # A veces ADB devuelve "Row: 0 display_name=Nombre, data1=Num"
                # Ojo con las comas en los nombres
                
                # Estrategia: buscar key=value
                name_match = re.search(r'display_name=([^,]+)', line)
                # data1 suele estar al final o entre comas
                num_match = re.search(r'data1=([^,]+)', line)
                
                # Si data1 está al final, el regex anterior puede fallar si no hay coma después
                if not num_match:
                     num_match = re.search(r'data1=(.*)$', line)

                if name_match and num_match:
                    name = name_match.group(1).strip()
                    # Limpiar data1 de posibles artifactos finales
                    num = num_match.group(1).strip()
                    
                    # Limpieza extra si hay } o ] al final (raro pero posible)
                    
                    clean_num = clean_number(num)
                    
                    if name and len(clean_num) > 3:
                        extracted_contacts[name] = clean_num
            except Exception as e:
                # print(f"Error parseando linea: {line} -> {e}")
                continue

    if not extracted_contacts:
        print("⚠️ No se pudieron extraer contactos (o la lista está vacía).")
        # No sobreescribimos si falló la lectura
        return

    print(f"✅ Se leyeron {len(extracted_contacts)} contactos del dispositivo.")

    # 4. Cargar existentes
    existing = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except: existing = {}

    # 5. Fusionar (Prioridad: Móvil actualiza números, pero mantenemos los manuales no encontrados)
    # Si queremos que Fina "aprenda" del celular, agregamos todo.
    existing.update(extracted_contacts)
    
    # 6. Guardar
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        print(f"💾 Base de datos de contactos actualizada en: {CONFIG_PATH}")
        print(f"👥 Total de contactos: {len(existing)}")
    except Exception as e:
        print(f"❌ Error guardando archivo JSON: {e}")

if __name__ == "__main__":
    sync_contacts()
