# Arquitectura de Empaquetado y Ecosistema de Plugins: Fina Ergen

Este documento detalla la estrategia de distribución para la versión de producción de Fina Ergen, enfocándose en la modularidad y facilidad de uso.

## 1. Distribución de la Aplicación Base

Para el sistema operativo Linux, se han seleccionado dos formatos principales para garantizar la máxima compatibilidad y funcionalidad:

### A. Paquete Debian (.deb) - Prioritario
*   **Público Objetivo**: Usuarios de Debian, Ubuntu, Linux Mint y derivados.
*   **Ventaja Clave**: Gestión de dependencias automática. El paquete declarará como requisitos: `nmap`, `kdocker`, `xdotool`, `python3`, `adb` y `ffmpeg`.
*   **Integración**: Instalación limpia en directorios de sistema (`/usr/bin`, `/usr/share/fina`).

### B. AppImage - Secundario
*   **Público Objetivo**: Distribuciones tipo Arch, Fedora o usuarios que prefieren no instalar en sistema.
*   **Limitación**: El usuario deberá asegurar manualmente que las herramientas de infraestructura (`waydroid`, `nmap`, etc.) estén instaladas en su host.

---

## 2. El Ecosistema de Plugins (.fplugin)

Para mantener a Fina Ergen ligera y expandible, los plugins se distribuirán de forma independiente al ejecutable principal.

### El Formato .fplugin
Un archivo `.fplugin` es técnicamente un contenedor comprimido (ZIP o TAR) con una estructura estandarizada:

```text
nombre-del-plugin.fplugin/
├── manifest.json       # Cerebro del plugin (metadatos)
├── icon.png            # Icono que se mostrará en la UI de Fina
├── logic/              # Directorio de scripts Python
│   ├── monitor.py      # Script de vigilancia continua
│   └── actions/        # Scripts para acciones específicas (ej: hangup)
└── resources/          # Activos locales (sonidos, imágenes internas)
```

### El Archivo manifest.json
Ejemplo de estructura para el plugin de Timbre:
```json
{
  "id": "com.fina.doorbell-tuya",
  "name": "Timbre Tuya V5",
  "version": "1.0.0",
  "author": "Claudio",
  "description": "Monitoreo y atención automática de timbres Tuya vía Waydroid",
  "entry_point": "logic/monitor.py",
  "requirements": {
    "waydroid_app": "com.tuya.smart",
    "host_tools": ["nmap", "kdocker"]
  },
  "ui_hooks": [
    {
      "tab": "dashboard",
      "button_label": "Probar Timbre (Manual)",
      "action": "logic/actions/test_sequence.py"
    }
  ]
}
```

---

## 3. Experiencia de Usuario (UX)

### Instalación de Plugins
1.  **Descarga**: El usuario descarga el archivo `.fplugin` desde una fuente oficial o comunitaria.
2.  **Importación**:
    *   **Opción A**: Botón "Instalar Plugin" en la configuración de Fina que abre un selector de archivos.
    *   **Opción B**: Arrastrar y soltar (Drag & Drop) el archivo sobre la ventana principal de Fina.
3.  **Activación**: Fina valida la integridad del archivo, lo descomprime en `~/.local/share/fina/plugins/` y reinicia el Cerebro Ergen para cargar las nuevas funciones inmediatamente.

### Actualizaciones
*   Fina podrá verificar la versión en el `manifest.json` y compararla con un repositorio en línea, permitiendo actualizaciones de plugins con un solo clic sin necesidad de actualizar toda la aplicación.

---

## 4. Hoja de Ruta Tecnológica

1.  **Fase 1 (Actual)**: Desarrollo de plugins en carpetas locales para pruebas.
2.  **Fase 2**: Implementación del cargador dinámico de `manifest.json` en el Cerebro Ergen.
3.  **Fase 3**: Creación del "Plugin Manager" en la interfaz Vue para gestionar la activación/desactivación.
4.  **Fase 4**: Empaquetado final de Fina Base en formato `.deb`.
5.  **Fase 5: Fina-Ergen (Adolescent)**:
    *   **Concepto**: Transición de Fina Ergen (Renacimiento) a Fina-Ergen (Adolescencia/Crecimiento).
    *   **Mejoras**: Interfaz hiper-moderna con widgets avanzados, mayor fluidez en la IA conversacional y ecosistema de plugins autogestionado.
    *   **Objetivo**: Expandir la inteligencia de Fina para que sea proactiva, no solo reactiva.
