# Configuración de Timbre Inteligente (Tuya + Waydroid)

Este documento detalla la implementación actual para interceptar, visualizar y responder al timbre inteligente Tuya usando Linux.

## Componentes
1.  **Waydroid**: Contenedor Android que ejecuta la App "Tuya Smart".
2.  **Weston**: Compositor Wayland necesario para ejecutar Waydroid (oculto/minimizado).
3.  **ADB (Android Debug Bridge)**: Para controlar la app (toques, swipes) y lanzar acciones.
4.  **PulseAudio/Pipewire**:
    *   `module-null-sink`: Crea un "Micrófono Virtual" (`FinaVoice`) para que Fina hable al timbre.
    *   `module-loopback`: Crea un "Cable" para que escuches lo que dice la visita.
5.  **Scrcpy**: Para visualizar el video del timbre en una ventana flotante.

## Scripts Principales
*   **`scripts/start_hidden_system.sh`**:
    *   Inicia Weston minimizado.
    *   Inicia Waydroid dentro de Weston.
    *   Prepara el entorno gráfico.
*   **`scripts/doorbell_monitor.py`**:
    *   Vigila la IP del timbre (`192.168.0.5`).
    *   Detecta cuando pasa de Offline -> Online (al presionar el botón).
    *   Secuencia de Atención:
        1.  Conecta ADB.
        2.  Abre App Tuya.
        3.  Presiona notificación/botón de llamada (Coords: `325, 157` o `KEYEVENT 5`).
        4.  Lanza ventana de video (`scrcpy`) **solo si hay éxito**.
        5.  Enruta audio.
        6.  Activa PTT (Swipe en `228, 643`) y Fina habla.
        7.  Deja la llamada abierta.
*   **`scripts/hangup_doorbell.py`**:
    *   Ejecutado por voz ("Corta el timbre").
    *   Mata la app Tuya (`am force-stop`) para colgar inmediatamente.
    *   Cierra scrcpy.

## Coordenadas Clave (Resolución Waydroid Default)
Las coordenadas son críticas y dependen de la resolución de Waydroid.
*   **Notificación Superior**: `325, 157`
*   **Botón Hablar (PTT / Microfono)**: `228, 643` (Centro-abajo)
*   **Botón Colgar (Rojo)**: `225, 710` (Abajo-centro)

## Flujo de Audio
1.  **Fina Habla** -> TTS -> Sink `FinaVoice`.
2.  **Waydroid** -> Captura de `FinaVoice.monitor` (Default Source).
3.  **Visita Habla** -> App Tuya -> Salida Waydroid.
4.  **Tú Escuchas** -> Salida Waydroid -> `module-loopback` -> Tus Parlantes.

## Solución de Problemas Comunes
*   **Loop de llamadas**: El script tiene un cooldown de 60s que se activa *al finalizar* la llamada.
*   **Fina no se escucha**: Verificar que `pactl set-default-source FinaVoice.monitor` esté activo o que Waydroid esté usando el input correcto.
*   **Video falla ("Reconectar")**: Conflicto de red. Asegurar que ningún celular esté viendo la cámara simultáneamente (Modo Avión en celulares).
