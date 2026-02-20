# 🚀 Actualización Importante Fina - Febrero 2026

## 1. 🧠 Nueva Inteligencia de Control de TV
Fina ahora posee "Conciencia de Estado" para decidir qué televisor controlar, eliminando la necesidad de comandos repetitivos.

### Lógica de Decisión Automática:
1.  **Mención Explícita:** Si dices *"Prendé la tele del cuarto"*, Fina obedece sin dudar.
2.  **Detección de Estado (ADB):** Si dices *"Cambiá de canal"* y solo la TV del Dormitorio está encendida, Fina asume automáticamente que le hablas a esa.
3.  **Inferencia Contextual (Fútbol/Canales):** Si pides *"Poné el partido"* o *"Poné Telefe"* y ninguna TV responde, Fina intentará activar el **Deco Telecentro** en la TV principal.
4.  **Detección Visual (Preparada):** El sistema está listo para usar una cámara y detectar en qué habitación estás (actualmente pregunta si tiene dudas).
5.  **Pregunta de Desempate:** Si hay varias TVs prendidas y no fuiste específico, Fina preguntará: **"¿En cuál tele? ¿Living o Dormitorio?"**.

### 🇦🇷 Argentinismos y Alias Agregados
Ahora puedes hablar con naturalidad:
*   **Verbos:** "Poné", "Cambiá", "Bajá", "Subí".
*   **Canales Rápidos:**
    *   "Poné las **noticias**" -> TN (Canal 3/81.1)
    *   "Poné **fútbol**" -> TyC Sports (Canal 106/82.5)
    *   "Poné **deportes**" -> TyC Sports
    *   "Poné **película**" -> Star Channel
    *   "Poné **música**" -> Music Top

---

## 2. 🛠️ Nuevas Herramientas del Sistema (Utils 2.0)
Se han eliminado las funciones "de juguete" (dummy) y se han reemplazado por implementaciones reales y funcionales.

### 📝 Organización Personal (Persistente)
*   **Notas Reales:** `create_note("texto")` guarda notas en `user_data.json` que no se borran al reiniciar.
*   **Recordatorios:** `add_reminder("tarea")` guarda recordatorios pendientes.
*   **Backup:** `backup_files` crea un archivo `.zip` comprimido con todo el código de Fina en `~/Fina_Backups`.

### 🌐 Red y Conectividad
*   **Escaneo WiFi:** `scan_wifi` muestra las redes disponibles (requiere `nmcli`).
*   **IP Pública:** `get_public_ip` te dice tu IP real de internet (útil para acceso remoto).
*   **Escaneo de Puertos:** `scan_ports` verifica puertos abiertos en un dispositivo.

### 🎨 Creatividad y Multimedia
*   **Generación de Imágenes:** `generate_image("un gato azul")` usa DALL-E 3 (si hay clave de OpenAI) y abre la imagen en el navegador.
*   **Conversión de Moneda:** `convert_currency` consulta tasas de cambio reales en tiempo real.
*   **Lectura de PDF:** `read_pdf` extrae texto de archivos PDF para leértelos.

### ⏱️ Utilidades Varias
*   **Temporizador Real:** `start_timer(10)` te avisa realmente a los 10 minutos (antes no hacía nada).
*   **Buscador de Archivos:** `find_file("nombre")` busca archivos en tu carpeta personal.
*   **Portapapeles:** `get_clipboard` puede leer lo que copiaste en el sistema (requiere `xclip`).

---

## 3. Comandos de Voz Nuevos para el Manual
Agrega estos a la guía de usuario:

| Comando Ejemplo | Acción |
| :--- | :--- |
| "Poné las **noticias**" | Pone TN en la TV activa o Deco. |
| "Cambiá al canal **fútbol**" | Pone TyC Sports. |
| "Hacé un **backup** de los archivos" | Crea copia de seguridad del proyecto. |
| "Generá una imagen de un **paisaje futurista**" | Crea arte con IA. |
| "¿Cuál es mi **IP pública**?" | Dice tu dirección de internet. |
| "Buscá el archivo **presupuesto.pdf**" | Encuentra archivos en tu PC. |
| "Avisame en **15 minutos**" | Inicia un temporizador real. |
| "¿Cuánto son **100 dólares** en pesos?" | Convierte moneda en vivo. |

---

## 4. 🛡️ Mejoras de Estabilidad y Contexto (Febrero 2026 - Update 2)

### 🚫 Protección contra Apagado Accidental
Se ha implementado una nueva capa de inteligencia contextual para evitar malentendidos lingüísticos peligrosos:
*   **Antes:** Decir *"Dormitorio"* a veces se confundía con *"Dormir"* (comando de apagado o buenas noches).
*   **Ahora:** Fina entiende que "Dormitorio", "Living", "Cocina", etc., son **lugares**.
    *   Si dices solo el nombre de la habitación, Fina responderá: **"¿Qué quieres que haga en el dormitorio?"** en lugar de iniciar la secuencia de apagado.

### 📺 Robustez en Control de TV (ADB Tuning)
Hemos ajustado los tiempos de espera del protocolo ADB para redes domésticas con latencia variable:
*   **Timeouts Extendidos:** Se aumentó la tolerancia de conexión de 2 a 4 segundos. Esto evita que Fina pregunte *"¿En cuál tele?"* innecesariamente cuando la TV tarda en responder al despertar.
*   **Clarificación Técnica de Encendido/Apagado:**
    *   **ENCENDER (Wake-on-LAN):** Fina usa la dirección física **MAC** de la TV. Funciona incluso si la TV está en reposo profundo (sin IP).
    *   **APAGAR (ADB/IP):** Fina usa la dirección **IP** y requiere que el sistema operativo de la TV (Android TV) esté corriendo.
    *   **Tip Pro:** Para mayor fiabilidad al apagar, se recomienda controlar el **Decodificador** (si tiene HDMI-CEC), ya que suele mantener mejor la conexión de red que la TV.

### ☁️ Clima Preciso (La Plata)
*   Se corrigió el error que impedía obtener el pronóstico de "Mañana".
*   Configuración forzada a **La Plata** (ID 3432043) para evitar ambigüedades con Buenos Aires.

### 🧹 Cierre Limpio de Aplicación ("Anti-Zombies")
*   Se reescribió el núcleo en **Rust** (`lib.rs`) para interceptar el evento de cierre de ventana (`X`).
*   Ahora, al cerrar la ventana principal de Fina, el sistema garantiza la terminación ("kill") de todos los subprocesos de Python (reconocimiento de voz, servidores, etc.), evitando que Fina "siga escuchando" en segundo plano.

---

## 5. 🛡️ Suite de Protección CENTINELA
El antiguo sistema "Sentinel" ha sido evolucionado a **CENTINELA**, una suite de monitoreo táctica y seguridad activa.

### 📊 Monitoreo de Hardware Real
Fina ahora reporta métricas exactas del sistema anfitrión:
*   **CPU**: Carga y frecuencia en MHz.
*   **RAM**: Porcentaje y GB exactos (Usado/Total).
*   **RED**: Tráfico entrante y saliente en Megabytes.

### 🔍 Escaneo de Intrusos (Real)
Ya no es una simulación visual. El comando `scan` en la Terminal Centinela dispara un escaneo de red utilizando **NMAP** para detectar dispositivos activos en la red local.

### 💻 Terminal Táctica
Se ha habilitado la interacción real con el núcleo de seguridad. Comandos como `stats`, `logs`, `scan` y `block` permiten administrar la seguridad de la casa directamente desde la interfaz de Fina.
