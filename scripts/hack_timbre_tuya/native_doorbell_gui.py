#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox
import tinytuya
import subprocess
import threading
import time
import os

# ================= CONFIGURACIÓN =================
ACCESS_ID = "ce4xk53qg5kgph5fsfux"
ACCESS_SECRET = "059755cbce2b444cb23c7e9f8cd241b7"
REGION = "us"
DEVICE_ID = "eba60f4e71e9782575wdkh"
# =================================================

class DoorbellNativeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🔔 Fina Doorbell (Native)")
        self.root.geometry("400x300")
        self.root.configure(bg="#222")
        self.root.attributes('-topmost', True) # Siempre visible

        # Estado variables
        self.video_process = None
        self.video_url = None
        self.is_talking = False

        # --- UI ELEMENTS ---
        
        # Header
        self.lbl_status = tk.Label(root, text="Esperando Timbre...", font=("Arial", 14), bg="#222", fg="#AAA")
        self.lbl_status.pack(pady=20)

        # Botón Atender
        self.btn_answer = tk.Button(root, text="📞 ATENDER", command=self.atender, 
                                    bg="#008800", fg="white", font=("Arial", 12, "bold"), width=30, height=2)
        self.btn_answer.pack(pady=10)

        # Botón Hablar (PTT)
        self.btn_talk = tk.Button(root, text="🎤 HABLAR (Mantener)", 
                                  bg="#444", fg="#888", font=("Arial", 12), width=30, height=2, state=tk.DISABLED)
        # Eventos para "Mantener pulsado"
        self.btn_talk.bind('<ButtonPress-1>', self.start_talk)
        self.btn_talk.bind('<ButtonRelease-1>', self.stop_talk)
        self.btn_talk.pack(pady=10)

        # Botón Cortar
        self.btn_hangup = tk.Button(root, text="❌ CORTAR", command=self.cortar, 
                                    bg="#880000", fg="white", font=("Arial", 12, "bold"), width=30, height=2, state=tk.DISABLED)
        self.btn_hangup.pack(pady=10)

        # Inicializar Cliente Cloud (Hilos para no congelar interfaz)
        threading.Thread(target=self.init_cloud, daemon=True).start()

    def init_cloud(self):
        self.lbl_status.config(text="Conectando Nube...")
        try:
            self.cloud = tinytuya.Cloud(
                apiRegion=REGION, 
                apiKey=ACCESS_ID, 
                apiSecret=ACCESS_SECRET, 
                apiDeviceID=DEVICE_ID
            )
            self.lbl_status.config(text="🟢 Lista para Timbre")
        except Exception as e:
            self.lbl_status.config(text="❌ Error Cloud")
            print(e)

    def fetch_url(self):
        self.lbl_status.config(text="⏳ Obteniendo URL de Video...")
        payload = {"type": "hls"} # HLS es más estable para ver
        try:
            response = self.cloud.cloudrequest(
                f"/v1.0/devices/{DEVICE_ID}/stream/actions/allocate",
                action="POST",
                post=payload
            )
            if response and 'success' in response and response['success']:
                return response['result']['url']
            else:
                print("API Error:", response)
                return None
        except Exception as e:
            print("Fetch Error:", e)
            return None

    def atender(self):
        if self.video_process: return # Ya atendido
        
        self.btn_answer.config(state=tk.DISABLED, bg="#444")
        
        def _connect():
            url = self.fetch_url()
            if url:
                self.video_url = url
                self.root.after(0, self.launch_player)
            else:
                self.root.after(0, lambda: self.lbl_status.config(text="❌ Falló Video"))
                self.root.after(0, lambda: self.btn_answer.config(state=tk.NORMAL, bg="#008800"))

        threading.Thread(target=_connect, daemon=True).start()

    def launch_player(self):
        self.lbl_status.config(text="🎥 Cargando Video... (Tocá el Timbre si no arranca)")
        self.btn_hangup.config(state=tk.NORMAL)
        self.btn_talk.config(state=tk.NORMAL, bg="#0055AA", fg="white")
        
        # Agregamos flags de reintento para aguantar los 404 iniciales
        # --loop-file=inf hace que MPV reintente si se corta o no encuentra
        # --stream-buffer-size asegura fluidez
        cmd = [
            "mpv", 
            "--title=FinaVideo", 
            "--geometry=500x500+450+100", 
            "--loop-file=inf", 
            "--force-window=immediate",
            self.video_url
        ]
        
        try:
            self.video_process = subprocess.Popen(cmd)
        except FileNotFoundError:
            # Fallback a VLC si no hay MPV
            cmd = ["vlc", "--loop", "--width", "500", "--height", "500", self.video_url]
            try:
                self.video_process = subprocess.Popen(cmd)
            except:
                messagebox.showerror("Error", "No se encontró 'mpv' ni 'vlc' instalado.")
                self.cortar()

    def start_talk(self, event):
        if self.btn_talk['state'] == tk.DISABLED: return
        self.is_talking = True
        self.btn_talk.config(bg="#DD0000", text="🎙️ TRANSMITIENDO...")
        self.lbl_status.config(text="🔊 Enviando Audio (Simulado)...")
        # Aquí iría la lógica de subir audio
        
    def stop_talk(self, event):
        if not self.is_talking: return
        self.is_talking = False
        self.btn_talk.config(bg="#0055AA", text="🎤 HABLAR (Mantener)")
        self.lbl_status.config(text="🎥 Video En Vivo")

    def cortar(self):
        # Matar video
        if self.video_process:
            self.video_process.terminate()
            self.video_process = None
        
        # Reset UI
        self.lbl_status.config(text="📴 Llamada Finalizada")
        self.btn_answer.config(state=tk.NORMAL, bg="#008800")
        self.btn_hangup.config(state=tk.DISABLED)
        self.btn_talk.config(state=tk.DISABLED, bg="#444", text="🎤 HABLAR (Mantener)")
        self.video_url = None

if __name__ == "__main__":
    if os.geteuid() == 0:
        print("⚠️ No uses ROOT para GUI si es posible.")
        
    root = tk.Tk()
    app = DoorbellNativeApp(root)
    root.mainloop()
