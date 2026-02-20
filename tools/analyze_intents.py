import json
import re
from collections import defaultdict

# 1. Load Intents
try:
    with open('intents.json', 'r') as f:
        intents_data = json.load(f)
except Exception as e:
    print(f"Error loading intents.json: {e}")
    exit()

# 2. Load Main.py to find handlers
try:
    with open('main.py', 'r') as f:
        main_code = f.read()
except Exception as e:
    print(f"Error loading main.py: {e}")
    exit()

# 3. Analyze Intents vs Handlers
implemented_intents = set()
# Search for 'intent == "name"' or 'intent == 'name'' or 'case "name"'
matches = re.findall(r'intent\s*==\s*["\']([^"\']+)["\']', main_code)
implemented_intents.update(matches)

# 4. Check phrases for duplicates
phrase_map = defaultdict(list)
all_phrases_count = 0
for intent, phrases in intents_data.items():
    for phrase in phrases:
        p_lower = phrase.lower().strip()
        phrase_map[p_lower].append(intent)
        all_phrases_count += 1

# 5. Generate Report
print(f"--- ANÁLISIS DE INTENTS ({all_phrases_count} frases totales) ---")

# A. Desconectados (En JSON pero no en Main)
json_keys = set(intents_data.keys())
disconnected = json_keys - implemented_intents
print(f"\n[DESCONECTADOS] Intents en JSON que NO tienen código en main.py ({len(disconnected)}):")
for k in disconnected:
    print(f"  - {k} ({len(intents_data[k])} frases)")

# B. Duplicados (Frases que activan múltiples intents)
duplicates = {k: v for k, v in phrase_map.items() if len(v) > 1}
if duplicates:
    print(f"\n[CONFLICTOS] Frases repetidas en múltiples intents ({len(duplicates)}):")
    for phrase, intents in list(duplicates.items())[:20]: # Show first 20
        print(f"  - '{phrase}': {intents}")
    if len(duplicates) > 20:
        print(f"  ... y {len(duplicates)-20} más.")

# C. Revisión de coherencia (Heurística simple)
print(f"\n[REVISIÓN SEMÁNTICA]")
# Check specific examples mentioned by user
exit_phrases_in_wrong_places = []
for intent, phrases in intents_data.items():
    if intent not in ['exit', 'exit_fina', 'shutdown', 'suspend', 'sleep', 'old_exit_deprecated']:
        for p in phrases:
            if any(x in p.lower() for x in ['salir', 'adios', 'adiós', 'apagar', 'duerme']):
                exit_phrases_in_wrong_places.append((intent, p))

if exit_phrases_in_wrong_places:
    print("  ⚠️ Frases de 'salir/apagar' encontradas en intents incorrectos:")
    for i, p in exit_phrases_in_wrong_places:
        print(f"    - '{p}' en intent '{i}'")

print("\n--- FIN DEL REPORTE ---")
