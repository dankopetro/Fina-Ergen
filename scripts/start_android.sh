#!/bin/bash
echo "🤖 Iniciando Entorno Android (Weston + WayDroid)..."

# Iniciar Weston en background
weston --width=600 --height=900 &
WESTON_PID=$!

sleep 3

# Exportar display de Wayland (generalmente wayland-1 dentro de weston)
export WAYLAND_DISPLAY=wayland-1

# Iniciar sesió WayDroid
waydroid session start &

sleep 5

# Mostrar interfaz
waydroid show-full-ui

# Al cerrar, matar todo
kill $WESTON_PID
waydroid session stop
