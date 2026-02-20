import os
import sqlite3
import re
import sys

def search_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Patrones comunes de Tuya
            patterns = {
                "localKey": r'localKey["\\]*[:=]+["\\]*([a-zA-Z0-9]+)',
                "devId": r'devId["\\]*[:=]+["\\]*([a-zA-Z0-9]+)',
                "token": r'token["\\]*[:=]+["\\]*([a-zA-Z0-9]+)',
                "secKey": r'secKey["\\]*[:=]+["\\]*([a-zA-Z0-9]+)'
            }
            
            found = False
            for key, regex in patterns.items():
                matches = re.findall(regex, content)
                for m in matches:
                    print(f"   🔥 {key} encontrada: {m}")
                    found = True
            
            # Búsqueda genérica de keys de 16 caracteres (común en Tuya)
            if not found:
                 # A veces están en XML plano: <string name="gw_bi">...</string>
                 if "localKey" in content:
                     print(f"   ⚠️ 'localKey' texto presente en {os.path.basename(filepath)} (Revisar manual)")

    except Exception as e:
        print(f"Error leyendo {filepath}: {e}")

def convert_and_analyze_db(db_path):
    print(f"📦 Analizando DB: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            t = table[0]
            # print(f"  Tabla: {t}")
            if "device" in t.lower() or "user" in t.lower():
                print(f"  🕵️ Escaneando tabla sensible: {t}")
                try:
                    cursor.execute(f"SELECT * FROM {t}")
                    rows = cursor.fetchall()
                    for row in rows:
                        row_str = str(row)
                        if "localKey" in row_str or len(row_str) > 50: # Solo imprimir cosas interesantes
                             # Limpiar un poco el output
                             if "localKey" in row_str:
                                 print(f"  🔥 MATCH DB: {row_str[:200]}...")
                except:
                    pass
        conn.close()
    except Exception as e:
        print(f"  ❌ No se pudo leer DB (¿Encriptada?): {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python analyze_loot.py <carpeta_dump>")
        sys.exit(1)
        
    target_dir = sys.argv[1]
    print(f"🕵️ Iniciando Análisis Forense en: {target_dir}")
    
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            full_path = os.path.join(root, file)
            
            if file.endswith(".xml") or file.endswith(".conf"):
                # print(f"📄 Xml: {file}")
                search_in_file(full_path)
            
            elif file.endswith(".db"):
                convert_and_analyze_db(full_path)
