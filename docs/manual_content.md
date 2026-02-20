
# Manual Oficial de Fina 2.0
## Asistente de Voz Inteligente para Linux

![Portada](manual_images/cover.png)

---

### 1. Introducción
**Fina** no es solo un asistente de voz. Es un sistema operativo verbal diseñado para Linux (Arch/Manjaro/Mint) que prioriza la **privacidad**, el **control local** y la **integración profunda** con tu hardware.

A diferencia de Alexa o Google Assistant, Fina corre en tu máquina, lee tus archivos, controla tu mouse y gestiona tus dispositivos IoT sin depender exclusivamente de servidores externos.

#### Filosofía de Diseño
*   **Local First:** Procesamiento de voz (Vosk) y TTS (Piper) en local para latencia cero y privacidad.
*   **Híbrido Inteligente:** Usa LLMs potentes (Mistral/Gemini) solo cuando la conversación lo requiere.
*   **Modular:** Cada habilidad (música, TV, seguridad) es un módulo independiente.

---

### 2. Arquitectura del Sistema
Fina actúa como un cerebro central que orquesta múltiples subsistemas:

![Arquitectura](manual_images/arch.png)

1.  **Oído (STT):** Vosk (off-line) escucha el comando de activación "Fina".
2.  **Cerebro (NLP):** Clasificador de intenciones (BERT) decide qué quieres hacer.
3.  **Voz (TTS):** Piper genera una voz natural en tiempo real.
4.  **Manos (Ejecución):** Scripts de Python y Bash ejecutan las acciones (abrir apps, ADB, Tuya).

---

### 3. Instalación y Requisitos

#### Requisitos del Sistema
*   **OS:** Linux (Arch, Manjaro, Ubuntu, Mint).
*   **Python:** 3.10 o superior.
*   **Hardware:** Micrófono USB decente, Altavoces.

#### Dependencias Clave
```bash
sudo pacman -S vlc ffmpeg espeak-ng adb
pip install -r requirements.txt
```

#### Instalación Rápida
1.  Clonar el repositorio.
2.  Crear entorno virtual: `python -m venv .venv`
3.  Activar: `source .venv/bin/activate`
4.  Instalar dependencias: `pip install -r requirements.txt`
5.  Configurar claves en `config.py` y `tuya_config.json`.

---

### 4. Funcionalidades Principales

#### 🏠 Domótica y Seguridad (Nuevo)
Fina ahora se integra con dispositivos Tuya, incluyendo **Timbres Inteligentes**.

*   **"Fina, ¿cómo está el timbre?"** -> Reporte de batería y estado.
*   **"Muéstrame la puerta"** -> Abre una foto reciente de la cámara.
*   **"Pon la cámara de la puerta"** -> Abre VLC con video en vivo (HLS).
*   **Vigilancia Pasiva:** Fina te avisa proactivamente si alguien toca el timbre.

#### 📺 Control de TV (Android TV/ADB)
Control total de tu Smart TV sin control remoto.
*   *"Enciende la tele"* / *"Apágala"*
*   *"Pon YouTube"* / *"Abre Netflix"*
*   *"Sube el volumen 5 puntos"*

#### 🔐 Biometría de Voz
Fina sabe quién eres.
*   Al pedir comandos críticos (apagar PC, actualizar sistema), Fina verifica tu huella vocal.
*   **Enrolamiento:** Ejecuta `python scripts/enroll_voice.py` para registrar tu voz.

#### 💻 Control del Sistema
*   *"Abre el navegador"*
*   *"Busca 'noticias de hoy' en Google"*
*   *"Sube el brillo de la pantalla"*

---

### 5. Roadmap y Futuros Desafíos 🚀

El desarrollo de Fina continúa. Aquí están los próximos hitos para llevarla al siguiente nivel:

#### A. Cerebro Local 100% (Ollama/Llama 3)
**Desafío:** Eliminar la dependencia de APIs externas para el chat general.
**Solución:** Integrar **Ollama** corriendo **Llama 3 8B** localmente. Esto permitirá conversar con Fina sin internet.

#### B. Visión Computacional (Ojos Reales)
**Desafío:** Que Fina "vea" a través de una webcam.
**Solución:** Integrar **YOLOv8** para que Fina describa lo que ve: *"Veo a Claudio sosteniendo una taza de café"*.

#### C. Control de Mouse por Voz (Manos Libres total)
**Desafío:** Navegar por el escritorio sin tocar el mouse.
**Solución:** Usar una cuadrícula numerada en pantalla para hacer clics precisos con la voz ("Clic en 5", "Scroll abajo").

#### D. Multi-room Audio
**Desafío:** Que Fina te escuche y responda en cualquier habitación.
**Solución:** Usar satélites ESP32 con micrófonos (ESPHome) enviando audio a la instancia central de Fina.

---

### 6. Galería de Interfaz Real
Aquí podemos ver a Fina en acción en tu sistema:

**Pantalla de Carga y Verificación:**
![Carga](manual_images/ui_loading.png)

**Interfaz Principal Activada (V2):**
![Interfaz](manual_images/ui_check.png)

---

**Fina AI Project - 2026**
*Desarrollado con pasión para Linux.*
