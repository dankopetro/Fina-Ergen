#!/usr/bin/env python3
import subprocess
import json
import re
import socket
import threading
from concurrent.futures import ThreadPoolExecutor

# Common IoT Vendors for identification
MAC_VENDORS = {
    # --- Networking / Infra ---
    "B0:92:4A": "TPLink",
    "F4:F2:6D": "TPLink",
    "18:D6:C7": "TPLink",
    "C0:C9:E3": "D-Link",
    "00:18:E7": "Cameo (D-Link)",
    "B0:C5:54": "D-Link",
    "F0:9F:C2": "Ubiquiti",
    "74:83:C2": "Ubiquiti",
    "18:E8:29": "Ubiquiti",
    "00:1D:AA": "Cisco Linksys",
    "E4:A4:71": "Intel Corporate",
    "00:D8:61": "Realtek (PC/Generic)",

    # --- Smart TV / Media ---
    "34:51:80": "TCL Smart TV",
    "D8:71:57": "TCL",
    "BC:2D:98": "TCL",
    "F0:23:B9": "LG TV/Audio",
    "A8:23:FE": "LG TV",
    "70:2A:D5": "Sony TV",
    "F0:BF:97": "Sony",
    "FC:F1:36": "Samsung Smart TV",
    "8C:77:12": "Samsung Electronics",
    "00:12:FB": "Samsung Electronics",
    "18:8E:D5": "Philips TV (TP Vision)",
    "C4:9D:ED": "Philips TV",
    "34:29:12": "Hisense",
    "C8:3A:6B": "Skyworth (Noblex/General)",
    "10:AE:60": "Google Chromecast",
    "D0:E0:55": "Google Nest Mini",
    "D8:31:34": "Roku",
    "F0:D2:F1": "Amazon Fire TV",

    # --- Climatización (Aires/Calefacción) ---
    "AC:C3:F2": "Midea (Aire Acond)",
    "38:D2:CA": "Midea AC",
    "F4:91:1E": "Gree Smart AC",
    "50:2C:C6": "Gree AC",
    "00:23:4E": "Daikin AC",
    "D8:9C:67": "Daikin",
    "34:EA:34": "Broadlink IR Blaster",
    "B4:43:0D": "Broadlink",

    # --- Cámaras de Seguridad (CCTV) ---
    "10:12:FB": "Hikvision",
    "44:32:C8": "Hikvision",
    "A4:14:37": "Hikvision",
    "38:AF:D7": "Dahua Technology",
    "BC:32:5E": "Dahua Technology",
    "90:02:A9": "Dahua",
    "00:62:6E": "Foscam",
    "2C:AA:8E": "Wyze Cam",
    "EC:71:DB": "Reolink",
    "9C:8E:CD": "Ezviz",

    # --- Hogar & IoT (Robots, Heladeras, Cerraduras) ---
    "50:14:79": "iRobot Roomba",
    "F0:B4:79": "iRobot Roomba",
    "40:4D:28": "Roborock (Xiaomi)",
    "00:E5:25": "Ecovacs Deebot",
    "50:11:F2": "Ecovacs",
    "D8:29:10": "August Smart Lock",
    "58:9C:FC": "Nuki Smart Lock",
    "E8:7D:66": "Samsung Smart Appliance (Heladera)",
    "20:3C:AE": "LG Smart Appliance",
    "34:94:54": "Shelly Relay",
    
    # --- IoT Genérico / Chips WiFi ---
    "64:BB:1E": "Philips Hue Bridge",
    "00:17:88": "Philips Hue",
    "EC:B5:FA": "Xiaomi / Yeelight",
    "50:EC:50": "Xiaomi",
    "A0:46:5A": "Espressif (Sonoff/Generic)",
    "24:6F:28": "Espressif (Tuya/SmartLife)",
    "84:F3:EB": "Espressif (NodeMCU)",
    "DC:4F:22": "Espressif",
    "B0:C0:90": "Tuya Smart",
    "B8:27:EB": "Raspberry Pi",
    "DC:A6:32": "Raspberry Pi",

    # --- Celulares / Tablets ---
    "A4:D1:8C": "Apple Device",
    "DC:2B:2A": "Apple Device",
    "24:F5:AA": "Samsung Galaxy",
    "00:16:32": "Samsung Mobile",
    "F4:F5:24": "Motorola Mobile",
    "E0:76:D0": "Motorola",
}

def get_local_ip():
    # Intento 1: Socket UDP (Muy rápido)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        pass
    
    # Intento 2: Comando ip (Linux estándar)
    try:
        res = subprocess.run(["ip", "route", "get", "1"], capture_output=True, text=True)
        # Formato: 1.0.0.0 via 192.168.0.1 dev wlan0 src 192.168.0.100 uid 1000
        match = re.search(r"src\s+([\d\.]+)", res.stdout)
        if match:
            return match.group(1)
    except:
        pass
        
    return "192.168.0.100"

def get_subnet(ip):
    # Assumes /24
    return ".".join(ip.split(".")[:3])

def ping_host(ip):
    try:
        # Fast ping: -c 1 count, -W 1 timeout (1 second is reliable enough)
        res = subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ip if res.returncode == 0 else None
    except:
        return None

def get_arp_table():
    devices = {}
    try:
        # Use ip neigh for Linux as it's more modern and parseable
        res = subprocess.run(["ip", "neigh"], capture_output=True, text=True)
        lines = res.stdout.splitlines()
        for line in lines:
            parts = line.split()
            # Example: 192.168.0.100 dev wlan0 lladdr aa:bb:cc:dd:ee:ff REACTABLE
            
            if len(parts) >= 5:
                ip = parts[0]
                state = parts[-1]
                
                # Check for MAC in standard position (after lladdr)
                mac = ""
                if "lladdr" in parts:
                    try:
                        mac_idx = parts.index("lladdr") + 1
                        mac = parts[mac_idx].upper()
                    except: pass
                
                # Filter useful entries
                if state not in ["FAILED", "INCOMPLETE"] and mac:
                    devices[ip] = mac
    except Exception as e:
        pass
    return devices

def resolve_vendor(mac):
    prefix = mac[:8].replace(":", "")
    # Simple check against our small dict
    for k, v in MAC_VENDORS.items():
        if mac.startswith(k):
            return v
    return "Desconocido"

def scan_network():
    local_ip = get_local_ip()
    subnet = get_subnet(local_ip)
    
    # 1. Ping Sweep to populate ARP cache
    # We scan .1 to .254
    active_ips = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(ping_host, f"{subnet}.{i}"): i for i in range(1, 255)}
        for future in futures:
            res = future.result()
            if res:
                active_ips.append(res)
    
    # 2. Get ARP table (MACs)
    arp_table = get_arp_table()
    
    # 3. Build Result
    results = []
    for ip in active_ips:
        mac = arp_table.get(ip, "")
        vendor = resolve_vendor(mac) if mac else ""
        
        # Try hostname (slow, maybe skip or optimize?)
        hostname = ""
        try:
            # Short timeout for hostname
            hostname = socket.gethostbyaddr(ip)[0]
        except:
            hostname = "?"

        device = {
            "ip": ip,
            "mac": mac,
            "vendor": vendor,
            "hostname": hostname,
            "type": "unknown" # Default, frontend fills this from settings
        }
        results.append(device)
        
    return results

if __name__ == "__main__":
    devices = scan_network()
    print(json.dumps(devices, indent=2))
