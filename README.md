<h1 align="center">
  <img src="static/assets/avatar.png" width="120" alt="Fina AI">
  <br>Fina Ergen v3.6.0
</h1>

<p align="center">
  <strong>El Asistente de Voz Modular y Domótico para Linux</strong>
</p>

<p align="center">
  <a href="#caracteristicas">Características</a> •
  <a href="#arquitectura">Arquitectura Modular</a> •
  <a href="https://github.com/dankopetro/Fina-Ergen/wiki">📚 CÓDICE MAESTRO (Wiki)</a> •
  <a href="#instalacion">Instalación Rápida</a>
</p>

<p align="center">
  <img src="manual_images/ui_check.png" width="800" alt="Fina Ergen Interface">
</p>

---

**Fina Ergen** no es solo un script; es un cerebro avanzado que corre localmente en tu sistema Linux con una hermosa interfaz nativa de escritorio (Tauri/Vue). Diseñada para procesar lenguaje natural en español con extrema rapidez offline, Fina es capaz de todo: desde hablarte con voces hiperrealistas y autenticarte por biometría dual, hasta controlar toda la domótica de tu casa (Cámaras, Android TV, Aire Acondicionado) mediante su increíble arquitectura de plugins.

<a id="caracteristicas"></a>
## ✨ Características Principales

- ⚡ **Súper Procesamiento de Voz:** Usa Vosk para velocidad offline relámpago y Whisper como alternativa.
- 🗣️ **Voces Naturales Infinitas (TTS):** Integración local mediante Piper (sin red) o conexión premium a ElevenLabs.
- 🔐 **Biometría Dual:** Primer sistema en Linux en cruzar huellas digitales de hardware con el reconocimiento irrefutable de la firma de tu voz (_Voice ID_ vía Resemblyzer).
- 🧠 **Cerebro Dinámico (LLM):** Soporte nativo para GPT/Mistral u otros modelos. Si la consulta supera sus acciones locales, su IA piensa la respuesta.
- 📺 **Domótica Extrema (IoT):** Fina controla tu Smart TV, decodificadores, aires acondicionados y sistemas de videovigilancia Tuya/SmartLife sin pestañear.
- 🔌 **Arquitectura 100% Modular:** Instala solo el motor base. Luego elige qué dependencias de IoT quieres integrar: tu computadora no colapsará instalando librerías que no usa.

<a id="arquitectura"></a>
## ⚙️ Arquitectura Modular (Fina Plugins)

Fina está dividida en un núcleo de IA liviano y una potente de capa externa comunitaria.

| Categoría   | Plugins Incorporados                      | Funciones Destacadas                                   |
| :---------- | :---------------------------------------- | :----------------------------------------------------- |
| **TV**      | `Android TV Remote`, `Chromecast`, `TCL`  | Mute, cambiar canales de decodificadores, HDMI y YouTube. |
| **Clima**   | `Midea`, `Surrey`                         | Ajuste por voz de los grados, modo ventilación y calor.|
| **Timbre**  | `Tuya Doorbell Sniper`                    | Integración con Waydroid para atender a las visitas por Fina. |
| **Sistema** | `App Management`, `Brightnes`, `Xdotool`  | Minimizar, cerrar y suspender herramientas de escritorio linux. |
| **Terceros**| `plugins/custom/`                         | Descarga automatizaciones de la comunidad sin editar el repo. |

<a id="instalacion"></a>
## 🚀 Instalación (Universal)

A partir de la versión v3.5.4, Fina Ergen es 100% modular y autodependiente. Ya no necesitas clonar el código fuente. Dirígete a la pestaña de **Releases** en GitHub y descarga el instalador que mejor se adapte a tu distribución Linux:

### 1. Instaladores Nativos (Ubuntu / Debian / Fedora)
Son la vía más integrada. Descarga el paquete e instálalo con tu gestor habitual:
- **Para Ubuntu/Debian/Mint:** Descarga el archivo `.deb` e instálalo con `sudo dpkg -i fina-ergen_..._amd64.deb`
- **Para Fedora/RHEL:** Descarga el archivo `.rpm` e instálalo con `sudo rpm -i fina-ergen_..._x86_64.rpm`

### 2. Formato Portable (AppImage)
Si prefieres no instalar nada a nivel sistema, descarga una de nuestras versiones AppImage. Solo dale permisos de ejecución (`chmod +x archivo.AppImage`) y lánzalo.
* **fina-ergen_..._amd64.AppImage (Recomendado):** Comprimida en formato XZ (pesa solo unos ~25MB). Contiene parches para mostrar correctamente los íconos del sistema en Ubuntu 24.04 y superior.
* **fina-ergen_..._x86_64.AppImage:** Versión AppImage genérica cruda producida por el compilador para compatibilidad heredada.

