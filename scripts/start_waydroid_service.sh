#!/bin/bash
# Script para iniciar WayDroid en modo SIN CABEZA (Servicio puro)
# Ideal para arranque al inicio del sistema.

echo "👻 Iniciando WayDroid en modo Servicio (Invisible)..."

# Detener sesiones previas de interfaz
killall weston 2>/dev/null

# Iniciar la sesión (esto carga Android en memoria sin ventana)
waydroid session start &

echo "✅ Servicio WayDroid iniciado. Esperando conexión ADB..."

# Esperar un poco y conectar ADB (para scrcpy)
sleep 15
adb connect 192.168.240.112:5555

echo "🔌 Conectado a ADB. Listo para recibir órdenes."
