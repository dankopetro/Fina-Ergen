
import sys
import os
import time
import datetime
import logging

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

import config
from utils import send_email

# Importar configuración de correo
EMAIL_USER = config.EMAIL_USER
EMAIL_PASSWORD = config.EMAIL_PASSWORD
# Usaremos el mismo correo del usuario como destinatario si no está en contact.json, 
# pero el prompt dice "mi correo electrónico". Asumiremos que el usuario quiere recibirlo en su propio correo (EMAIL_USER) o el configurado.
# Para seguridad, lo enviaremos a EMAIL_USER (asumiendo que es el correo del usuario).
TARGET_EMAIL = EMAIL_USER 

MANUAL_PATH = os.path.join(PROJECT_ROOT, "Manual_Usuario_Fina.pdf")

def schedule_email():
    now = datetime.datetime.now()
    # Objetivo: Hoy a las 13:00
    target_time = now.replace(hour=13, minute=0, second=0, microsecond=0)
    
    # Si ya pasó la 1 PM, programar para mañana? O enviar ya?
    # El usuario dijo "del dia de hoy". Si son las 14:00, ya pasó.
    # Pero son las 11:58, así que está en el futuro.
    
    if target_time < now:
        print("La hora programada (13:00) ya pasó hoy.")
        # Opcional: enviarlo ahora si el usuario insiste, pero el script debería respetar la orden.
        # Sin embargo, para pruebas, si estamos cerca, esperamos.
        return

    delay = (target_time - now).total_seconds()
    print(f"Esperando {delay:.2f} segundos para enviar el manual a las 13:00...")
    
    time.sleep(delay)
    
    print("Enviando manual...")
    subject = "Manual de Usuario - Fina Asistente de Voz"
    body = "Adjunto encontrarás el manual de usuario completo de Fina, con instrucciones de instalación y lista de comandos."
    
    result = send_email(EMAIL_USER, EMAIL_PASSWORD, TARGET_EMAIL, subject, body, attachment_path=MANUAL_PATH)
    print(f"Resultado: {result}")

if __name__ == "__main__":
    schedule_email()
