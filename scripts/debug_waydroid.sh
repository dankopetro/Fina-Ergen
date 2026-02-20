#!/bin/bash
# Limpiar previo
echo "🧹 Limpiando procesos previos..."
pkill -9 -f waydroid
pkill -9 -f weston
pkill -9 -f scrcpy
# Limpiar sockets
rm -rf /run/user/$(id -u)/waydroid* 2>/dev/null
rm -rf /tmp/waydroid.lock 2>/dev/null
waydroid session stop 2>/dev/null

echo "⏳ Esperando limpieza (5s)..."
sleep 5

# Lanzar Weston VISIBLE
echo "🖥️ Lanzando Weston VISIBLE..."
unset WAYLAND_DISPLAY
export DISPLAY=:0
weston --width=450 --height=820 --config="./weston.ini" &
sleep 5

# Lanzar Waydroid
export WAYLAND_DISPLAY=wayland-1
echo "🧠 Lanzando Waydroid..."
# Iniciar sesión primero
waydroid session start &
sleep 5
# Mostrar UI
waydroid show-full-ui &

echo "⏳ Esperando 20s para que cargue Android..."
sleep 20

# Conectar ADB
echo "🔌 Conectando ADB..."
adb connect 192.168.240.112:5555
sleep 3

# Listar Tuya
echo "===== RESULTADO ====="
echo "🔍 Buscando paquetes 'tuya':"
adb devices
adb shell pm list packages | grep tuya
echo "====================="

echo "✅ Listo. Puedes cerrar Weston manualmente cuando termines."
