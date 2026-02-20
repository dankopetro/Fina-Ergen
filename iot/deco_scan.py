
import socket
import concurrent.futures

def scan_port(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            result = s.connect_ex((ip, port))
            if result == 0:
                try:
                    service = socket.getservbyport(port)
                except:
                    service = "unknown"
                return port, service
    except:
        pass
    return None

def scan_target(ip):
    print(f"Scanning {ip} for open ports...")
    # Common ports for Android TV / Cast / Remote / ADB / Web
    # 5555: ADB
    # 8008, 8009: Chromecast
    # 6466, 6467: Android TV Remote Service (Google)
    # 8080, 9090, 80, 443: Web/HTTP
    # 9998, 9999: VLC/Kodi/etc
    # 49152+: UPnP
    
    interesting_ports = [
        5555, 
        8008, 8009, 
        6466, 6467, 
        8000, 8080, 9000, 9090, 
        80, 443
    ]
    
    open_ports = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(scan_port, ip, port): port for port in interesting_ports}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                print(f"✅ Open Port: {res[0]} ({res[1]})")
                open_ports.append(res[0])
    
    if not open_ports:
        print("No common ports found open.")
    else:
        print(f"\nAnalysis for {ip}:")
        if 5555 in open_ports:
            print("- ADB is OPEN (but maybe unauth)")
        if 6466 in open_ports or 6467 in open_ports:
            print("- Google Android TV Remote Service detected! (Pairing possible)")
        if 8009 in open_ports:
            print("- Chromecast supported (Can cast URLs)")

if __name__ == "__main__":
    scan_target("192.168.0.9")
