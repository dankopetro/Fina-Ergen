# Script universal para crear el acceso directo de Fina Ergen
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ICON_PATH="$ROOT_DIR/src-tauri/icons/128x128.png"
EXEC_PATH="$ROOT_DIR/lanzar_fina_simple.sh"
DESKTOP_FILE="$HOME/.local/share/applications/fina-ergen.desktop"

mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Name=Fina Ergen
Comment=AI Assistant and Home Automation
Exec=bash "$EXEC_PATH"
Icon=$ICON_PATH
Terminal=true
Type=Application
Categories=Utility;Science;Education;
Keywords=ai;assistant;voice;
EOF

chmod +x "$DESKTOP_FILE"
echo "✅ Acceso directo creado en: $DESKTOP_FILE"
echo "💡 Ya debería aparecer en tu menú como 'Fina Ergen'"
