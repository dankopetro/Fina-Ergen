#!/bin/zsh
# Cargar configuración de usuario (para envs, alias, etc)
source ~/.zshrc

# Ir al directorio raíz del proyecto
cd "$(dirname "$0")/.."

# Ejecutar
echo "🧠 Core Jaio..."
python3 main.py
read
