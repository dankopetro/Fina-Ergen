# 0. Limpieza previa (Evitar carteles superpuestos)
pkill kdocker
sleep 0.5

# Esperar a que Weston aparezca (Max 15 seg)
echo "🔎 Buscando ventana de Weston..."
MAX_ATTEMPTS=15
WID=""

for i in $(seq 1 $MAX_ATTEMPTS); do
    # USAR AWK!
    WID=$(wmctrl -l | grep -iE 'Weston|weston' | tail -1 | awk '{print $1}')
    
    if [ ! -z "$WID" ]; then
        echo "✅ Weston encontrado: $WID"
        break
    fi
    sleep 1
done

if [ -z "$WID" ]; then
    echo "❌ Timeout: No se encontró Weston."
    exit 1
fi

# 2. Mover al Escritorio 2 (Indice 1)
echo "🚀 Moviendo Weston al Escritorio 2..."

wmctrl -i -r "$WID" -t 1
# Traer al frente en ese escritorio (opcional, pero asegura visibilidad)
wmctrl -i -a "$WID"

echo "✅ Listo. Ventana movida al Escritorio 2."
exit 0
