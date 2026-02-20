#!/usr/bin/env python3
import time
import sys
import os
import subprocess
import threading
from scapy.all import *

# ================= CONFIGURACIÓN =================
DOORBELL_IP = "192.168.0.5"   # IP del Timbre Tuya
GATEWAY_IP  = "192.168.0.1"   # IP del Router
INTERFACE   = "enp1s0"        # Interfaz de Red

PACKET_THRESHOLD = 3          # HIPER SENSIBLE
TIME_WINDOW      = 3.0        
COOLDOWN         = 10.0       

# RUTA AL MONITOR (Ajustada a tu entorno de pruebas)
MONITOR_SCRIPT = "./plugins/doorbell/monitor.py"
# =================================================

class TuyaSentinel:
# ... (rest of class)

    def packet_callback(self, packet):
        if not self.running: return
        if IP in packet and packet[IP].src == DOORBELL_IP:
            size = len(packet)
            print(f"   📡 Paquete recibido: {size} bytes") # DEBUG VISUAL
            
            now = time.time()
            self.packet_list = [t for t in self.packet_list if now - t < TIME_WINDOW]
            self.packet_list.append(now)
            
            if len(self.packet_list) >= PACKET_THRESHOLD:
                self.trigger_action()
                self.packet_list = [] 

    def start(self):
        os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
        self.log(f"Iniciando Test de Vigilancia sobre {DOORBELL_IP}...")

        while not self.target_mac:
            self.target_mac = self.get_mac(DOORBELL_IP)
            if not self.target_mac:
                self.log("Timbre dormido... Esperando...")
                time.sleep(2)
        
        self.gateway_mac = self.get_mac(GATEWAY_IP)
        self.log("Objetivo Adquirido. 🎯")

        t_spoof = threading.Thread(target=self.spoof_worker, daemon=True)
        t_spoof.start()

        self.log("⚡ VIGILANCIA ACTIVA. VE A TOCAR EL TIMBRE. 🏃‍♂️🔔")
        sniff(filter=f"ip src {DOORBELL_IP}", prn=self.packet_callback, store=0, iface=INTERFACE)

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("⚠️ Necesito sudo.")
        sys.exit(1)
        
    sentinel = TuyaSentinel()
    try:
        sentinel.start()
    except KeyboardInterrupt:
        sentinel.running = False
