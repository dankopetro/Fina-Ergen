#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import time
import os
import sys
from scapy.all import *

# ================= CONFIGURACIÓN =================
# Configuración RED (Sentinel)
DOORBELL_IP = "192.168.0.5"
GATEWAY_IP  = "192.168.0.1"
INTERFACE   = "enp1s0"
PACKET_THRESHOLD = 3
TIME_WINDOW = 3.0
# =================================================

class DoorbellFinalApp:
    def __init__(self, root):
        # LIMPIEZA DE LOGS DE ROOT (Para que usuario pueda escribir luego)
        if os.path.exists("/tmp/waydroid_launch.log"):
            try:
                os.remove("/tmp/waydroid_launch.log")
            except:
                pass

        self.root = root
        self.root.title("🔔 Fina Doorbell (Waydroid Edition)")
        self.root.geometry("400x350")
        self.root.configure(bg="#111")
        self.root.attributes('-topmost', True)

        self.sentinel_thread = None
        
        # --- UI ---
        # Indicator Circle
        self.canvas = tk.Canvas(root, width=50, height=50, bg="#111", highlightthickness=0)
        self.status_light = self.canvas.create_oval(10, 10, 40, 40, fill="#333")
        self.canvas.pack(pady=10)

        self.lbl_status = tk.Label(root, text="🛡️ Vigilancia Activa", font=("Arial", 16), bg="#111", fg="#888")
        self.lbl_status.pack(pady=5)
        
        # Flag para evitar rebotes/loops
        self.has_auto_answered = False
        self.packet_list = [] # Buffer de paquetes ARP/UDP
        
        # Botones
        self.btn_manual = tk.Button(root, text="👁️ VER ESCRITORIO (Manual)", command=self.ver_escritorio, 
                                    bg="#0055AA", fg="white", font=("Arial", 11, "bold"), width=30, height=2)
        self.btn_manual.pack(pady=5)

        self.btn_answer = tk.Button(root, text="📞 ATENDER (Waydroid)", command=self.atender, 
                                    bg="#006600", fg="#AAA", font=("Arial", 14, "bold"), width=30, height=2, state=tk.DISABLED)
        self.btn_answer.pack(pady=10)

        self.btn_hangup = tk.Button(root, text="❌ CERRAR / REARMAR", command=self.rearmer, 
                                    bg="#660000", fg="white", font=("Arial", 12), width=20, state=tk.DISABLED)
        self.btn_hangup.pack(pady=5)

        self.btn_kill = tk.Button(root, text="🔥 APAGAR TODO (Enfriar)", command=self.apagar_todo, 
                                    bg="#FF4400", fg="white", font=("Arial", 10, "bold"), width=30)
        self.btn_kill.pack(pady=15)

        # Hilos
        threading.Thread(target=self.start_sentinel, daemon=True).start()
        threading.Thread(target=self.warmup_system, daemon=True).start()

    # --- WARMUP (PRE-CARGA) ---
    def warmup_system(self):
        time.sleep(1) # Esperar a que UI cargue
        self.update_status("🔥 Pre-calentando...", "#FF8800")
        
        # Lanzar en modo escritorio pero el launcher lo minimizará solo
        self.run_waydroid(mode="desktop")
        
        # Esperar un poco y confirmar listo
        time.sleep(15) 
        self.update_status("🛡️ Vigilando Red", "#004400")

    # --- SENTINEL (DETECTOR) ---
    def start_sentinel(self):
        os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
        target_mac = self.get_mac(DOORBELL_IP)
        gateway_mac = self.get_mac(GATEWAY_IP)
        
        if not target_mac:
            self.update_status("💤 Timbre Dormido", "#333")
            while not target_mac:
                target_mac = self.get_mac(DOORBELL_IP)
                time.sleep(2)
        
        self.update_status("🛡️ Vigilando Red", "#004400")
        self.root.after(0, lambda: self.btn_answer.config(state=tk.NORMAL)) # Habilitar manual por si acaso

        def spoof():
            while True:
                sendp(Ether(dst=target_mac)/ARP(op=2, pdst=DOORBELL_IP, hwdst=target_mac, psrc=GATEWAY_IP), verbose=False, iface=INTERFACE)
                sendp(Ether(dst=gateway_mac)/ARP(op=2, pdst=GATEWAY_IP, hwdst=gateway_mac, psrc=DOORBELL_IP), verbose=False, iface=INTERFACE)
                time.sleep(2)
        threading.Thread(target=spoof, daemon=True).start()

        # Usamos atributo de clase para poder limpiarlo externamente

        def pkt_callback(pkt):
            if IP in pkt and pkt[IP].src == DOORBELL_IP:
                if len(pkt[IP].payload) > 100: # Filtrar paquetes pequeños
                     self.packet_list.append(time.time())

        threading.Thread(target=lambda: sniff(filter=f"host {DOORBELL_IP}", prn=pkt_callback, store=0, stop_filter=lambda x: False, started_callback=lambda: print("Sniffer iniciado..."), iface=INTERFACE), daemon=True).start()

        while True:
            current_time = time.time()
            # Limpiar viejos
            self.packet_list = [t for t in self.packet_list if current_time - t < 2]

            # Detección: Si hay más de 50 paquetes grandes en 2 segundos
            if len(self.packet_list) > 30: # Umbral ajustado
                 self.trigger_ring()
                 self.packet_list = [] # Resetear contador
                 time.sleep(5) # Delay anti-rebote inmediato
            
            time.sleep(0.1)

    def get_mac(self, ip):
        conf.verb = 0
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, verbose=False, iface=INTERFACE)
        if ans: return ans[0][1].src
        return None

    # --- ACCIONES ---
    def trigger_ring(self):
        if not self.has_auto_answered:
            self.has_auto_answered = True
            self.root.after(0, lambda: self.alert_ui())
            # AUTO-ATENDER (Traer ventana al frente inmediatamente)
            print("⚡ RING DETECTADO -> Ejecutando Auto-Atender...")
            self.root.after(100, lambda: self.atender())
        else:
            print("Ignoring duplicate ring...")

    def alert_ui(self):
        self.update_status("🔔 ¡TIMBRE SONANDO! 🔔", "#FF0000")
        self.btn_answer.config(bg="#00FF00", fg="black", text="📞 ATENDER AHORA")
        print("\a") # Beep

    def update_status(self, text, color):
        self.lbl_status.config(text=text, fg=color if color != "#333" else "#888")
        self.canvas.itemconfig(self.status_light, fill=color)

    def run_waydroid(self, mode="app"):
        # 0. MANTENIMIENTO PREVENTIVO (Como Root)
        # Verificar que el motor systemd esté corriendo
        try:
            status = subprocess.check_output("systemctl is-active waydroid-container", shell=True).decode().strip()
            if status != "active":
                self.update_status("🔧 Arrancando Motor...", "#FF8800")
                os.system("systemctl restart waydroid-container")
                time.sleep(3) # Tiempo para que levante
        except:
            pass

        # Lanzar Script Waydroid (como usuario)
        launcher_path = os.path.join(os.path.dirname(__file__), "waydroid_launcher.py")
        cmd = ["python3", launcher_path]
        
        if mode == "desktop":
            cmd.append("--desktop")

        # Detectar usuario original (SUDO o PKEXEC)
        real_user = os.environ.get('SUDO_USER')
        if not real_user and 'PKEXEC_UID' in os.environ:
            import pwd
            try:
                real_user = pwd.getpwuid(int(os.environ['PKEXEC_UID'])).pw_name
            except:
                pass

        if os.geteuid() == 0 and real_user:
            # Fix XDG y USER para Waydroid. Asumimos UID 1000 para XDG si no podemos calcularlo dinámicamente,
            # pero mejor usar el UID real del usuario.
            import pwd
            u_uid = pwd.getpwnam(real_user).pw_uid
            
            base_cmd = ["sudo", "-u", real_user, "env", "DISPLAY=:0", f"XDG_RUNTIME_DIR=/run/user/{u_uid}"]
            cmd = base_cmd + cmd
        
        subprocess.Popen(cmd)

    def ver_escritorio(self):
        self.update_status("🖥️ Abriendo Escritorio...", "#0088FF")
        self.run_waydroid(mode="desktop")

    def atender(self):
        self.update_status("📱 ABRIENDO TUYA...", "#0088FF")
        self.btn_answer.config(state=tk.DISABLED)
        self.btn_hangup.config(state=tk.NORMAL, bg="#AA0000")
        self.run_waydroid(mode="app")

    def rearmer(self):
        # 1. Resetear UI INMEDIATAMENTE (Feedback instantáneo)
        self.update_status("🛡️ Vigilando Red", "#004400")
        self.btn_answer.config(state=tk.NORMAL, bg="#006600", fg="#AAA", text="📞 ATENDER (Waydroid)")
        self.btn_hangup.config(state=tk.DISABLED, bg="#660000")
        # El flag se resetea AL FINAL del proceso de fondo para evitar rebotes
        
        # 2. Ejecutar lógica lenta en segundo plano
        threading.Thread(target=self._do_rearm_logic, daemon=True).start()

    def _do_rearm_logic(self):
        # CORTAR LLAMADA (Solo Taps, sin EndCall que apaga pantalla)
        print("🔴 CORTANDO LLAMADA (Tap Botón Rojo)...")
        
        # 1. Botón Rojo (Centro) - Intento 1
        subprocess.run("sudo waydroid shell input tap 335 720", shell=True)
        time.sleep(0.5)
        
        # 2. Botón Rojo (Centro) - Intento 2 (Confirmación)
        subprocess.run("sudo waydroid shell input tap 335 720", shell=True)
        time.sleep(0.5)
        
        # 3. Botón 'Colgar' alternativo (Arriba derecha)
        #subprocess.run("sudo waydroid shell input tap 254 146", shell=True)
        #time.sleep(0.8)
        
        
        # VOLVER AL HOME (Limpieza para la próxima)
        print("🏠 Volviendo al Escritorio Android (KEYCODE_HOME)...")
        # Usamos KEYCODE_HOME (3) que es más robusto que coordenadas
        subprocess.run("sudo waydroid shell input keyevent KEYCODE_HOME", shell=True)
        time.sleep(2.0) # Esperar a ver el escritorio
        
        # MINIMIZAR
        print("📉 Minimizando Waydroid...")
        min_script = os.path.join(os.path.dirname(__file__), "minimizar_weston.sh")
        subprocess.Popen(["bash", min_script])

        # AHORA SÍ: Limpiar buffer y permitir nuevos disparos
        print("🧹 Limpiando buffer de red...")
        self.packet_list = []
        self.has_auto_answered = False
        print("✅ Sistema Rearmado y Listo para el próximo Ring.")

    def apagar_todo(self):
        self.update_status("❄️ APAGANDO MOTORES...", "#FF8800")
        try:
            script_path = os.path.join(os.path.dirname(__file__), "enfriar_pc.sh")
            subprocess.Popen(["bash", script_path])
            self.root.after(2000, lambda: self.update_status("✅ SISTEMA APAGADO", "#333"))
        except Exception as e:
            print(f"Error al apagar: {e}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("⚠️ RELANZANDO COMO ROOT...")
        args = ["sudo", sys.executable] + sys.argv
        os.execlpe("sudo", *args, os.environ)
    else:
        os.system("xhost +SI:localuser:root >/dev/null 2>&1")
        
    root = tk.Tk()
    app = DoorbellFinalApp(root)
    root.mainloop()
