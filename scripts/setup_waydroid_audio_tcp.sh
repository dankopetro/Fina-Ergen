#!/bin/bash
# Script avanzado de configuración de Audio Waydroid -> Host PipeWire
# Este script habilita la comunicación TCP de PulseAudio y configura Waydroid para usarla

echo "🎛️ CONFIGURACIÓN AVANZADA DE AUDIO WAYDROID (TCP)"
echo "------------------------------------------------"

# 1. Cargar módulo TCP en PipeWire/PulseAudio del host
# Permitimos conexiones desde la subred de Waydroid (192.168.240.0/24)
echo "1️⃣ Habilitando protocolo TCP en el Host..."
if pactl list modules | grep -q "module-native-protocol-tcp"; then
    echo "   ✅ El módulo TCP ya está cargado."
else
    # IP del host en la red waydroid suele ser 192.168.240.1
    pactl load-module module-native-protocol-tcp port=4713 "auth-ip-acl=127.0.0.1;192.168.240.0/24"
    echo "   ✅ Módulo TCP cargado en puerto 4713."
fi

# 2. Configurar Waydroid para usar PulseAudio a través de TCP
echo ""
echo "2️⃣ Configurando propiedades de Waydroid..."

# Establecer backend a pulseaudio (por si acaso)
waydroid prop set persist.waydroid.audio_backend pulseaudio

# Dentro de Android, apuntar al servidor PulseAudio del host
# La IP del host vista desde Waydroid es 192.168.240.1
echo "   Configurando pulse.server = 192.168.240.1:4713..."
sudo waydroid shell setprop pulse.server 192.168.240.1:4713

# 3. Reiniciar el servicio de audio de Android (mediaserver)
echo ""
echo "3️⃣ Reiniciando servidor de audio de Android..."
sudo waydroid shell setprop ctl.restart audioserver
sleep 2

# 4. Verificar
echo ""
echo "4️⃣ Verificación:"
echo "   Si todo salió bien, ahora Waydroid debería aparecer en 'pactl list clients' del host."
echo "   Intentando listar clientes de Waydroid..."
pactl list clients | grep -i "waydroid" || echo "⚠️ Aún no veo clientes de Waydroid (puede que aparezcan al usar audio)."

echo ""
echo "✅ Configuración aplicada."
echo "   Ahora intenta grabar en Waydroid. Debería usar la fuente predeterminada del Host."
