# Historial de Versiones (Changelog) - Fina Ergen

Todas las actualizaciones y cambios notables de este proyecto serán documentados en este archivo.

## 🚀 ¿Qué archivo descargar en cada Release?
A partir de las versiones `v3.5.x`, en la página de **Releases** encontrarás dos formatos de instaladores `.AppImage`:

1.  **fina-ergen_v..._amd64.AppImage (RECOMENDADO)**: Es una versión reempaquetada y optimizada. Tiene compresión **XZ** (pesa un 35% menos y se descarga más rápido) y contiene parches vitales de librerías (`libfuse2`) para garantizar que el ícono de la aplicación y la integración de escritorio funcionen perfectamente en sistemas modernos como Ubuntu 24.04+ y Linux Mint 22+.
2.  **fina-ergen_v..._x86_64.AppImage**: Es el archivo genérico y crudo generado por el compilador de Tauri. Si la primera opción falla en tu distribución, siempre puedes recurrir a este.

---

## [v3.5.8-13] - 2026-03-06 (Verificación Funcional y Saludo)

### Añadido
- **Verificación Funcional en Arranque**: El sistema ahora verifica que el clima y el aire acondicionado respondan antes de saludar, eliminando la espera por tiempo fijo.
- **Nuevo Saludo**: El saludo inicial ahora solicita amablemente el nombre del usuario para comenzar la interacción.

## [v3.5.8-12] - 2026-03-06 (Hotfix: TV Scripts y Monitor M8)
Correcciones críticas para la ejecución de scripts en plugins y la infraestructura Android del timbre.

### Arreglado
* **Monitor M8**: Se corrigió la ruta de búsqueda del script `start_hidden_system.sh` para que funcione correctamente desde la carpeta de plugins del usuario.
* **Plugins de TV/Deco**: Se arregló la verificación de scripts para el modelo Deco (sei800tc1), permitiendo que detecte los scripts con prefijo `deco_`.
* **Estabilidad**: Se unificaron las salidas de error (stderr) con la salida estándar (stdout) en el `PluginManager` para evitar bloqueos por tuberías llenas.

## [v3.5.8-8] - 2026-03-06 (Limpieza de Plugins y Sintaxis)
Esta versión corrige la detección de plugins de red, mejora la estabilidad de la mensajería y limpia errores de sintaxis en la interfaz principal.

### Arreglado
* **Detección de Plugins**: Los plugins ahora se detectan de forma recursiva (hasta 3 niveles de profundidad), lo que permite organizar carpetas por categorías.
* **Sintaxis de Interfaz**: Se consolidaron las llamadas de traducción multilínea en `App.vue` para evitar errores de compilación.
* **Control de TV**: Se mejoró la resolución de rutas de scripts en el plugin de TV para mayor compatibilidad con diferentes marcas (TCL, Deco Telecentro).
* **Timbre M8**: El monitor de timbre ahora inicia correctamente los servicios de Weston y Waydroid al detectar actividad.

### Añadido
* **Botón de Mensajería**: Acceso directo al Centro de Mensajería Unificado incluso sin celular vinculado.
* **Estilos**: Temperatura del Aire Acondicionado ahora se muestra en negrita (`font-black`) para mejor legibilidad.
* **Herramientas**: Script local de mantenimiento de sintaxis para desarrolladores.

## [v3.5.5] - 2026-03-03 (Edición de Internacionalización Completa)
Esta versión concluye la reestructuración completa de los archivos de localización, permitiendo que la interfaz cambie dinámicamente de idioma (Inglés/Español) sin valores estáticos en código.

### Añadido
* **Soporte Completo i18n**: Internacionalización nativa de todas las vistas, ajustes de TV, biometría, y el panel de Market de Plugins y nodos de red.
* **Actualización del paquete**: Bump de la versión base y dependencias pre-empaquetadas para compilación sólida en Debian/Ubuntu.

### Arreglado
* **Parches Quirúrgicos de Sintaxis HTML**: Resolución exhaustiva de etiquetas sin cierre, literales no terminados y atributos de clases duplicadas en Vue.
* **Componentes de UI de Seguridad**: Se reescribieron los widgets de escaneo de red que provocaban errores de parseo por cadenas incompletas.

## [v3.5.4-18] - 2026-02-22 (Edición "Tanque" Inteligente)
Esta versión perfecciona la portabilidad y la experiencia de primer usuario ("Out-of-the-box"), asegurando que Fina configure su propio cerebro sin intervención manual y facilitando la gestión de voces locales.

### Añadido
* **Unificación de Configuración (UI Priority)**: Fina ahora prioriza los ajustes realizados desde la Interfaz Visual (`Ajustes > Servicios & APIs`) sobre el archivo `config.py`. Los novatos pueden configurar Emails, APIs y Modelos sin tocar una línea de código.
* **Sección "Modelos & Heurísticas"**: Nuevo bloque en la UI para configurar rutas de modelos de voz (Piper) y reconocimiento (Vosk) de forma visual.
* **Multivocidad Dinámica**: El sistema ahora escanea automáticamente todos los archivos `.onnx` en la ruta configurada. Permite tener múltiples voces en una misma carpeta y rotar entre ellas con el comando de voz: *"Fina, cambiá la voz"*.
* **Estructura de Carpetas Automática**: Fina ahora autogenera todas sus carpetas esenciales (`voice_models`, `voice_profiles`, `temp_audio`, `plugins`, `Logs`) en `~/.config/Fina/` al primer arranque.
* **Auto-Bootstrap de IA (Full)**: Inclusión de `resemblyzer` en el instalador silencioso. Ahora la biometría de voz funciona en PCs nuevas sin necesidad de ejecutar comandos de terminal.

