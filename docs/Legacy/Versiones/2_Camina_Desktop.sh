#!/bin/zsh
source ~/.zshrc

# Ir al directorio raíz del proyecto
cd "$(dirname "$0")/.."

# Ejecutar
echo "🖥️  Camina Desktop..."
python3 test/fina_desktop.py
read
