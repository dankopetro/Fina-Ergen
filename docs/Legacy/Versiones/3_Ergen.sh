#!/bin/zsh
source ~/.zshrc

# Ir a la raíz del proyecto
cd "$(dirname "$0")/.."

echo "🔥 Ergen..."
# Intentar ejecutar
if command -v npm &> /dev/null; then
    npm run tauri dev
else
    cargo tauri dev
fi
read
