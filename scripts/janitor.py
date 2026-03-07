#!/usr/bin/env python3
import os
import psutil
import subprocess
import time
import sys

def purge_fina():
    print("🧹 Iniciando Purga Atómica de Fina Ergen...")
    
    # 1. Intentar cierre ordenado de Waydroid primero
    try:
        subprocess.run(["waydroid", "session", "stop"], timeout=5, stderr=subprocess.DEVNULL)
    except: pass

    # 2. Patrones de procesos a eliminar (Más específicos para UI, WebKit y DevServer)
    patterns = [
        "main.py", "fina_api.py", "monitor_ergen.py", 
        "weston", "waydroid", "fina-app", "piper", 
        "doorbell", "tauri", "uvicorn", "scrcpy",
        "node", "vite-dev", "cargo-tauri", "npm",
        "webkitwebprocess", "webkitnetworkprocess", "fina"
    ]
    
    current_pid = os.getpid()

    # Primero matar UI, WebKit y Weston (lo que mantiene la ventana abierta)
    # killall es a veces más efectivo con los procesos de WebKit
    kill_targets = ["fina-app", "weston", "waydroid", "node", "WebKitWebProcess", "WebKitNetworkProcess", "npm", "cargo"]
    for p_name in kill_targets:
         os.system(f"pkill -9 -u $USER -f {p_name} 2>/dev/null")
         os.system(f"killall -9 {p_name} 2>/dev/null")

    # Recorrer todos los procesos del sistema para el resto
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'username']):
        try:
            if proc.info['username'] != psutil.Process().username() or proc.pid == current_pid:
                continue

            cmdline = " ".join(proc.info['cmdline'] or [])
            name = proc.info['name'] or ""
            
            if any(p in cmdline.lower() or p in name.lower() for p in patterns):
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # 3. Limpieza de Puertos (API, UI, Stream)
    for port in [8000, 8555, 5173, 1420]: # 5173/1420 son de Vite/Tauri
        try:
            subprocess.run(["fuser", "-k", f"{port}/tcp"], stderr=subprocess.DEVNULL)
        except: pass

    # 4. LIMPIEZA Y PREPARACIÓN DE ADB (Background total para no bloquear salida)
    print("🧹 Refrescando ADB en segundo plano...")
    try:
        # Lanzamos esto completamente desconectado para que janitor termine INMEDIATAMENTE
        # No esperamos a que ADB responda
        cmd = "nohup sh -c 'adb kill-server; adb start-server; adb connect 192.168.0.10; adb connect 192.168.0.11; adb connect 192.168.0.9' >/dev/null 2>&1 &"
        subprocess.Popen(cmd, shell=True, start_new_session=True)
            
    except Exception as e:
        print(f"⚠️ Error lanzando ADB background: {e}")
        



    # 5. RESET DE TERMINAL AGRESIVO
    print("✨ Restaurando terminal y liberando TTY...")
    os.system("stty sane 2>/dev/null")
    os.system("echo -e '\\033c' 2>/dev/null") # Clear completo de hardware
    os.system("reset 2>/dev/null")

    print("\n✅ Purga completa. ADB listo y terminal restaurada.")

if __name__ == "__main__":
    purge_fina()
