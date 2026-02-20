#!/bin/bash
# Script para revivir ADB sin reiniciar la PC
# Creado para Fina Ergen

echo "💀 Deteniendo procesos ADB zombis..."
# Matar adb server y cualquier proceso adb colgado
killall -9 adb 2>/dev/null
pkill -9 adb 2>/dev/null

echo "🧊 Limpiando sockets..."
# A veces el socket queda bloqueado en el sistema
sudo fuser -k 5037/tcp 2>/dev/null

echo "🚀 Reiniciando servidor ADB..."
adb start-server

echo "🔌 Re-conectando TVs conocidas..."
# Intentar conectar a las IPs fijas de la casa
adb connect 192.168.0.10:5555
adb connect 192.168.0.11:5555
adb connect 192.168.0.9:5555

echo "✅ ADB revivido. Lista de dispositivos:"
adb devices
