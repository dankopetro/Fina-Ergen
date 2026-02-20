#!/bin/bash
# Script de Simulacro de Arranque del Sistema Fina (Backend)
# Objetivo: Validar la cadena completa WayDroid -> ADB -> Monitor

echo "🚀 Iniciando Simulacro de Arranque..."

# 1. Limpieza preventiva
killall weston waydroid scrcpy python3 2>/dev/null
pkill -f doorbell_monitor.py

# 2. Iniciar Weston (Base Gráfica)
echo "🖥️  Lanzando Weston (Minimizalo cuando aparezca)..."
# Usamos tamaño 'phone' para que no ocupe tanto
weston --width=600 --height=820 --idle-time=0 &
WESTON_PID=$!

echo "⏳ Esperando 10s para carga de WayDroid..."
sleep 10

# 3. Lanzar Sesión WayDroid
export WAYLAND_DISPLAY=wayland-1
waydroid session start &

# 4. Bucle de Conexión ADB (Espera hasta que conecte)
echo "🔌 Buscando conexión ADB..."
for i in {1..20}; do
    adb connect 192.168.240.112:5555 > /dev/null 2>&1
    STATUS=$(adb devices | grep "device$" | grep "192.168")
    
    if [ ! -z "$STATUS" ]; then
        echo "✅ ADB Conectado Exitosamente!"
        break
    fi
    echo "   ... intento $i/20, esperando..."
    sleep 2
done

# Verificación final
if [ -z "$STATUS" ]; then
    echo "❌ ERROR CRÍTICO: No se pudo conectar ADB. Abortando."
    exit 1
fi

# 5. Lanzar Vigilante (Monitor de Timbre)
echo "🕵️ Iniciando Vigilante Conserje..."
nohup python3 scripts/doorbell_monitor.py > doorbell_monitor.log 2>&1 &

echo "=================================================="
echo "✅✅ SISTEMA OPERATIVO Y LISTO"
echo "🔔 POR FAVOR, TOCA EL TIMBRE AHORA."
echo "   (Debería abrirse ventana flotante y saludar)"
echo "=================================================="
