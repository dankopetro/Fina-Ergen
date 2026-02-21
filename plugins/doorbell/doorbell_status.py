import tinytuya
import json
import sys
import os

def get_battery():
    # PRIORIDAD: Ruta Universal (~/.config/Fina/tuya_config.json)
    universal_path = os.path.expanduser("~/.config/Fina/tuya_config.json")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_path = os.path.join(script_dir, "../../config/tuya_config.json")
    
    config_path = ""
    if os.path.exists(universal_path):
        config_path = universal_path
    elif os.path.exists(project_path):
        config_path = project_path
    else:
        return "N/A"
        
    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        c = tinytuya.Cloud(
            apiRegion=config['region_code'],
            apiKey=config['access_id'],
            apiSecret=config['access_secret'],
            uid=config['uid']
        )

        status = c.getstatus(config['device_id'])
        if status.get('success'):
            for dp in status.get('result', []):
                if dp.get('code') == 'wireless_electricity':
                    return str(dp.get('value'))
        return "N/A"
    except:
        return "N/A"

if __name__ == "__main__":
    print(get_battery())
