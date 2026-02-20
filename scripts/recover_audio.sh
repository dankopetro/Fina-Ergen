#!/bin/bash
# Script de RECUPERACIÓN DE AUDIO
# Borra configuraciones personalizadas y reinicia Waydroid limpio

echo "🚑 INICIANDO PROTOCOLO DE RECUPERACIÓN..."
echo "=========================================="

# 1. Matar todo
echo "1️⃣ Deteniendo procesos..."
pkill -f doorbell_monitor.py
waydroid session stop 2>/dev/null
pkill weston
pkill scrcpy
pkill adb

# 2. Limpiar configuraciones de audio en Waydroid
echo "2️⃣ Limpiando props de Waydroid..."
# Revertir backend a default (o lo que sea stable)
# A veces es mejor dejarlo en 'pulseaudio' si native no va, pero intentemos borrar la prop para reset factory
waydroid prop set persist.waydroid.audio_backend "" 
sudo waydroid shell setprop pulse.server ""

# 3. Descargar módulos residuales en el Host
echo "3️⃣ Limpiando PipeWire/Pulse HOST..."
pactl unload-module module-native-protocol-tcp 2>/dev/null
pactl unload-module module-loopback 2>/dev/null
pkill pacat 2>/dev/null

# 4. Iniciar todo limpio
echo "4️⃣ Reiniciando Weston + Waydroid..."
unset WAYLAND_DISPLAY
DISPLAY=:0 weston --width=480 --height=822 --idle-time=0 &
WESTON_PID=$!
sleep 5

export WAYLAND_DISPLAY=wayland-1
waydroid show-full-ui &

echo "⏳ Esperando arranque..."
sleep 15

# 5. Conectar ADB
adb connect 192.168.240.112:5555
sleep 2

echo "✅ SISTEMA RESTAURADO"
echo "👉 Ahora prueba grabar con tu voz en Waydroid para confirmar que el mic físico volvió."
