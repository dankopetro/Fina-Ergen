import xml.etree.ElementTree as ET
import subprocess
import re
import time
import json
import sys
import os

def get_node_center(bounds_str):
    if not bounds_str: return None
    nums = re.findall(r'\d+', bounds_str)
    if len(nums) == 4:
        x1, y1, x2, y2 = map(int, nums)
        return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def find_ui_element(target, resource_id=None, text=None, content_desc=None):
    # Dump current screen
    dump_cmd = f"adb -s {target} shell uiautomator dump /sdcard/view_dump.xml"
    subprocess.run(dump_cmd, shell=True, capture_output=True)
    
    cat_cmd = f"adb -s {target} shell cat /sdcard/view_dump.xml"
    xml_data = subprocess.run(cat_cmd, shell=True, capture_output=True, text=True).stdout
    
    if not xml_data or "<?xml" not in xml_data:
        print("Error: No se pudo obtener el dump de la UI")
        return None
    
    try:
        root = ET.fromstring(xml_data)
        for node in root.iter('node'):
            node_id = node.get('resource-id', '')
            node_text = node.get('text', '')
            node_desc = node.get('content-desc', '')
            
            match = False
            if resource_id and resource_id in node_id: match = True
            if text and text.lower() in node_text.lower(): match = True
            if content_desc and content_desc.lower() in node_desc.lower(): match = True
            
            if match:
                center = get_node_center(node.get('bounds'))
                if center:
                    return {"x": center[0], "y": center[1], "id": node_id, "text": node_text}
    except Exception as e:
        print(f"Error parsing XML: {e}")
    
    return None

def sandbox_v2(ip, number, message):
    target = f"{ip}:5555"
    if ":" in ip: target = ip
    
    print(f"=== SMS HUB SANDBOX V2 (Target: {target}) ===")
    
    # Intentar limpiar la App primero
    subprocess.run(f"adb -s {target} shell am force-stop com.google.android.apps.messaging", shell=True)
    time.sleep(1)

    # 1. Abrir actividad de composición
    print(f"Lanzando Google Messages para {number}...")
    # Intent más directo
    cmd = f'adb -s {target} shell am start -a android.intent.action.SENDTO -d "sms:{number}" --es sms_body "{message}"'
    subprocess.run(cmd, shell=True)
    
    time.sleep(4) # Tiempo para que cargue la burbuja de texto

    # 2. Buscar el botón de enviar por "Resource ID" (Código interno)
    print("Buscando botón de envío (com.google.android.apps.messaging:id/send_message_button1)...")
    send_btn = find_ui_element(target, resource_id="send_message_button")
    
    if not send_btn:
        print("Buscando por descripción 'Enviar'...")
        send_btn = find_ui_element(target, content_desc="Enviar")
        
    if not send_btn:
        print("Buscando por descripción 'Send'...")
        send_btn = find_ui_element(target, content_desc="Send")

    if send_btn:
        print(f"¡Botón detectado quirúrgicamente! Coordenadas: {send_btn['x']},{send_btn['y']}")
        print(f"ID Interno: {send_btn['id']}")
        # Hacer el clic en las coordenadas exactas obtenidas del sistema
        subprocess.run(f"adb -s {target} shell input tap {send_btn['x']} {send_btn['y']}", shell=True)
        print(">>> COMANDO ENVIADO <<<")
        return True
    else:
        print("CRÍTICO: No se encontró el botón de enviar en la jerarquía de la App.")
        return False

if __name__ == "__main__":
    ip = "192.168.0.6"
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    
    sandbox_v2(ip, "2213999606", "Hola desde el nuevo SMS_HUB con ID Internos")
