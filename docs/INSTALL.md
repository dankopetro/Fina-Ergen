# Guía de Instalación - Fina Asistente de Voz

Esta guía te ayudará a instalar y configurar Fina, el asistente de voz en español para Linux.

## 📋 Requisitos Previos

- **Sistema Operativo**: Linux (Ubuntu 20.04+, Debian, Arch, Fedora)
- **Python**: 3.8 o superior
- **Espacio en Disco**: ~2GB para modelos y dependencias
- **Micrófono**: Para reconocimiento de voz
- **Altavoces/Audífonos**: Para síntesis de voz
- **Lector de Huellas Dactilares**: Opcional pero recomendado

---

## 🔧 Instalación Paso a Paso

### 1. Instalar Dependencias del Sistema

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip python3-venv \
    ffmpeg rofi mpv alsa-utils \
    fprintd libpam-fprintd \
    portaudio19-dev python3-pyaudio \
    git wget curl
```

#### Arch Linux:
```bash
sudo pacman -S \
    python python-pip \
    ffmpeg rofi mpv alsa-utils \
    fprintd \
    portaudio python-pyaudio \
    git wget curl
```

#### Fedora:
```bash
sudo dnf install -y \
    python3 python3-pip \
    ffmpeg rofi mpv alsa-utils \
    fprintd pam_fprintd \
    portaudio-devel python3-pyaudio \
    git wget curl
```

---

### 2. Configurar Autenticación por Huella Dactilar

Si tienes un lector de huellas dactilares, configúralo:

```bash
# Iniciar el servicio fprintd
sudo systemctl start fprintd
sudo systemctl enable fprintd

# Registrar tu huella dactilar
fprintd-enroll

# Verificar que funciona
fprintd-verify
```

**Nota**: Si no tienes lector de huellas, Fina usará autenticación por contraseña automáticamente.

---

### 3. Instalar Piper TTS

Piper es el motor de síntesis de voz que usa Fina:

```bash
# Descargar Piper
cd ~/Downloads
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_x86_64.tar.gz

# Extraer y mover a /usr/local/bin
tar -xzf piper_linux_x86_64.tar.gz
sudo mv piper/piper /usr/local/bin/
sudo chmod +x /usr/local/bin/piper

# Verificar instalación
piper --version
```

---

### 4. Configurar Entorno Virtual de Python

```bash
cd "/home/claudio/Descargas/Fina - Asistente de Voz para Linux"

# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt
```

---

### 5. Descargar Modelos de Voz en Español Argentino

Los modelos de voz deben descargarse manualmente desde Hugging Face:

#### Opción A: Descarga Manual

1. Visita: https://huggingface.co/rhasspy/piper-voices/tree/main/es/es_AR/daniela/high
2. Descarga los siguientes archivos a la carpeta `voice_models/`:

**Voz Femenina (Daniela):**
- `es_AR-daniela-high.onnx`
- `es_AR-daniela-high.onnx.json`

#### Opción B: Usar wget/curl

```bash
cd voice_models/

# Voz femenina (Daniela)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/es_AR-daniela-high.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/es_AR-daniela-high.onnx.json

cd ..
```

---

### 6. Configurar Archivos de Configuración

#### Copiar plantillas:
```bash
cp config_template.py config.py
cp contact_template.json contact.json
```

#### Editar config.py:
```bash
nano config.py  # o usa tu editor favorito
```

Completa las siguientes claves API:
- `GITHUB_TOKEN`: Token de GitHub para GitHub Models
- `EMAIL_USER`: Tu dirección de Gmail
- `EMAIL_PASSWORD`: Contraseña de aplicación de Gmail
- `WEATHER_API_KEY`: Clave de OpenWeatherMap
- `NEWS_API_KEY`: Clave de NewsAPI

#### Editar contact.json:
```bash
nano contact.json
```

Agrega tus contactos de email:
```json
{
  "Juan": "juan@example.com",
  "María": "maria@example.com"
}
```

---

### 7. Descargar Modelo de Whisper

Whisper se descargará automáticamente la primera vez que ejecutes Fina, pero puedes pre-descargarlo:

```bash
python3 -c "import whisper; whisper.load_model('tiny')"
```

---

## 🚀 Ejecutar Fina

```bash
# Asegúrate de estar en el directorio del proyecto
cd "/home/claudio/Descargas/Fina - Asistente de Voz para Linux"

# Activar entorno virtual
source venv/bin/activate

# Ejecutar Fina
python main.py
```

---

## 🎤 Primeros Pasos

1. **Despertar a Fina**: Di "Fina", "Hola Fina" o "Despierta Fina"
2. **Autenticación**: Coloca tu dedo en el lector de huellas (o ingresa tu contraseña)
3. **Comandos**: Una vez autenticado, puedes dar comandos como:
   - "¿Cómo está el clima?"
   - "Reproduce música"
   - "Lee mis correos"
   - "Busca información sobre Linux"

---

## 🔧 Solución de Problemas

### Problema: "fprintd no está instalado"
**Solución**: Instala fprintd o usa autenticación por contraseña (Fina cambiará automáticamente)

### Problema: "Piper no encontrado"
**Solución**: Verifica que piper esté en `/usr/local/bin/` y sea ejecutable

### Problema: "No se reconoce mi voz"
**Solución**: 
- Verifica que el micrófono esté funcionando: `arecord -l`
- Habla más cerca del micrófono
- Reduce el ruido de fondo

### Problema: "Modelos de voz no encontrados"
**Solución**: Asegúrate de haber descargado los modelos `.onnx` y `.onnx.json` en `voice_models/`

### Problema: "Error de API Key"
**Solución**: Verifica que todas las claves API en `config.py` sean válidas

---

## 📚 Recursos Adicionales

- **Documentación de Piper**: https://github.com/rhasspy/piper
- **Modelos de Voz**: https://huggingface.co/rhasspy/piper-voices
- **GitHub Models**: https://github.com/marketplace/models
- **OpenWeatherMap API**: https://openweathermap.org/api
- **NewsAPI**: https://newsapi.org/

---

## 🆘 Obtener Ayuda

Si encuentras problemas:
1. Revisa los logs en la consola
2. Verifica que todas las dependencias estén instaladas
3. Asegúrate de que los archivos de configuración sean correctos
4. Consulta el README.md para más información

---

*¡Disfruta usando Fina, tu asistente de voz en español!* 🇦🇷
