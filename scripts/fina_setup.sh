#!/bin/bash
# ==============================================================================
# FINA ERGEN - ASISTENTE DE POST-INSTALACIÓN
# ==============================================================================
# Este script configura el idioma inicial y descarga los modelos pesados (Voz/STT)
# Basado en Zenity para una interfaz amigable en Linux.

set -e

# --- CONFIGURACIÓN DE RUTAS ---
CONFIG_DIR="$HOME/.config/Fina"
SETTINGS_PATH="$CONFIG_DIR/settings.json"
VOICE_MODELS_DIR="$CONFIG_DIR/voice_models"
VOSK_MODELS_DIR="$CONFIG_DIR/model"

mkdir -p "$VOICE_MODELS_DIR"
mkdir -p "$VOSK_MODELS_DIR"

# Verificar si zenity está instalado
if ! command -v zenity &> /dev/null; then
    echo "Zenity no está instalado. Instalándolo..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y zenity
    else
        echo "No se pudo instalar zenity automáticamente. Por favor instálalo manualmente."
        exit 1
    fi
fi

# --- 1. SELECCIÓN DE IDIOMA ---
LANG=$(zenity --list --title="Fina Ergen - Idioma" \
    --column="Código" --column="Idioma" \
    "es" "Español (Castellano/Argentino)" \
    "en" "English (United States/UK)" \
    "fr" "Français (France)" \
    "de" "Deutsch (Deutschland)" \
    "ja" "Japanese (日本語)" \
    "zh" "Chinese (Mandarin)" \
    --height=300 --width=400 --hide-column=1)

if [ -z "$LANG" ]; then
    exit 1
fi

# --- 2. SELECCIÓN DE VOZ ---
case $LANG in
    "es")
        VOICE_LIST=("es_AR-daniela-high" "Daniela (Femenina - Argentina)" \
                   "es_MX-claude-high" "Claude (Masculina - México)" \
                   "es_MX-laura-high" "Laura (Femenina - México)")
        ;;
    "en")
        VOICE_LIST=("en_US-amy-low" "Amy (Female - USA)" \
                   "en_US-lessac-high" "Lessac (Male - USA)" \
                   "en_GB-vctk-medium" "VCTK (British)")
        ;;
    "fr")
        VOICE_LIST=("fr_FR-siwis-low" "Siwis (Féminin)")
        ;;
    "de")
        VOICE_LIST=("de_DE-thorsten-low" "Thorsten (Männlich)")
        ;;
    "ja")
        VOICE_LIST=("ja_JP-misaki-low" "Misaki (女性)")
        ;;
    "zh")
        VOICE_LIST=("zh_CN-huayan-medium" "Huayan (女性)")
        ;;
esac

VOICE_ID=$(zenity --list --title="Fina Ergen - Modelo de Voz" \
    --text="Selecciona el modelo de voz para $LANG:" \
    --column="ID" --column="Descripción" \
    "${VOICE_LIST[@]}" \
    --height=300 --width=450 --hide-column=1)

if [ -z "$VOICE_ID" ]; then
    exit 1
fi

# --- 3. DESCARGA DE MODELOS ---

# Construir URLs Piper
case $VOICE_ID in
    "es_AR-daniela-high") URL_ONNX="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/es_AR-daniela-high.onnx" ;;
    "es_MX-claude-high") URL_ONNX="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx" ;;
    "es_MX-laura-high") URL_ONNX="https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/laura/high/es_MX-laura-high.onnx" ;;
    "en_US-amy-low") URL_ONNX="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low/en_US-amy-low.onnx" ;;
    "en_US-lessac-high") URL_ONNX="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx" ;;
    "en_GB-vctk-medium") URL_ONNX="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/vctk/medium/en_GB-vctk-medium.onnx" ;;
    "fr_FR-siwis-low") URL_ONNX="https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/low/fr_FR-siwis-low.onnx" ;;
    "de_DE-thorsten-low") URL_ONNX="https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/low/de_DE-thorsten-low.onnx" ;;
    "ja_JP-misaki-low") URL_ONNX="https://huggingface.co/rhasspy/piper-voices/resolve/main/ja/ja_JP/misaki/low/ja_JP-misaki-low.onnx" ;;
    "zh_CN-huayan-medium") URL_ONNX="https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/huayan/medium/zh_CN-huayan-medium.onnx" ;;
esac
URL_JSON="${URL_ONNX}.json"

# Vosk Model URL Mapping
case $LANG in
    "es") URL_VOSK="https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip"; VOSK_NAME="vosk-model-es-0.42" ;;
    "en") URL_VOSK="https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip"; VOSK_NAME="vosk-model-en-us-0.22" ;;
    "fr") URL_VOSK="https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip"; VOSK_NAME="vosk-model-fr-0.22" ;;
    "de") URL_VOSK="https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip"; VOSK_NAME="vosk-model-de-0.21" ;;
    "ja") URL_VOSK="https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip"; VOSK_NAME="vosk-model-ja-0.22" ;;
    "zh") URL_VOSK="https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip"; VOSK_NAME="vosk-model-cn-0.22" ;;
esac

(
echo "10" ; echo "# Descargando Modelo Piper (TTS)..."
wget -q "$URL_ONNX" -O "$VOICE_MODELS_DIR/${VOICE_ID}.onnx"
wget -q "$URL_JSON" -O "$VOICE_MODELS_DIR/${VOICE_ID}.onnx.json"

echo "40" ; echo "# Descargando Modelo Vosk (STT) - Esto puede tardar..."
wget -q "$URL_VOSK" -O "$VOSK_MODELS_DIR/${VOSK_NAME}.zip"

echo "80" ; echo "# Descomprimiendo Vosk..."
unzip -o "$VOSK_MODELS_DIR/${VOSK_NAME}.zip" -d "$VOSK_MODELS_DIR/"
rm "$VOSK_MODELS_DIR/${VOSK_NAME}.zip"

echo "100" ; echo "# Finalizando configuración..."
) | zenity --progress --title="Instalación de Modelos" --text="Preparando..." --percentage=0 --auto-close

# --- 4. ACTUALIZAR SETTINGS.JSON ---
python3 - <<EOF
import json, os
path = "$SETTINGS_PATH"
data = {}
if os.path.exists(path):
    with open(path, 'r') as f: data = json.load(f)

if "apis" not in data: data["apis"] = {}

data["apis"]["FINA_LANGUAGE"] = "$LANG"
data["apis"]["VOICE_MODEL"] = "$VOICE_ID"
data["apis"]["VOSK_MODEL"] = "$VOSK_NAME"

os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w') as f: json.dump(data, f, indent=4)
EOF

zenity --info --title="Completado" --text="Fina Ergen ha sido configurada correctamente.\nIdioma: $LANG\nVoz: $VOICE_ID\n\nYa puedes iniciar la aplicación."

exit 0
