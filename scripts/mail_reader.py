import sys
import json
import os
import imaplib
import email
from email.header import decode_header

def decode_mime_words(s):
    if not s: return ""
    try:
        return u''.join(
            word.decode(encoding or 'utf8') if isinstance(word, bytes) else word
            for word, encoding in decode_header(s))
    except: return str(s)

def read_emails():
    # Path to settings.json (relative to scripts/mail_reader.py)
    # ../config/settings.json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    settings_path = os.path.join(base_dir, "config", "settings.json")
    
    user, password = None, None
    try:
        with open(settings_path, 'r') as f:
            data = json.load(f)
            apis = data.get("apis", {})
            user = apis.get("EMAIL_USER")
            password = apis.get("EMAIL_PASSWORD")
            
            # Legacy fallback
            if not user: user = data.get("EMAIL_USER")
            if not password: password = data.get("EMAIL_PASSWORD")
    except Exception as e:
        return {"status": "error", "message": f"Error leyendo settings: {e}"}

    if not user or not password:
         return {"status": "error", "message": "Faltan credenciales en settings.json"}

    try:
        # Timeout de 10 segundos para evitar que el script quede colgado
        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=10)
        mail.login(user, password)
        mail.select("inbox")
        
        # Fetch UNSEEN (Unread)
        status, messages = mail.search(None, '(UNSEEN)')
        mail_ids = messages[0].split()
        
        # Get only last 5
        recent_ids = mail_ids[-5:]
        
        emails = []
        for i in reversed(recent_ids):
            # USAR PEEK PARA NO MARCAR COMO LEÍDO AUTOMÁTICAMENTE
            _, msg_data = mail.fetch(i, "(BODY.PEEK[])")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_mime_words(msg["Subject"])
                    sender = decode_mime_words(msg.get("From"))
                    date_val = msg.get("Date")
                    emails.append({
                        "subject": subject,
                        "from": sender,
                        "date": date_val
                    })
        mail.close()
        mail.logout()
        return {"status": "success", "emails": emails}

    except Exception as e:
        err_msg = str(e)
        if "Application-specific password required" in err_msg:
            return {
                "status": "error", 
                "error_type": "auth_app_password",
                "message": "Gmail requiere una 'Contraseña de Aplicación'. Por favor, genérala en tu cuenta de Google."
            }
        return {"status": "error", "message": f"IMAP Error: {err_msg}"}

if __name__ == "__main__":
    print(json.dumps(read_emails()))
