# 📱 Guía de Automatización Móvil de Fina Ergen

Esta guía documenta el sistema de interacción con dispositivos móviles. 

## 🔄 Cambio de Estrategia (Feb 2026)
Tras exhaustivas pruebas con ADB (Android Debug Bridge), se ha decidido **migrar la funcionalidad de mensajería (WhatsApp)** hacia una **integración Web** en futuras versiones.

**Razones:**
1.  ADB depende críticamente del estado del dispositivo (bloqueado/desbloqueado).
2.  La automatización de clicks (Auto-Tap) es frágil ante cambios de interfaz.
3.  La experiencia de usuario es más robusta usando WhatsApp Web en el escritorio.

## 🚀 Funcionalidades Actuales (ADB)

Aunque el envío de mensajes se moverá a Web, ADB sigue siendo crucial para:
1.  **Detección de Apps:** Fina sabe qué apps están instaladas en el celular.
2.  **Sincronización de Contactos:** `plugins/system/sync_contacts.py` extrae la agenda para usarla en comandos de voz.
3.  **Lanzamiento de Apps:** Fina puede abrir apps en el celular bajo demanda.

---

## 📅 Roadmap: Centro de Mensajería Unificado (WebView)

Para la próxima fase de desarrollo (Instalador/Setup), implementaremos una arquitectura híbrida:

### 1. Funciones Nativas (ADB - Celular)
Estas funciones seguirán operando directamente sobre el dispositivo Android conectado, ya que son robustas y estándar:
*   **Llamadas Telefónicas:** Vía Intent `ACTION_CALL`.
*   **SMS:** Envío silencioso mediante `service call isms` (con detección inteligente de versión Android).
*   **Sincronización de Contactos:** Lectura de agenda para comandos de voz.

### 2. Mensajería Web (Plugins WebView)
Las apps de mensajería modernas se gestionarán a través de una **Ventana Oculta de Navegador (WebView)** integrada en Fina, eliminando la dependencia de "Auto-Taps" inestables en el celular.

**Apps Soportadas (Core Plugins):**
1.  **WhatsApp Web** (Estándar global).
2.  **Telegram Web** (Alternativa robusta).
3.  **Facebook Messenger** (Gran base de usuarios).
4.  **Signal** (Foco en privacidad).

**Workflow de Usuario (Privacidad Primero):**
1.  **Detección Pasiva:** Al conectar el celular, Fina detecta qué apps están instaladas (solo informativo).
2.  **Consulta (Opt-In):** Fina pregunta: *"Veo que usas WhatsApp y Signal. ¿Quieres vincularlos para enviar mensajes desde aquí?"*
3.  **Vinculación:** Se abre una ventana emergente con el QR de la app elegida.
4.  **Uso Invisible:** Una vez vinculado, Fina usa la sesión guardada para enviar mensajes en segundo plano.

### 3. Sistema de Plugins Abierto
Para soportar futuras apps (Discord, Slack, WeChat), se creará una estructura de `manifest.json` donde desarrolladores puedan definir:
*   URL del servicio web.
*   Selectores CSS para buscar contactos y cajas de texto.
*   Scripts de inyección JS personalizados.

---

**Ubicación de Archivos Clave:**
*   `plugins/system/mobile_hub.py`: Gestión de ADB (SMS/Llamadas).
*   `plugins/system/sync_contacts.py`: Sincronización de agenda.
*   `src-tauri/tauri.conf.json`: (Futuro) Definición de ventanas WebView ocultas.
*   `docs/MOBILE_AUTOMATION_GUIDE.md`: Este archivo.
