#!/bin/bash
# 0. Configuración Básica
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR" || exit 1

FECHA=$(date +%Y-%m-%d)
HORA=$(date +%H-%M-%S)
LOG_DIR="$HOME/.config/Fina/Logs/$FECHA"
mkdir -p "$LOG_DIR"

LOG_API="$LOG_DIR/api_$HORA.log"
LOG_BRAIN="$LOG_DIR/brain_$HORA.log"
LOG_UI="$LOG_DIR/ui_tauri_$HORA.log"

echo "🔥 Iniciando Fina Ergen (Modo Completo)..."
echo "📂 Logs en: $LOG_DIR"

# 1. Matar viejos procesos
echo "🧹 Limpiando procesos antiguos..."
pkill -f "fina_api.py"
pkill -f "$ROOT_DIR/main.py"
pkill -f "monitor_ergen.py"
pkill -f "mem_watchdog.py"
pkill -f "weston"
pkill -f "fina-app"

# 2. Detección Inteligente de Python y Entorno Virtual (VENV)
# Buscamos en orden: 1. Locales, 2. Entorno Activo, 3. Globales (~/.venv)
PYTHON=""

# 2.1 Buscar en subcarpetas locales comunes
for venv_name in "venv" ".venv" "env" ".env"; do
    if [ -f "$ROOT_DIR/$venv_name/bin/python3" ]; then
        PYTHON="$ROOT_DIR/$venv_name/bin/python3"
        echo "🐍 [ENCONTRADO] Entorno Virtual '$venv_name' detectado en proyecto."
        break
    fi
done

# 2.2 Buscar en entorno activo o global del usuario
if [ -z "$PYTHON" ]; then
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        PYTHON="$VIRTUAL_ENV/bin/python3"
        echo "🐍 [ACTIVO] Usando entorno virtual activo: $VIRTUAL_ENV"
    elif [ -f "$HOME/.venv/bin/python3" ]; then
        PYTHON="$HOME/.venv/bin/python3"
        echo "🐍 [GLOBAL] Usando entorno virtual del HOME (~/.venv)."
    elif [ -f "$HOME/.local/share/Fina/venv/bin/python3" ]; then
        PYTHON="$HOME/.local/share/Fina/venv/bin/python3"
        echo "🐍 [GLOBAL] Usando entorno virtual de Fina en .local."
    fi
fi

# 2.3 MODO RESCATE (CRÍTICO): Si no hay venv, lo creamos. NUNCA usar Python del sistema directamente con pip.
if [ -z "$PYTHON" ]; then
    echo "🛠️ [RESCATE] No se encontró ningún entorno virtual. Creando uno en '$ROOT_DIR/venv'..."
    python3 -m venv "$ROOT_DIR/venv" || { echo "❌ ERROR: No se pudo crear venv. Instala 'python3-venv'."; exit 1; }
    PYTHON="$ROOT_DIR/venv/bin/python3"
fi

# 2.1 Asegurar dependencias (FastAPI, Resemblyzer, etc)
echo "📦 Verificando dependencias..."
if [ -f "$ROOT_DIR/requirements.txt" ]; then
    # Un chequeo rápido para no instalar siempre: si falla al importar fastapi, instalamos todo
    if ! "$PYTHON" -c "import fastapi, resemblyzer" &>/dev/null; then
        echo "📥 Instalando librerías faltantes (esto solo pasará una vez)..."
        "$PYTHON" -m pip install --upgrade pip &>/dev/null
        "$PYTHON" -m pip install -r "$ROOT_DIR/requirements.txt" || echo "⚠️ Error instalando algunas dependencias."
    else
        echo "✅ Librerías Python OK."
    fi
fi

# 2.2 Verificación de Piper (TTS)
if ! command -v piper &> /dev/null; then
    # Lugares probables
    for loc in "/usr/local/bin/piper" "$ROOT_DIR/piper" "$ROOT_DIR/assets/piper" "$(dirname "$PYTHON")/piper"; do
        if [ -x "$loc" ]; then
            export PATH="$(dirname "$loc"):$PATH"
            echo "✅ Piper encontrado en: $loc"
            PIPER_OK=1
            break
        fi
    done
    
    if [ -z "$PIPER_OK" ]; then
        echo "⚠️ Piper no encontrado. La voz no funcionará."
        echo "💡 Tip: sudo cp assets/piper /usr/local/bin/"
    fi
fi

API="fina_api.py"
BRAIN="main.py"
MONITOR="plugins/doorbell/monitor_ergen.py" 
WATCHDOG="mem_watchdog.py"

# 3. Lanzar API (Backend)
echo "🔌 Lanzando API con PID propio..."
$PYTHON -u $API 2>&1 | tee "$LOG_API" &
PID_API=$!
sleep 2

# 4. Lanzar Brain (Cerebro)
echo "🧠 Lanzando CEREBRO con PID propio..."
$PYTHON -u $BRAIN 2>&1 | tee "$LOG_BRAIN" &
PID_BRAIN=$!

# 5. Monitores
[ -f "$WATCHDOG" ] && $PYTHON -u $WATCHDOG &> /dev/null &
[ -f "$MONITOR" ] && $PYTHON -u $MONITOR &> /dev/null &

sleep 1

# 6. Lanzar UI
echo "🚀 Lanzando Interfaz Visual..."
echo "Registro de UI (npm) en: $LOG_UI"
echo "---------------------------------------" >> "$LOG_UI"

# Función de limpieza robusta
cleanup() {
    echo "🛑 Cerrando Fina Ergen y limpiando recursos..."
    
    # 1. Llamar al NUEVO Conserje de Python (Alternativa Superior)
    PYTHON_BIN="python3"
    if [ -f "scripts/janitor.py" ]; then
        $PYTHON_BIN scripts/janitor.py
    fi
    
    # 2. Refuerzo específico para Weston y Waydroid (a veces son persistentes)
    echo "🧹 Verificando cierre de procesos gráficos..."
    pkill -9 -u $USER -f "weston" 2>/dev/null
    pkill -9 -u $USER -f "waydroid" 2>/dev/null
    
    # Matar subprocesos del script por si acaso
    kill $PID_API 2>/dev/null
    kill $PID_BRAIN 2>/dev/null
    
    echo "✅ Sesión finalizada correctamente."
}

# Ejecutar cleanup al salir (sea normal o por Ctrl+C/Terminación)
trap cleanup EXIT INT TERM

# Ejecutamos tauri dev y mantenemos el script vivo
npm run tauri dev 2>&1 | tee "$LOG_UI"
