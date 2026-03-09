#!/bin/bash

IP=$1

if [ -z "$IP" ]; then
  echo "Uso: prevent_tv_sleep.sh [IP]"
  exit 1
fi

echo "--- OPTIMIZANDO SUEÑO PROFUNDO EN $IP ---"

# Conectar si no está conectado
adb connect $IP:5555

# 1. Mantener encendido mientras esté enchufado (AC=1, USB=2, Wireless=4. Suma=7)
adb -s $IP:5555 shell settings put global stay_on_while_plugged_in 7

# 2. Desactivar el timeout de pantalla (o ponerlo al máximo)
adb -s $IP:5555 shell settings put system screen_off_timeout 2147483647

# 3. Forzar que no entre en modo Doze agresivo para la app de control remoto
adb -s $IP:5555 shell dumpsys deviceidle whitelist +com.google.android.videos
adb -s $IP:5555 shell dumpsys deviceidle whitelist +com.google.android.tv.remote

# 4. Svc power stayon (Comando directo de hardware)
adb -s $IP:5555 shell svc power stayon true

echo "✅ Órdenes de 'Desvelo' enviadas. La TV debería ser más estable ahora."
