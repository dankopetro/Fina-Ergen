#!/bin/bash
# 0. Configuración Básica
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR" || exit 1

FECHA=$(date +%Y-%m-%d)
HORA=$(date +%H-%M-%S)
LOG_DIR="$ROOT_DIR/Logs/$FECHA"
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

PYTHON="python3"
API="fina_api.py"
BRAIN="main.py"
MONITOR="plugins/doorbell/monitor_ergen.py" 

# Check NPM
if ! command -v npm &> /dev/null; then
    echo "❌ ERROR: npm no encontrado en el PATH."
    exit 1
else
    echo "✅ NPM encontrado: $(npm --version)"
fi

# 3. Lanzar API (Backend/Estado)
echo "🔌 Lanzando API (Backend)..."
if [ -f "$API" ]; then
    $PYTHON -u $API 2>&1 | tee "$LOG_API" &
    PID_API=$!
    echo "✅ API PID: $PID_API. Esperando 3s para arranque..."
    sleep 3
else
    echo "❌ ERROR FATAL: Falta $API"
    exit 1
fi

# 4. Lanzar Brain (Voz/Inteligencia)
echo "🧠 Lanzando CEREBRO (Voz)..."
if [ -f "$BRAIN" ]; then
    $PYTHON -u $BRAIN 2>&1 | tee "$LOG_BRAIN" &
    PID_BRAIN=$!
    echo "✅ BRAIN PID: $PID_BRAIN"
else
    echo "❌ ERROR FATAL: Falta $BRAIN"
    # No salimos, quizás solo quieren UI
fi

# 5. Monitores (Opcionales / Vigilancia)
WATCHDOG="mem_watchdog.py"
if [ -f "$WATCHDOG" ]; then
    $PYTHON -u $WATCHDOG 2>&1 | tee "$LOG_DIR/watchdog_$HORA.log" &
fi

if [ -f "$MONITOR" ]; then
    $PYTHON -u $MONITOR 2>&1 | tee "$LOG_DIR/monitor_$HORA.log" &
fi

sleep 2

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
