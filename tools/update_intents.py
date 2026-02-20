import json
import os

file_path = 'intents.json'

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Lists provided by user
    to_exit = [
        "adiós", "vale, adiós", "adiós por ahora", "adiós por ahora, Fina", "adiós asistente",
        "salir", "¡salir!", "salir ahora", "salir del programa", "salir de la aplicación",
        "cerrar sesión", "cerrar sesión ahora", "cerrar sesión en el asistente", "cerrando ahora",
        "desconectar", "finalizar", "finalizar sesión", "dejar", "apagar el asistente", 
        "vete al infierno"
    ]

    to_sleep = [
        "nos vemos luego", "hasta luego", "hasta pronto", "hasta la próxima", "buenas noches",
        "cuídate", "que tengas un buen día", "ya me voy", "ya salgo", "ya terminé",
        "Terminé", "Terminé aquí", "volveré"
    ]

    # Add to 'exit'
    if 'exit' not in data:
        data['exit'] = []
    
    # Avoid duplicates when adding
    current_exit = set(data['exit'])
    for phrase in to_exit:
        if phrase not in current_exit:
            data['exit'].append(phrase)

    # Add to 'sleep'
    if 'sleep' not in data:
        data['sleep'] = []
        
    current_sleep = set(data['sleep'])
    for phrase in to_sleep:
        if phrase not in current_sleep:
            data['sleep'].append(phrase)

    # Remove old_exit_deprecated
    if 'old_exit_deprecated' in data:
        del data['old_exit_deprecated']
        print("Removed old_exit_deprecated")
    else:
        print("old_exit_deprecated not found")

    # Save
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print("Successfully updated intents.json")

except Exception as e:
    print(f"Error: {e}")
