#!/usr/bin/env python3
import socket
import binascii

# Configuración
TARGET_IP = "192.168.0.5"
LISTEN_PORTS = [6666, 6667, 3333] # Puertos broadcast típicos de IoT chino

def start_sniffer():
    print(f"👻 MODO FANTASMA ACTIVADO")
    print(f"👂 Escuchando gritos UDP desde {TARGET_IP} en puertos {LISTEN_PORTS}...")
    print("👉 VE A TOCAR EL TIMBRE (No hace falta atender, solo tocar).")
    
    # Crear sockets para cada puerto
    sockets = []
    for port in LISTEN_PORTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(0.1) # No bloquear
            sock.bind(('', port)) # Escuchar en todas las interfaces
            sockets.append((port, sock))
            print(f"   ✅ Escuchando en UDP {port}")
        except Exception as e:
            print(f"   ❌ No se pudo abrir puerto {port}: {e}")

    print("\n------------------------------------------------")
    
    while True:
        for port, sock in sockets:
            try:
                data, addr = sock.recvfrom(4096) # Buffer size
                sender_ip = addr[0]
                
                # ¡FILTRAR SOLO EL OBJETIVO!
                if sender_ip == TARGET_IP:
                    print(f"\n🚨 ¡DETECTADO PAQUETE DE {sender_ip} en puerto {port}!")
                    print(f"📦 Tamaño: {len(data)} bytes")
                    print(f"🔑 Hex: {binascii.hexlify(data).decode('utf-8')[:100]}...") # Mostrar primeros 100 chars
                    print(f"📜 Ascii: {str(data)[:100]}")
                    print("------------------------------------------------")
                    
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    try:
        start_sniffer()
    except KeyboardInterrupt:
        print("\n👻 Sniffer apagado.")
