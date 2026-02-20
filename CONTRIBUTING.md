# Contribuyendo a Fina Ergen 🧩

Primero que nada, **¡gracias por tu interés en hacer a Fina Ergen aún mejor!** 🎉 Fina es un proyecto de código abierto que se nutre del esfuerzo y las ideas de personas como tú.

Este documento proporciona pautas para colaborar, ya sea creando un nuevo módulo (plugin), corrigiendo errores, mejorando la interfaz de usuario web o ayudando con la documentación.

---

## � ¿Cómo puedo colaborar?

Existen muchísimas formas de ayudar al ecosistema de Fina Ergen:

1. **Creando nuevos Plugins**: Fina Ergen está construida sobre una arquitectura modular. Si tienes una bombilla inteligente, un ventilador, una TV o cualquier dispositivo, ¡crea un plugin para él! Revisa el [repositorio oficial de Plugins Market](https://github.com/dankopetro/Fina-Plugins-Market) para ver la guía del SDK y agregar el tuyo.
2. **Reportando Errores**: Si Fina se cierra sola, un comando no funciona o la interfaz tiene problemas, crea un [Issue](https://github.com/dankopetro/Fina-Ergen/issues) explicando qué ocurrió y, si es posible, mostrando el log de la terminal.
3. **Proponiendo Mejoras**: ¿Una nueva función para el frontend en Vue? ¿Un módulo de IA distinto? Comparte tu idea.
4. **Mejorando el Código (Pull Requests)**: Si ya has arreglado algo o añadido una función genial al núcleo (Fina Core) o al Frontend (Tauri/Vue).

---

## 🛠️ Entorno de Desarrollo

Para trabajar en el núcleo de Fina o en su interfaz gráfica, necesitarás instalar las herramientas base.

### Requisitos Mínimos:
- **Python 3.10+**: Para el motor de voz y los plugins (Fina Core).
- **Node.js 20+** y **npm**: Para la interfaz gráfica que emplea Vue 3 y Vite.
- **Rust (rustup)**: Para el backend del frontend usando la plataforma Tauri v2.

### Pasos Iniciales:
1. Haz un **fork** de este repositorio.
2. Clona tu fork localmente: `git clone https://github.com/tu-usuario/Fina-Ergen.git`
3. Instala las dependencias de Python (si tocas el Core): `pip install -r requirements.txt`
4. Instala las dependencias del frontend: `npm install`
5. Levanta el entorno de prueba de Tauri: `npm run tauri dev`

---

## 🚦 Reglas para los Pull Requests (PRs)

Para mantener el código ordenado y seguro para todos:

*   **Paso 1: Sincroniza**. Asegúrate de estar trabajando sobre la última versión de la rama `master`.
*   **Paso 2: Describe bien tu código**. Explica claramente en tu PR qué hace tu código y por qué es necesario.
*   **Paso 3: Respeta la identidad visual**. Si trabajas en el frontend (`src/App.vue`), mantén la estética (colores cyan, neón, modo oscuro) establecida.
*   **Paso 4: No subas credenciales**. **NUNCA** incluyas en tus PR tus tokens de OpenAI, ElevenLabs o llaves `.pem` privadas.

## 🤝 Código de Conducta

Por favor, mantén siempre el respeto en los Issues y Pull Requests. Queremos que el ecosistema de Fina sea amigable para desarrolladores de todos los niveles. Todos hemos sido principiantes alguna vez.

---

¡Disfruta programando y gracias por hacer crecer a Fina Ergen! 🚀💻