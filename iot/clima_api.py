import urllib.request
import json
import socket
import sys

# Script robusto para obtener clima usando argumentos
# Timeout rápido para no colgar la UI
socket.setdefaulttimeout(5)

# Valores por defecto o argumentos
if len(sys.argv) > 2:
    API_KEY = sys.argv[1]
    CITY_ID = sys.argv[2]
else:
    # Fallback o Error
    print(json.dumps({"cod": 400, "message": "Missing API Key or City ID arguments"}))
    sys.exit(1)

URL = f"http://api.openweathermap.org/data/2.5/weather?id={CITY_ID}&appid={API_KEY}&units=metric&lang=es"

try:
    # Usamos urllib estándar de Python (sin pip install requests)
    req = urllib.request.Request(URL)
    with urllib.request.urlopen(req) as response:
        data = response.read()
        # Imprimir JSON crudo a stdout
        print(data.decode('utf-8'))
except Exception as e:
    # JSON de error controlado
    error_json = {"cod": 500, "message": str(e)}
    print(json.dumps(error_json))
