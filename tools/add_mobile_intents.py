
import json
import os

file_path = './intents.json'

if not os.path.exists(file_path):
    print("Error: intents.json not found")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Agregar nuevos intents si no existen
if 'send_message' not in data:
    data['send_message'] = [
        "enviar un whatsapp",
        "enviar mensaje",
        "mandale un whatsapp",
        "envía un telegram",
        "escribir por whatsapp",
        "dile por whatsapp",
        "mándale un mensaje",
        "envía un sms",
        "mándale un texto",
        "mensaje de whatsapp",
        "mensaje de telegram",
        "mensaje de signal",
        "enviar mensaje a",
        "whatsapp a",
        "telegram a",
        "envíale un mensaje a",
        "mándale un wasap a",
        "escribile a",
        "dile a"
    ]

if 'make_call' not in data:
    data['make_call'] = [
        "llama a",
        "llamar a",
        "hacer una llamada",
        "marcar a",
        "teléfono a",
        "quiero llamar a",
        "llama por teléfono",
        "márcale a",
        "haz una llamada a",
        "comunícame con"
    ]

with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ Intents de mensajería agregados.")
