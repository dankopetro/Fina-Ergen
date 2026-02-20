#!/bin/bash

echo "🔥 DETECTADO SOBRECALENTAMIENTO / LIMPIEZA SOLICITADA"
echo "❄️ Iniciando protocolo de enfriamiento..."

# 1. Detener servicios oficialmente (Intento amable)
echo "🛑 Deteniendo servicios de Waydroid..."
waydroid session stop > /dev/null 2>&1
sudo systemctl stop waydroid-container > /dev/null 2>&1

# 2. Asesinato de procesos gráficos (Weston/Wayland)
echo "🔪 Matando entorno gráfico..."
sudo pkill -9 weston
sudo pkill -9 Xwayland

# 3. Asesinato de procesos del contenedor (LXC y Android)
echo "🔪 Matando procesos internos de Android..."
sudo pkill -9 waydroid
sudo pkill -9 lxc-start
sudo pkill -9 lxc-monitor
# Binder y procesos zombies de Android a veces quedan huérfanos
sudo pkill -f "binder"
sudo pkill -f "gbinder"

# 4. Matar nuestros scripts de Python (Sentinel y Launcher)
echo "🐍 Cerrando scripts de vigilancia..."
sudo pkill -f "doorbell_final_app.py"
sudo pkill -f "waydroid_launcher.py"
sudo pkill -f "mem_watchdog.py"
sudo pkill -f "streamer.py"
sudo pkill -f "ffmpeg"
sudo pkill -f "monitor.py"

# Matar puerto de video stream si está bloqueado
sudo fuser -k 8555/tcp 2>/dev/null || true

# 5. Limpieza de memoria compartida y sockets (Opcional pero ayuda)
echo "🧹 Limpiando sockets..."
sudo rm -rf /tmp/waydroid.log
sudo rm -rf /run/user/$(id -u)/wayland-*

echo "✅ SISTEMA LIMPIO."
echo "🌡️ La temperatura debería bajar en unos segundos."
exit 0
