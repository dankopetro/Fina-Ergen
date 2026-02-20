# Mejoras Futuras para Fina Assistant (Versión Rust/Tauri)

Este documento detalla las propuestas para fortalecer y profesionalizar la aplicación nativa de Fina.

## 1. Robustez del Sistema (Autocuración)
*   **Guardián de Procesos:** Implementar lógica en Rust que monitorice `fina_api.py` y `main.py`.
*   **Reinicio Automático:** Si un proceso de Python falla, la aplicación de Rust debe reiniciarlo de forma transparente para el usuario.

## 2. Integración con el Escritorio Linux
*   **System Tray (Área de Notificación):** Icono en la barra de tareas para control rápido, cambio de estado y acceso a ajustes.
*   **Global Hotkeys:** Atajo de teclado universal (ej. `Super + F`) para despertar a Fina desde cualquier lugar sin usar la palabra de activación.
*   **Notificaciones Nativas:** Informar sobre eventos importantes (errores, actualizaciones, recordatorios) usando el sistema de notificaciones de Linux.

## 3. Biometría y Seguridad Premium
*   **Puente Nativo fprintd:** Gestionar la huella dactilar directamente desde Rust/DBus en lugar de llamadas a shell.
*   **Ventanas de Autenticación:** Mostrar diálogos nativos de "Confirmar Identidad" con una estética similar a la del sistema operativo.

## 4. Experiencia de Usuario (UI/UX)
*   **Visualizador de Voz en Tiempo Real:** Animaciones fluidas en la interfaz que reaccionen a la intensidad del sonido captado por el micrófono.
*   **Gestión de Entorno Virtual:** Detección y activación automática del `.venv` de Python al arrancar el binario.
*   **Instalador de Dependencias Integrado:** Verificación de librerías faltantes al inicio con opción de reparación guiada.

## 5. Expansión IoT
*   **Control de Aires Acondicionados:** Integración de protocolos Tuya, Midea o Broadlink para gestionar el clima del hogar por voz.

---
**Documento de referencia para el desarrollo de la Fase 2.**
