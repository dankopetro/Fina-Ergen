#!/bin/bash
# Script helper para lanzar comandos interactivos en una nueva ventana de terminal
# Detecta kgx, gnome-terminal, konsole, xterm, etc.

COMMAND_TO_RUN="$@"

if [ -z "$COMMAND_TO_RUN" ]; then
    echo "Uso: $0 <comando completo>"
    exit 1
fi

# 1. Intentar KGX (Console) - Preferido en GNOME moderno
if command -v kgx &> /dev/null; then
    kgx -e "$COMMAND_TO_RUN" 2>/dev/null
    exit 0
fi

# 2. Intentar Gnome Terminal
if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "$COMMAND_TO_RUN; echo; read -p 'Presione Enter para cerrar...' variable" 2>/dev/null
    exit 0
fi

# 3. Intentar Konsole (KDE)
if command -v konsole &> /dev/null; then
    konsole -e "$COMMAND_TO_RUN" 2>/dev/null
    exit 0
fi

# 4. Intentar XTerm (Universal fallback)
if command -v xterm &> /dev/null; then
    xterm -e "$COMMAND_TO_RUN" 2>/dev/null
    exit 0
fi

echo "❌ No se encontró ninguna terminal compatible (kgx, gnome-terminal, konsole, xterm)."
exit 1
