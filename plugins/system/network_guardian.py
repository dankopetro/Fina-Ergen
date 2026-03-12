
import subprocess
import json
import socket
import sys
import re

def get_local_ip():
    """Detecta la IP local de forma robusta para definir la subred de escaneo."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        # Evitamos devolver el loopback si queremos escanear la red real
        if ip and not ip.startswith("127."):
            return ip
    except:
        pass
    return None

def scan_network():
    local_ip = get_local_ip()
    if not local_ip:
        return {"status": "error", "message": "No se detectó una red activa."}

    parts = local_ip.split('.')
    subnet = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
    
    print(f"Buscando intrusos en {subnet}...")
    
    try:
        # -sn (Ping scan - disable port scan)
        # -T4 (Aggressive timing)
        result = subprocess.run(["nmap", "-sn", subnet], capture_output=True, text=True, timeout=30)
        
        # Parse nmap output
        # Example: "Nmap scan report for X.X.X.X"
        hosts = re.findall(r"Nmap scan report for ([\d\.]+)", result.stdout)
        
        # Also find MAC addresses if available (requires sudo usually, but let's try)
        # "MAC Address: 00:00:00:00:00:00 (Vendor)"
        # macs = re.findall(r"MAC Address: ([\w:]+)", result.stdout)
        
        return {
            "status": "success",
            "subnet": subnet,
            "hosts_found": len(hosts),
            "ips": hosts
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        res = scan_network()
        print(json.dumps(res))
    else:
        print("Uso: python3 network_guardian.py scan")
