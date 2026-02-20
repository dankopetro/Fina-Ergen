#!/bin/bash
echo "🤖 Iniciando Entorno Android (Weston + WayDroid)..."

# Detener cualquier sesión previa
waydroid session stop

# Iniciar Weston (Ventana de Linux)
echo "🖥️  Lanzando Weston..."
# Iniciar Weston Normal (pero lo ocultaremos)
weston --width=600 --height=820 --idle-time=0 &
WESTON_PID=$!

echo "⏳ Esperando a que Weston aparezca..."
timeout 10s bash -c 'until xdotool search --onlyvisible --class "weston"; do sleep 0.5; done'

# ¡MAGIA! Mover ventana al exilio (Fuera de pantalla)
echo "🪄 Ocultando ventana de Weston..."
xdotool search --class "weston" windowmove 10000 10000
sleep 5

# Exportar variables necesarias para que WayDroid encuentre Weston
export WAYLAND_DISPLAY=wayland-1
export XDG_SESSION_TYPE=wayland

# Iniciar la sesión de WayDroid (el cerebro)
echo "🧠 Iniciando Sesión WayDroid..."
waydroid session start &

echo "⏳ Esperando 10s a que arranque el sistema..."
sleep 10

# Mostrar la interfaz (lo que ves)
echo "📱 Mostrando Interfaz Android..."
waydroid show-full-ui

# Si show-full-ui falla, el script sigue.
# Ponemos una pausa para que leas los errores
echo "⚠️  WayDroid UI terminó. Presiona ENTER para cerrar Weston."
read

kill $WESTON_PID
waydroid session stop
