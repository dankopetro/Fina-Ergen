#!/bin/bash
#force_kill.sh ahora delega en cleanup.sh para consistencia
echo "🔪 Ejecutando Orden 66 (Vía Cleanup Maestro)..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
bash "$DIR/cleanup.sh"
