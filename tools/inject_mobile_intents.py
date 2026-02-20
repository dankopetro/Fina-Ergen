
import sys

file_path = './main.py'
inject_file = './fina_mobile_intents.py'

with open(file_path, 'r', encoding='utf-8') as f:
    main_content = f.read()

with open(inject_file, 'r', encoding='utf-8') as f:
    mobile_code = f.read()

# Buscar punto de inserción: justo antes de los emails
marker = 'elif intent == "read_email":'

if marker in main_content:
    # Insertar con indentación correcta
    new_content = main_content.replace(marker, mobile_code + "\n            " + marker)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ Código de mensajes por voz inyectado en main.py")
else:
    print("Error: No encontré el punto de inserción.")
