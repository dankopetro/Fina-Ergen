#!/bin/bash
# Script para reiniciar Waydroid con audio PulseAudio configurado

echo "🔄 Reiniciando sistema Waydroid con audio PulseAudio..."
echo "=================================================="

# 1. Detener todo
echo ""
echo "1️⃣ Deteniendo procesos..."
pkill -f doorbell_monitor.py
waydroid session stop 2>/dev/null
pkill weston
sleep 2

# 2. Configurar Waydroid para usar PulseAudio
echo ""
echo "2️⃣ Configurando audio de Waydroid..."
waydroid prop set persist.waydroid.audio_backend pulseaudio
echo "✅ Backend de audio configurado: pulseaudio"

# 3. Reiniciar Weston
echo ""
echo "3️⃣ Iniciando Weston..."
unset WAYLAND_DISPLAY
DISPLAY=:0 weston --width=480 --height=822 --idle-time=0 &
WESTON_PID=$!
sleep 3

# 4. Iniciar Waydroid
echo ""
echo "4️⃣ Iniciando Waydroid..."
export WAYLAND_DISPLAY=wayland-1
waydroid show-full-ui &
sleep 8

# 5. Conectar ADB
echo ""
echo "5️⃣ Conectando ADB..."
adb connect 192.168.240.112:5555
sleep 2
adb devices

echo ""
echo "✅ SISTEMA REINICIADO"
echo ""
echo "📝 Ahora prueba de nuevo:"
echo "   1. Abre la grabadora en Waydroid"
echo "   2. Ejecuta: python3 scripts/test_direct_monitor.py"
