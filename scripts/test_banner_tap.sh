#!/bin/bash
echo "🧪 Probando toque en NOTIFICACIÓN SUPERIOR..."
echo "📍 Apuntando a X=510 Y=150"

# Enviar toque a WayDroid (sudo -n para no pedir pass)
sudo -n waydroid shell input tap 490 175

echo "✅ Toque enviado."
