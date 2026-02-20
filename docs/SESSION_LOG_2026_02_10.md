# 📅 Log de Sesión de Optimización (10 Feb 2026)

Esta sesión se centró en mejorar la **velocidad de respuesta de la TV y el Deco**, la **estabilidad de ADB** y la **corrección de la sintonización**.

## 🚀 TV TCL (Dormitorio - `tcl_32s60a`) - IP .10

1.  **Sintonización Turbo (Modo Ráfaga):**
    *   **Problema:** El envío "dígito por dígito" con pausas (`0.3s`) era lento y fallaba al enviar puntos decimales (ej: `80.1`).
    *   **Solución:** Se implementó una técnica de **Ráfaga de KeyEvents**. Ahora el script construye un único comando ADB con todos los códigos de tecla (`8 2 . 4`) y los envía de golpe.
    *   **Resultado:** Cambio de canal casi instantáneo y sin errores en decimales.
    *   **Archivo modificado:** `plugins/tv/tcl_32s60a/set_channel.py`

2.  **Soporte de --mac:**
    *   Se eliminó el envío forzado de `--mac` desde `App.vue` para comandos que no sean de encendido (`tv_on`, `tv_power`), evitando errores de argumentos no reconocidos.

## 📺 Deco Telecentro 4K (Living - `sei800tc1`) - IP .9

1.  **Velocidad Triplicada:**
    *   **Problema:** Cambiar a canales HD de 4 dígitos (ej: 1019) tardaba mucho.
    *   **Solución:** Se redujo el `sleep` entre dígitos de `0.3s` a **`0.1s`** en el helper de control remoto.
    *   **Resultado:** Sintonización mucho más ágil sin perder confiabilidad.
    *   **Archivo modificado:** `plugins/tv/sei800tc1/remote_helper.py`

2.  **Blindaje de Script:**
    *   Se agregó soporte opcional para el argumento `--mac` en `tv_on.py` para evitar crashes si la UI decide enviarlo.

## ⚡ Optimización del Sistema (ADB & Arranque)

1.  **Arranque Ultrarrápido (App.vue):**
    *   **Eliminado:** El ciclo agresivo de `adb kill-server` + `adb connect (all)` al iniciar la aplicación, que causaba bloqueos y mensajes de "TV no responde".
    *   **Nuevo Comportamiento:** Al arrancar, Fina solo intenta conectar suavemente (`timeout 2s`) a la **TV de la habitación activa** (ej: Living o Dormitorio). El resto se conecta bajo demanda.

2.  **Monitor de Timbre (Modo Ninja):**
    *   **Optimizado:** `doorbell_monitor.py` ya no intenta conectar a ADB en segundo plano constantemente. Solo activa la conexión ("Modo Ninja") cuando detecta efectivamente que el timbre está `Online`.

3.  **Cierre Maestro ("The Janitor"):**
    *   **Implementado:** Al cerrar Fina (`janitor.py`), se ejecuta una limpieza estratégica:
        1.  Mata cualquier proceso ADB zombie.
        2.  Inicia un servidor ADB limpio.
        3.  Pre-conecta en segundo plano a las TVs conocidas (`.9`, `.10`, `.11`).
    *   **Beneficio:** Deja el sistema "calentito" y listo para que el próximo arranque sea instantáneo.

## 📋 Canales y Configuración

1.  **Lista Completa:**
    *   Se actualizó `channels_telecentro.json` con la lista oficial completa de **205 canales** (incluyendo HD y 4K) scrapeada directamente de la web de Telecentro.
    *   Se agregaron variantes de nombres para facilitar la sintonización por voz/texto.

2.  **Correcciones de UI:**
    *   Arreglado el botón **HDMI** para usar el script correcto (`set_input_deco.py`) que cambia la TV activa a la entrada del Deco.
    *   Arreglado el click en la lista de canales para enviar solo el número (limpiando el nombre del canal).

---
**Estado Final:** Sistema estable, rápido y con ADB optimizado para no colgarse ni al inicio ni durante el uso.
