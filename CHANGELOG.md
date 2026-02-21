# Historial de Versiones (Changelog) - Fina Ergen

Todas las actualizaciones y cambios notables de este proyecto serán documentados en este archivo.

## 🚀 ¿Qué archivo descargar en cada Release?
A partir de las versiones `v3.5.x`, en la página de **Releases** encontrarás dos formatos de instaladores `.AppImage`:

1.  **fina-ergen_v..._amd64.AppImage (RECOMENDADO)**: Es una versión reempaquetada y optimizada. Tiene compresión **XZ** (pesa un 35% menos y se descarga más rápido) y contiene parches vitales de librerías (`libfuse2`) para garantizar que el ícono de la aplicación y la integración de escritorio funcionen perfectamente en sistemas modernos como Ubuntu 24.04+ y Linux Mint 22+.
2.  **fina-ergen_v..._x86_64.AppImage**: Es el archivo genérico y crudo generado por el compilador de Tauri. Si la primera opción falla en tu distribución, siempre puedes recurrir a este.

---

## [v3.5.4-15] - 2026-02-21 (Documentación Maestra y Estabilidad)
Esta versión se enfoca en la profesionalización del soporte al usuario y la blindaje total del entorno de ejecución.

### Añadido
* **Manual Enciclopédico de Usuario (20 Páginas)**: Creación de la documentación técnica definitiva en formato PDF Premium Dark. Cubre desde la filosofía del "Dominio Local" hasta la arquitectura profunda del Dual Engine y el desarrollo de Plugins. Ubicación: `docs/Manual_Usuario_Fina_Ergen_v3.5.4.pdf`.
* **Manual Visual de Usuario (10 Páginas)**: Guía práctica basada íntegramente en las 27 capturas de pantalla oficiales de la interfaz, explicando cada botón y widget del Dashboard. Ubicación: `docs/Manual_Usuario_Visual_Fina_v3.5.4.pdf`.
* **Auditoría de Servicios (Persistence Logs)**: Los procesos de fondo (`main.py` y `fina_api.py`) ahora escriben sus errores y logs directamente en `~/.config/Fina/fina_services.log`. Esto permite diagnosticar fallos en instalaciones `.deb` y `AppImage` sin necesidad de una terminal abierta.

## [v3.5.4-14] - 2026-02-21 (Parche Crítico AppImage)
Corrección de errores de ejecución en entornos portables y automatización de arranque.

### Arreglado
* **Conflicto PYTHONHOME en AppImage**: Se implementó una purga de variables de entorno (`PYTHONHOME` y `PYTHONPATH`) en el núcleo de Rust antes de invocar cualquier comando de Python. Esto soluciona el error fatal "No module named encodings" que impedía el escaneo de red en AppImages.
* **Auto-Arranque de Backend**: El instalador `.deb` y el `AppImage` ahora lanzan automáticamente todos los servicios de Python (Cerebro y API) al abrir la aplicación, eliminando la necesidad de scripts de lanzamiento externos.
* **Comando Nativo de Red**: Migración del escaneo de red a un comando nativo de Tauri (`scan_network_devices`), eliminando la dependencia de llamadas REST durante la fase crítica de arranque.

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
