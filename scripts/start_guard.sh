#!/bin/bash

# Ruta al proyecto
cd "$(dirname "$0")/.."

echo "🕵️  Iniciando El Vigilante (Monitor de Timbre)..."

# Matar instancia previa si existe
pkill -f "doorbell_monitor.py"

# Lanzar en background con nohup (inmune a cerrar terminal)
nohup python3 scripts/doorbell_monitor.py > doorbell_monitor.log 2>&1 &

PID=$!
echo "✅ Vigilante activo en segundo plano (PID: $PID)"
echo "📄 Log guardado en: doorbell_monitor.log"
echo ""
echo "💡 Para detenerlo, ejecuta: StopGuard"
echo "   (O usa el comando: pkill -f doorbell_monitor.py)"
