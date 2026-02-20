# 🎙️ Fina - Asistente de Voz para Linux 🐧 (v2.8.7 RC)

¡Bienvenido a **Fina Ergen**, tu asistente inteligente personal diseñado para controlar tu escritorio Linux y tu hogar inteligente con el poder de tu voz! Esta versión 2.8.7 Release Candidate consolida la estabilidad total del sistema.

---

## 🚀 Instalación y Uso

Sigue estos pasos para poner a Fina en marcha en tu sistema Arch Linux / Manjaro (o adaptable a Debian/Ubuntu).

### 1. Requisitos Previos

Asegúrate de tener instaladas las siguientes herramientas del sistema:
*   **Python 3.8+**
*   **Android Debug Bridge (ADB):** Para controlar la TV.
*   **WebKit2GTK:** Para la interfaz visual.

### 2. Arranque Oficial (Ergen)

Para garantizar la sincronización entre el Cerebro (Python) y la Interfaz (Tauri), usa siempre el script de lanzamiento:
```bash
./lanzar_fina_simple.sh
```

---

## 🧹 Apagado Robusto (Janitor)
Se ha implementado `janitor.py`, un sistema de limpieza atómico que asegura que al cerrar Fina, todos los subprocesos gráficos (Weston, Waydroid) y la interfaz se cierren de golpe, devolviendo el control total de la terminal al usuario de forma instantánea. No más terminales bloqueadas o ventanas zombis.

---

## 📺 Control de TV Android
Fina ahora es proactiva. Al iniciar el sistema, escaneará automáticamente tu red para informarte si la televisión está conectada y lista para recibir comandos. Puedes subir volumen, cambiar canales y lanzar apps con órdenes naturales como:
* *"Pon Telefe en la tele"*
* *"Subí el volumen 10 puntos"*

---

## 🧬 Biometría y ADN de Voz
La versión 2.8.7 RC incluye una corrección crítica en la captura de audio, permitiendo un reconocimiento de identidad (Claudio) con una precisión superior al 95%. Fina reconoce tu "ADN sonoro" antes de ejecutar comandos críticos.

---

## 🗣️ Configuración de Idioma y Voces
Fina utiliza modelos neuronales Piper TTS locales.
*   **Voz por defecto:** Daniela (🇦🇷).
*   **Comando:** "Fina, cambia el modelo de voz".

---

## 🚀 El Futuro: Fina-Ergen
Con la etapa Ergen completada, iniciamos la investigación para **Fina-Ergen** (Adolescente), un salto evolutivo que traerá:
*   **Hyper-UI**: Interfaz renovada con widgets avanzados y animaciones fluidas.
*   **IA Madura**: Una inteligencia más conversacional, proactiva y capaz de gestionar su propio ecosistema de plugins.

---

## 📜 Créditos
Este proyecto es una evolución del **Jarvis Voice Assistant**.
*   **Desarrollador Original:** Jarvis Team.
*   **Adaptación y Evolución Ergen:** Claudio (Dankopetro).

¡Disfruta de tu nuevo asistente en su estado más estable!
