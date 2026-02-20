#!/usr/bin/env python3
"""
Script: sintoniza_canales.py

Objetivo: Automatizar la captura de los canales de la TV usando screenshots del EPG.

Flujo:
1. Detectar la IP de la TV (ADB).
2. Recorrer una lista de canales comunes.
3. Sintonizar cada canal (entrada rápida).
4. Esperar a que la TV muestre el EPG.
5. Extraer el nombre del canal usando uiautomator dump y parsing XML.
6. Si la extracción automática falla, solicitar al usuario que ingrese el nombre manualmente.
7. Guardar el mapeo ``canales.json`` con la estructura:
   {
       "Canal 80.1": "Nombre del canal",
       ...
   }

Requisitos externos:
- ``pytesseract`` y ``Pillow`` instalados en el entorno Python.
- Tesseract OCR disponible en el sistema (``sudo apt install tesseract-ocr``).
"""

import subprocess
import json
import time
import os
import re
from pathlib import Path
import argparse

# Intentar importar dependencias si fueran necesarias
try:
    import requests # para notificar a la UI de Fina si se desea
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
TV_IPS = ["192.168.0.11", "192.168.0.10"]  # IPs posibles de la TV
COMMON_CHANNELS = [
    "80.1", "80.2", "80.3", "80.4", "80.5", "80.6", "80.7", "80.8",
    "81.1", "81.2", "81.3", "81.4", "81.5", "81.6", "81.7", "81.8",
    "82.1", "82.2", "82.3", "82.4", "82.5", "82.6", "82.7", "82.8",
    "83.1", "83.2", "83.3", "83.4", "83.5", "83.6", "83.7", "83.8",
    "84.1", "84.2", "84.3", "84.4", "84.5", "84.6", "84.7", "84.8",
    "85.1", "85.2", "85.3", "85.4", "85.5", "85.6", "85.7", "85.8",
    "86.1", "86.2", "86.3", "86.4", "86.5", "86.6", "86.7", "86.8",
    "87.1", "87.2", "87.3", "87.4", "87.5", "87.6", "87.7", "87.8",
    "88.1", "88.2", "88.3", "88.4", "88.5", "88.6", "88.7", "88.8",
    "89.1", "89.2", "89.3", "89.4", "89.5", "89.6", "89.7", "89.8",
]

# Obtener la raíz del proyecto para guardar channels.json
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = PROJECT_ROOT / "channels.json"
REFERENCE_FILE = PROJECT_ROOT / "cannels.json" # Lista base para comparar

# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def get_tv_ip():
    """Devuelve la primera IP que responde a un comando ADB simple."""
    for ip in TV_IPS:
        try:
            result = subprocess.run(
                ["adb", "-s", f"{ip}:5555", "shell", "echo", "test"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0:
                return ip
        except Exception:
            continue
    return None


def send_key(ip, keycode):
    """Envío genérico de un keyevent vía ADB."""
    subprocess.run(
        ["adb", "-s", f"{ip}:5555", "shell", "input", "keyevent", keycode],
        capture_output=True,
        text=True,
        timeout=3,
    )


def tune_channel_fast(ip, channel_number):
    """Sintoniza un canal rápidamente (sin comprobación de señal)."""
    print(f"🔧 Sintonizando {channel_number}...")
    # Abrir la app de TV (asumiendo que ya está en primer plano)
    subprocess.run(
        ["adb", "-s", f"{ip}:5555", "shell", "am", "start", "-n", "com.tcl.tv/.TVActivity"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    time.sleep(0.5)
    # MÉTODO ULTRA RÁPIDO: Un solo proceso para todas las teclas
    print(f"   Enviando ráfaga instantánea: {channel_number} ", end="", flush=True)
    
    key_map = {
        '0': '7', '1': '8', '2': '9', '3': '10', '4': '11',
        '5': '12', '6': '13', '7': '14', '8': '15', '9': '16',
        '.': '158' # KEYCODE_NUMPAD_DOT
    }
    
    keycodes = [key_map.get(d) for d in str(channel_number) if key_map.get(d)]
    keycodes.append('66') # Enter
    
    # Enviamos todos los keycodes como argumentos de un único comando 'input'
    # Esto elimina el retraso de inicio de proceso por cada dígito.
    try:
        subprocess.run(
            ["adb", "-s", f"{ip}:5555", "shell", "input", "keyevent"] + keycodes,
            capture_output=True,
            timeout=10,
        )
        print("[OK]")
    except Exception as e:
        print(f"[Error: {e}]")
    
    # Esperar a que la barra de info aparezca
    time.sleep(1.5)


# Eliminada función capture_epg ya que usaremos uiautomator dump


def xml_extract_name(ip, channel_number):
    """Extrae el nombre del canal desde el volcado de UI (XML)."""
    try:
        remote_xml = "/sdcard/view.xml"
        local_xml = "/tmp/view.xml"
        
        # 1. Volcar UI
        subprocess.run(["adb", "-s", f"{ip}:5555", "shell", "uiautomator", "dump", remote_xml], 
                      capture_output=True, timeout=5)
        
        # 2. Descargar XML
        subprocess.run(["adb", "-s", f"{ip}:5555", "pull", remote_xml, local_xml], 
                      capture_output=True, timeout=5)
        
        if not os.path.exists(local_xml):
            return None
            
        with open(local_xml, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 3. Buscar el número del canal en el XML y obtener el texto cercano
        # El formato del XML es: ... text="80.5" ... text="Telefe" ...
        # Buscamos el nodo que contiene el número y luego buscamos textos descriptivos cercanos
        
        # Extraer todos los atributos 'text'
        all_texts = re.findall(r'text="([^"]+)"', content)
        
        if not all_texts:
            return None
            
        # Buscar el índice del número del canal
        ch_str = str(channel_number)
        for i, text in enumerate(all_texts):
            if text == ch_str:
                # El nombre suele ser el siguiente texto (o el anterior)
                # Probamos el siguiente primero
                if i + 1 < len(all_texts):
                    candidate = all_texts[i+1].strip()
                    # Evitar repetir el número o capturar textos vacíos/largos de programas
                    if candidate and candidate != ch_str and len(candidate) < 50:
                        return candidate
                # Si no, probamos el anterior
                if i > 0:
                    candidate = all_texts[i-1].strip()
                    if candidate and candidate != ch_str and len(candidate) < 50:
                        return candidate
        
        return None
    except Exception as e:
        print(f"⚠️ Error extrayendo nombre del XML: {e}")
        return None


def save_channels(scanned_channels, filename=OUTPUT_FILE, reference=REFERENCE_FILE):
    """
    Compara el escaneo con la lista vieja y gestiona DESPLAZAMIENTOS DE GRUPO.
    Si un canal principal se mueve, sus etiquetas (dibujitos, futbol, etc) lo siguen.
    """
    print("\n--- 🧠 Procesando cambios y desplazamientos de grupo ---")
    
    final_list = {}
    # Cargar la lista ACTUAL (donde están tus etiquetas manuales)
    if filename.exists():
        try:
            with open(filename, "r", encoding="utf-8") as f:
                final_list = json.load(f)
        except: pass
    elif reference.exists():
        try:
            with open(reference, "r", encoding="utf-8") as f:
                final_list = json.load(f)
        except: pass

    # 1. Detectar qué canales físicos se movieron (Mapeo de Nros Viejos -> Nros Nuevos)
    # Ejemplo: Si "telefe" era 80.1 y ahora es 80.2, guardamos { "80.1": "80.2" }
    movimientos_fisicos = {}
    for name, num in scanned_channels.items():
        num_str = str(num)
        if name in final_list:
            old_num = str(final_list[name])
            if old_num != num_str:
                movimientos_fisicos[old_num] = num_str
                print(f"🏃 Movimiento detectado: {name} ({old_num} ➡️ {num_str})")

    # 2. Mover TODAS las etiquetas que apuntaban a los números viejos
    # Esto salva a "dibujitos", "futbol", etc.
    cambios_realizados = []
    for alias, current_num in list(final_list.items()):
        current_num_str = str(current_num)
        if current_num_str in movimientos_fisicos:
            new_pos = movimientos_fisicos[current_num_str]
            if alias not in scanned_channels: # Solo si es una etiqueta manual (no escaneada hoy)
                final_list[alias] = new_pos
                cambios_realizados.append(f"🔗 Etiqueta '{alias}' siguió el movimiento a {new_pos}")

    for msg in cambios_realizados:
        print(msg)

    # 3. Actualizar/Reemplazar con los nombres exactos detectados hoy
    for name, num in scanned_channels.items():
        num_str = str(num)
        # Limpiar cualquier cosa que estuviera en el nuevo número para evitar "fantasmas"
        # pero conservamos los que acabamos de mover nosotros arriba.
        to_del = [n for n, v in final_list.items() if str(v) == num_str and n != name and n not in cambios_realizados]
        # (Nota: no borramos si es una etiqueta que ya actualizamos en el paso 2)
        
        final_list[name] = num_str

    # 4. Guardar ordenado
    try:
        def sort_key(x):
            try: return float(x[1])
            except: return 0.0
        sorted_channels = dict(sorted(final_list.items(), key=sort_key))
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(sorted_channels, f, indent=4, ensure_ascii=False)
        print(f"✅ Lista DEFINITIVA actualizada. Total: {len(sorted_channels)} canales.")
    except Exception as e:
        print(f"❌ Error al guardar: {e}")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Escanea canales de TV vía ADB y XML.")
    parser.add_argument("--ip", help="IP de la TV (opcional)")
    parser.add_argument("--non-interactive", action="store_true", help="No pedir entrada manual si falla detección")
    parser.add_argument("--channels", help="Lista de canales separados por coma (ej: 80.1,80.2)")
    args = parser.parse_args()

    print("📺 Iniciando sintonizador (EPG + XML)")
    
    ip = args.ip if args.ip else get_tv_ip()
    
    if not ip:
        print("❌ No se encontró ninguna TV conectada vía ADB.")
        return
    print(f"🔗 Usando TV en {ip}")

    channels_to_scan = COMMON_CHANNELS
    if args.channels:
        channels_to_scan = [c.strip() for c in args.channels.split(",")]

    # Lista TEMPORAL de este escaneo
    canales_detectados_hoy = {}

    for ch in channels_to_scan:
        intentos = 0
        nombre = None
        
        while intentos < 3:
            tune_channel_fast(ip, ch)
            if intentos > 0:
                print(f"🔄 Reintentando detección para {ch} (Intento {intentos + 1}/3)...")
                time.sleep(1.0) # Un poco más de tiempo en reintento
                
            nombre = xml_extract_name(ip, ch)
            if nombre:
                break
            intentos += 1
        
        if not nombre:
            if args.non_interactive:
                print(f"⏭️ No se detectó nombre para {ch}, saltando (modo no interactivo).")
                continue
            
            print(f"❓ No se detectó nombre automáticamente para {ch}.")
            # Fallback manual
            try:
                res = input(f"   👉 Nombre para {ch} (Enter para saltar): ").strip()
                if res:
                    nombre = res
                else:
                    continue
            except EOFError:
                continue
        
        # Guardar en temporal
        nombre_clean = nombre.lower().strip()
        print(f"✅ Detectado: {nombre_clean} → {ch}")
        canales_detectados_hoy[nombre_clean] = str(ch)
        
        # Pausa mínima
        time.sleep(0.1)

    # Solo procesamos si detectamos algo
    if canales_detectados_hoy:
        save_channels(canales_detectados_hoy)
    else:
        print("⚠️ No se detectó ningún canal nuevo para comparar.")

    print("\n🏁 Proceso completado.")

if __name__ == "__main__":
    main()