### Arreglado
* **📂 Estandarización Universal de Rutas**: Se realizó una revisión exhaustiva [EXHAUSTIVA] de todos los scripts (`tv_on`, `clima`, `scanners`, `plugins`) para asegurar que TODOS busquen y guarden ajustes en `~/.config/Fina/`.
* **🔧 Corección Crítica de Rutas (API)**: Se reparó un error que impedía a la API de Fina detectar correctamente la configuración del usuario dentro de AppImages.
* **Diagnóstico de Rutas Robusto**: Mejora en la detección y logueo de archivos de configuración (`channels.json`, `contacts.json`) para facilitar migraciones entre máquinas.
* **Sincronización de Entornos Virtuales**: Se unificó la ubicación del `venv` entre el Cerebro (Sidecar) y la UI en una ruta persistente única (`~/.config/Fina/venv`).
* **Optimización de Interfaz (UX)**: El botón del **Market de Plugins** ha sido movido a la sección de **Ajustes -> Nódulos**, su lugar lógico definitivo para la gestión de dispositivos.
* **Detección de Piper**: Mejora en la búsqueda de binarios de voz para mayor robustez en AppImages "Slim".
* **Persistencia de Canales**: Los scripts de escaneo (`scan_ultra_fast.py`) ahora guardan los resultados prioritariamente en la carpeta de configuración del usuario.

## [v3.5.4-14] - 2026-02-21 (Edición Visual y Estabilidad Crítica)
Esta actualización resuelve fricciones de portabilidad, automatiza servicios e introduce documentación de alta calidad.

### Añadido
* **Manual Visual de Usuario (10 Páginas)**: Guía práctica basada en 27 capturas reales de la interfaz. Ubicación: `docs/Manual_Usuario_Visual_Fina_v3.5.4.pdf` (Incluido en instaladores).
* **Manual Enciclopédico (20 Páginas)**: Tratado técnico avanzado del ecosistema Fina. Ubicación: `docs/Manual_Usuario_Fina_Ergen_v3.5.4.pdf`.
* **Auditoría de Servicios (Persistence Logs)**: Registro automático en `~/.config/Fina/fina_services.log` para servicios de fondo.

### Arreglado
* **Conflicto PYTHONHOME en AppImage**: Purga de variables de entorno en Rust para evitar el error "encodings" en entornos portables.
* **Auto-Arranque de Backend**: Los servicios de Python inician automáticamente junto con la aplicación.
* **Escaneo de Red Nativo**: Migración a comando Tauri de Rust para mayor velocidad y fiabilidad en el arranque.

## [v3.5.4-12] - 2026-02-21 (Edición Universal)
Esta versión marca un hito en el ciclo de vida de Fina Ergen, convirtiéndola en una aplicación 100% autodependiente e independiente de la ubicación donde se empaquete e instale.

### Añadido
* **Universalidad Total**: Fina ya no depende de rutas de código estáticas (como `/home/usuario/Descargas/Fina`). Ahora todas las rutas internas de ejecución (Python path, Root, Carpetas Temporales) se detectan de forma dinámica y se le comunican a la Interfaz Visual (UI) en el tiempo de arranque.
* **Persistencia Segura (User Data Separation)**: Los datos personales del usuario, el archivo maestro de configuración (`config.py`), los recordatorios, la biometría (firmas de voz) y los tokens OAuth de Tuya **han sido mudados a la carpeta `~/.config/Fina/`**. Esto permite que el usuario borre el programa o lo actualice usando un AppImage, y sus datos sigan estando perfectamente seguros e identificables.
* **Gestor de Plugins Avanzado (Dual Engine)**: Ahora Fina busca plugins en dos flujos en simuletáneo: su carpeta interna `/plugins` para dependencias del sistema, y la carpeta del usuario `~/.config/Fina/plugins`. Esto permite a los usuarios "tunear" o instalar nuevas extensiones (como las descargadas del Market), las cuales sobreviven a una actualización del binario principal.
* **Inteligencia en VENV (Entornos Virtuales)**: Un nuevo sistema de detección de entorno en el script de arranque (`lanzar_fina_simple.sh`). Busca tu motor de Python en modo descendiente, y si no tienes uno provisto, compila un entorno virtual salvaguardado de manera hermética.
* **Optimización Extrema de Recursos (IoT)**: Para los Plugins agresivos (como el Waydroid de Android usado para el Timbre Tuya), se instrumentó una regla de hierro. Si el usuario no tiene ninguna IP de timbre cargada en sus Configs, Fina no lanzará la máquina virtual Android de fondo. Esto salvaguardó el 25% de la carga base de RAM en computadoras ligeras!
* **Fast-Clima**: Reparaciones de sincronía de API. Ahora apenas Fina carga, se ejecuta su primer ciclo metereológico de OpenWeather y actualiza el Widget frontal, en lugar de que te salte "N/A" (A falta de un timeout del componente).

## [v3.5.4-11] a [v3.5.4-8] - 2026-02-21 (Refactor UI-Backend)
### Cambios
* Se comenzó el proceso paulatino de desconexión entre Tauri IPC Hard-shells (Comandos en Bash puros en la UI) y Arquitecturas de Larga Duración de API Rest.
* Integración del Backend Fina_API (`fina_api.py`) sirviendo JSON y estado unificado a todo el motor Tauri Frontend en simultáneo.

## [v3.5.4-7] a [v3.5.4-5] - 2026-02-21 (Mejoras Domóticas Base)
### Cambios
* Las arquitecturas de Plugins del Timbre y el Clima pasaron sus pruebas iniciales y se incorporaron al sistema dinámicamente como hilos estables desacoplados, previniendo cuelgues de las hebras maestras ante fallos en la conexión WiFi de tu red.

---
_Creado con amor. ¡Gracias por usar e instalar Fina!_
