#!/bin/bash
# Script para crear el Estudio Virtual de Fina
# Crea un Null Sink (Dispositivo Virtual) para enrutamiento limpio

SINK_NAME="FinaVoice"

echo "🎛️ MONTANDO ESTUDIO VIRTUAL..."

# 1. Limpiar versiones previas
pactl unload-module module-null-sink 2>/dev/null
pactl unload-module module-loopback 2>/dev/null

# 2. Crear el Null Sink (La Sala de Grabación)
echo "1️⃣ Creando dispositivo virtual '$SINK_NAME'..."
MODULE_ID=$(pactl load-module module-null-sink sink_name=$SINK_NAME sink_properties=device.description=Fina_Virtual_Mic)

if [ -z "$MODULE_ID" ]; then
    echo "❌ Error creando Null Sink."
    exit 1
fi

echo "   ✅ Sala creada (Module ID: $MODULE_ID)"

# 3. (Opcional) Crear Loopback para que tú lo escuches (Monitor)
# Esto redirige el audio virtual a tus altavoces reales para que sepas cuándo habla
echo "2️⃣ Habilitando monitoreo para humanos..."
REAL_SPEAKERS=$(pactl get-default-sink)
pactl load-module module-loopback source=$SINK_NAME.monitor sink=$REAL_SPEAKERS latency_msec=1

echo "✅ ESTUDIO VIRTUAL LISTO"
echo "   - Salida Virtual: $SINK_NAME"
echo "   - Entrada Virtual: $SINK_NAME.monitor"
echo ""
echo "👉 Ahora Fina puede hablar directamente a '$SINK_NAME' y Waydroid grabará de '$SINK_NAME.monitor'"
