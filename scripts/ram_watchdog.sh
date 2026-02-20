#!/bin/bash
THRESHOLD=95
CHECK_INTERVAL=2

echo "🛡️ RAM Watchdog iniciado (Umbral: $THRESHOLD%)"

while true; do
    # Obtener uso de RAM%
    USAGE=$(free | awk '/Mem/{printf("%d"), $3/$2*100}')
    
    if [ "$USAGE" -ge "$THRESHOLD" ]; then
        echo "🚨 ¡ALERTA! RAM Crítica ($USAGE%). Iniciando apagado de emergencia..."
        # Notificación visual si es posible
        notify-send -u critical "Fina Watchdog" "⚠️ EMERGENCIA: RAM al $USAGE%. Matando procesos." 2>/dev/null
        
        # Ejecutar limpieza nuclear
        bash scripts/cleanup.sh
        
        echo "💀 Sistema Fina abortado por seguridad."
        exit 1
    fi
    sleep $CHECK_INTERVAL
done