---

## 🧩 Plugins y Extensiones (Market)

Fina viene "pelada" de fábrica para ser rapidísima. Todo el control de aparatos IoT, TV y automatizaciones de terceros se descarga por separado mediante un Market. Tienes dos maneras de hacerlo:

### Vía Interfaz (Recomendada)
1. Abre Fina Ergen y dirígete al botón **Market de Plugins** (actualmente visible en la sección *Agenda*).
2. Explora el repertorio, haz clic en **Instalar** al plugin que desees y Fina se encargará de descargarlo, inyectarlo en tu perfil de usuario y encenderlo automáticamente.

### Vía Manual
1. Visita nuestro Repositorio Oficial de Extensiones en la web: **[Fina Plugins Market](https://github.com/dankopetro/Fina-Plugins-Market)**
2. Descarga la carpeta de la extensión que te interese (ej: `AirConditioning/Midea-Surrey`).
3. Cópiala en la carpeta de configuraciones de tu usuario de Linux:
   `~/.config/Fina/plugins/` *(Ej: `~/.config/Fina/plugins/AirConditioning/Midea-Surrey/`)*
4. Reinicia Fina Ergen para cargarla.
## 📚 Códice Maestro (Wiki Oficial)

Toda la documentación técnica exhaustiva, guías de usuario y manuales del sistema han sido iterados y migrados al gigantesco **Códice Maestro** alojado directamente en nuestra Wiki. Es la fuente de verdad absoluta para domar al asistente:

- 📖 [**Explorar la Wiki Oficial de Fina Ergen**](https://github.com/dankopetro/Fina-Ergen/wiki)
- 🧩 [**Guía de Creación de Plugins (SDK)**](https://github.com/dankopetro/Fina-Plugins-Market): Aprende a desarrollar tus propios módulos y arquitecturas IoT leyendo los estándares oficiales directamente en el Market.

## 🔮 Roadmap v4.0 (El Futuro)

Fina no conoce techo. Hacia adelante, el vector principal de evolución se ancla en:
- **Inteligencia Predictiva Proactiva (Ambient Computing):** Integración de radares mmWave para seguimiento espacial automático. Fina sabrá en qué habitación estás sin necesidad de cámaras, moviendo la música y las confirmaciones al altavoz más cercano a ti.
- **Llama.cpp en VRAM:** LLLM corriendo nativamente (Mistral/Llama3) local para pulverizar en definitiva la dependencia a IA de emporios comerciales (OpenAI). 
- **Hardware Libre (Proyecto Fina-Acoustics):** Diseños satelitales basados en arrays far-field y Raspberry Pi con *Edge-AI* para aniquilar tus Google Nest o Echo Dots dotando privacidad física del 100%.
- **Voz VITS Emocional:** Un Motor TTS generativo y neural avanzado que cambiará su propia euforia o tono, pasando a un susurro si detecta que es de madrugada, y gritando frente a intrusos hostiles.

## 💖 Apoya el Proyecto

Si Fina Ergen te ha sido útil y quieres apoyar su continuo desarrollo, puedes invitarme un café o realizar una donación. ¡Toda ayuda es bienvenida para seguir mejorando el asistente!

| Plataforma | Link |
| :--- | :--- |
| **☕ Buy Me a Coffee** | [![Buy Me A Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/dankopetro) |
| **🅿️ PayPal** | [![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/dankopetro) |
| **₿ Bitcoin** | `bc1qa75vqz7q7kac0mdf8tzsd4gxpnljh5cukvt2ll` |

---

## 🏆 Agradecimientos
El desarrollo de Fina comenzó como un _fork_ espiritual fuertemente inspirado en el código fuente del proyecto open-source [**Jarvis Voice Assistant**](https://github.com/KhagendraN/Jarvis-Voice-Assistant) creado por [@KhagendraN](https://github.com/KhagendraN) bajo licencia MIT. A partir de esos divertidos scripts iniciales de automatización, Fina evolucionó con los años hacia esta inmensa arquitectura modular. Fina no existiría hoy con esta arquitectura de no ser por esos primeros cimientos.

---
<p align="center">
  <b>Hecho con ❤️ en Argentina. Licencia MIT.</b> <br>
  <i>"El alambre inteligente."</i>
</p>
