
import sys
import os
 
# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import config
print(f"DEBUG: Contents of config module: {dir(config)}")
from utils import send_email

EMAIL_USER = config.EMAIL_USER
EMAIL_PASSWORD = config.EMAIL_PASSWORD
TARGET_EMAIL = EMAIL_USER 

MANUAL_PATH = os.path.join(PROJECT_ROOT, "Manual_Usuario_Fina.pdf")

print(f"Enviando manual a {TARGET_EMAIL}...")
subject = "Manual de Usuario - Fina Asistente de Voz"
body = "Adjunto encontrarás el manual de usuario completo de Fina."

if not os.path.exists(MANUAL_PATH):
    print(f"Error: No se encuentra el archivo {MANUAL_PATH}")
    sys.exit(1)

result = send_email(EMAIL_USER, EMAIL_PASSWORD, TARGET_EMAIL, subject, body, attachment_path=MANUAL_PATH)
print(f"Resultado: {result}")
