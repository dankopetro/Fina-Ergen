#!/bin/bash
# Script Francotirador de Audio
# Busca streams de Waydroid y los mueve al Micrófono Físico (ID 58)

TARGET_SOURCE=58
WAYDROID_NAME="Waydroid"

echo "🎯 FRANCOTIRADOR DE AUDIO ACTIVO"
echo "👉 Esperando que Waydroid empiece a grabar..."
echo "------------------------------------------------"

while true; do
    # Buscar ID de stream de Waydroid
    # Buscamos la línea que dice "Cliente: XXXX" donde XXXX es el ID de Waydroid
    # Pero pactl es verboso. Usamos una técnica sucia pero rápida.
    
    # Listar todos los source-outputs
    OUTPUT=$(pactl list source-outputs)
    
    if echo "$OUTPUT" | grep -q "Waydroid"; then
        # Extraer el ID del bloque que contiene "Waydroid"
        # Usamos awk para parsear bloques.
        # ID está en la línea "Salida de fuente #ID"
        
        # Manera simplificada: Iterar sobre IDs y chequear si pertenecen a Waydroid
        IDS=$(pactl list short source-outputs | cut -f1)
        
        for ID in $IDS; do
            # Verificar si este ID es de Waydroid
            INFO=$(pactl list source-outputs | grep -A 20 "Salida de fuente #$ID")
            if echo "$INFO" | grep -q "Waydroid"; then
                CURRENT_SOURCE=$(echo "$INFO" | grep "Fuente:" | cut -d: -f2 | xargs)
                
                if [ "$CURRENT_SOURCE" != "$TARGET_SOURCE" ]; then
                    echo "🔥 DETECTADO Stream #$ID conectado a Fuente #$CURRENT_SOURCE"
                    echo "⚡ MOVIENDO a Fuente #$TARGET_SOURCE (Micrófono)..."
                    pactl move-source-output $ID $TARGET_SOURCE
                    if [ $? -eq 0 ]; then
                        echo "✅ ¡MOVIDO CON ÉXITO!"
                        echo "🎤 ¡HABLA AHORA!"
                        
                        # Reproducir sonido de confirmación en el host
                        paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null &
                        
                        exit 0
                    else
                        echo "❌ Falló el movimiento."
                    fi
                fi
            fi
        done
    fi
    sleep 0.5
done
