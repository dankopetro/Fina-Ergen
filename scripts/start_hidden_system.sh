#!/bin/bash
# Script para iniciar el sistema Fina con Weston oculto
echo "🚀 Iniciando Sistema Fina (Modo Invisible)..."

# 1. Limpieza (Pero NO matamos al monitor)
echo "🧹 Limpiando sesiones previas..."
waydroid session stop 2>/dev/null
pkill -9 -f waydroid
pkill -9 -f weston
pkill -9 -f scrcpy
# Limpiar sockets
rm -rf /run/user/$(id -u)/waydroid* 2>/dev/null
rm -rf /tmp/waydroid.lock 2>/dev/null

echo "⏳ Esperando 5s..."
sleep 5

# 2. Iniciar Weston y ocultarlo
echo "🖥️  Lanzando Weston..."
unset WAYLAND_DISPLAY
export DISPLAY=:0

# Buscar weston.ini robustamente
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WESTON_CONFIG="./weston.ini"
if [ ! -f "$WESTON_CONFIG" ]; then
    WESTON_CONFIG="$SCRIPT_DIR/../weston.ini"
fi
if [ ! -f "$WESTON_CONFIG" ]; then
    WESTON_CONFIG="$SCRIPT_DIR/weston.ini"
fi

echo "📝 Usando config: $WESTON_CONFIG"
# Iniciar Weston con config para evitar bloqueo usando ruta absoluta
weston --config="$WESTON_CONFIG" --width=450 --height=820 &
WESTON_PID=$!

echo "⏳ Esperando a que Weston aparezca..."
timeout 15s bash -c 'until xdotool search --onlyvisible --class "weston"; do sleep 0.5; done'

echo "🪄 Dockerizando Weston al Tray..."
# Esperamos a que la ventana exista realmente
timeout 20s bash -c 'until xdotool search --class "weston"; do sleep 0.5; done'
sleep 3

# Capturar ID
WID=$(xdotool search --class "weston" | head -n 1)

if [ -n "$WID" ]; then
    echo "🪄 Dockerizando Weston ID: $WID"
    kdocker -w "$WID" -q -i /usr/share/icons/breeze-dark/status/32/rotation-locked-portrait.svg &
else
    echo "⚠️ No se encontró Weston para dockerizar. Se queda visible."
fi

# 3. Iniciar WayDroid
export WAYLAND_DISPLAY=wayland-1
echo "🧠 Iniciando Interfaz Gráfica WayDroid (Background)..."
waydroid show-full-ui &

echo "⏳ Esperando 15s para carga de sistema..."
sleep 15

# 4. Conectar ADB
echo "🔌 Conectando ADB..."
timeout 5 adb connect 192.168.240.112:5555
timeout 2 adb devices

echo "✅ INFRAESTRUCTURA GRÁFICA LISTA."
echo "Weston PID: $WESTON_PID"
