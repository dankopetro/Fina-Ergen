
import os
import json
import tinytuya
import sys

# Configuración
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "tuya_config.json")

# Silenciar prints normales
sys.stdout = open(os.devnull, 'w')

try:
    with open(CONFIG_PATH, "r") as f:
        conf = json.load(f)

    c = tinytuya.Cloud(
        apiRegion=conf['region_code'], 
        apiKey=conf['access_id'], 
        apiSecret=conf['access_secret'], 
        apiDeviceID=conf['device_id']
    )

    uri = f'/v1.0/devices/{conf["device_id"]}/stream/actions/allocate'
    body = {"type": "hls"}
    
    response = c.cloudrequest(uri, post=body)
    
    # Restaurar stdout para imprimir SOLO la URL
    sys.stdout = sys.__stdout__
    
    if 'result' in response and 'url' in response['result']:
        print(response['result']['url'])
    else:
        sys.exit(1)
        
except:
    sys.exit(1)
