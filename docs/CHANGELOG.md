# Changelog - Fina Asistente

## [3.3.0] - 2026-02-17: SMS Invisible y Hub Universal
**Estado:** 🚀 Milestone (Engineering Upgrade)

### Nuevas Funciones (Features)
- **Universal Mobile Hub**: Motor de autodescubrimiento de hardware. Fina ahora detecta automáticamente el protocolo de envío según el fabricante (Motorola, Samsung, etc.).
- **Mensajería Screen-Off**: Envío de SMS mediante inyección Binder directa. Permite enviar mensajes sin encender la pantalla ni abrir la app de mensajes en el móvil.
- **Identidad Ergen Consolidada**: Purga completa de referencias a "Phoenix" en el núcleo (incluyendo el sidecar binario de Tauri), unificando todo el proyecto bajo el ecosistema Ergen.
- **Manejo Inteligente de Espacios**: Los mensajes con espacios ahora se envían íntegros mediante el uso de argumentos atómicos en el comando `service call`.

### Correcciones (Bugfixes)
- **Sidecar Path Fix**: Corregida la ruta del binario `brain` que apuntaba a una carpeta de pruebas antigua.
- **JSON Shell Sync**: Sincronización perfecta entre el script de Python y la interfaz Vue mediante el modo "Silent" para evitar errores de parseo en el frontend.
- **SubID Auto-Detection**: El sistema ahora identifica correctamente la SIM activa para evitar rechazos del kernel de Android.

---

## [3.2.1] - 2026-02-14: Integración Móvil y Modal de Comunicación
**Estado:** 🚀 Release (Ergen Upgrade)

### Nuevas Funciones (Features)
- **Modal de Comunicación**: Nueva interfaz unificada para enviar SMS e iniciar llamadas sin salir de Fina.
- **Selección de Dispositivo Principal**: Sistema de "Estrellas" en *Ajustes > Nódulos* para marcar tu dispositivo favorito.
- **Vínculo Dinámico**: Los botones de Agenda ahora muestran el nombre del dispositivo conectado (ej: "iPhone Claudio").
- **ADB Integrado**: Soporte completo para comandos ADB (`send_sms`, `make_call`) mediante `mobile_hub.py`.

### Correcciones (Bugfixes)
- **Tauri v2 Window Management**: Migración a `appWindow` para minimizar/cerrar correctamente en Linux.
- **Tauri Detection**: Lógica `window.__TAURI_INTERNALS__` para diferenciar Dev/Prod.
- **Estabilidad de Red**: Mejor manejo de errores al conectar con dispositivos móviles.

---

## [2.8.7 RC] - 2026-02-05: Estabilización Final y Versión RC
**Estado:** 🚀 Release Candidate (Candidata a Lanzamiento)

### Corregido (Bugfixes)
- **Calidad de Audio (Vosk/Biometría)**: Corregido el error de captura de audio (`np.frombuffer` con `float32` vs `int16`). La confianza del reconocimiento subió de 0.45 a 0.95+.
- **Apagado Atómico**: Implementado `scripts/janitor.py` (Python + psutil) que liquida procesos huérfanos de Weston, Waydroid y WebKit.
- **Terminal "Zombi"**: Corregido mediante el uso de `stty sane` y `reset` al finalizar, devolviendo el control al usuario de inmediato.
- **Ruido al Inicio**: Eliminado el chasquido (pop) de audio durante la inicialización del motor TTS.
- **Rutas de TV**: Modularización total de plugins de TV (TCL/Surrey) y corrección de rutas relativas.

### Mejoras (Improvements)
- **Arranque Proactivo**: Fina ahora verifica y reporta el estado de la conexión con la TV al iniciar.
- **Cortesía en Plugins**: Todos los plugins (Clima, TV) ahora ofrecen feedback verbal inmediato ("Subiendo volumen", "Cambiando canal").
- **Identidad**: Mejorado el reconocimiento de frases de identidad ("Soy Claudio", "Abre sesión").

---

## [2026-01-24] - Batalla contra el Ruido y Estabilización

### Corregido (Bugfixes)
- **Bloqueo por "Procesando" Eterno**: Se implementó un contador de fallos consecutivos en `main.py`. Tras 3 intentos fallidos de entender un comando (o ruido), Fina se duerme automáticamente ("Estoy aquí por si me necesitas").
- **Ruido de Ventilador**: Se añadió un filtro de longitud mínima (< 5 caracteres) para ignorar ruidos cortos captados por Vosk sin disparar la IA.
- **Biometría de "Adiós"**: Se restauró la distinción entre "Adiós" (Cerrar Programa - Requiere Admin) y "Hasta Luego" (Dormir - Libre).
- **Entrenamiento de Voz**: Se creó y ejecutó `train_voice.py` para regenerar el perfil biométrico de "Claudio".
- **Script de Inicio (Rust)**: Se corrigió `start_fina_rust.sh` ya que NO lanzaba `main.py`. Ahora orquesta API + Backend + Frontend.
- **Apagado (Shutdown)**: Se implementó un script de fuerza bruta `scripts/force_kill.sh` para asegurar que la ventana de Rust se cierre al salir, solucionando (parcialmente) el problema de ventanas zombies.

### Mejoras (Improvements)
- **Wake Word**: Se añadieron alias fonéticos ("china", "tina") para mejorar la activación por voz.
- **Logging**: Se limpió la salida de logs para facilitar el diagnóstico.
- **Crash Main**: Se arregló un crash crítico donde `command.lower()` fallaba si `listen()` retornaba Timeout (`None`).

### Estado Actual
- Fina escucha, entiende y ejecuta comandos.
- Biometría funcional.
- Interfaz gráfica se lanza correctamente junto al cerebro.
- **Pendiente**: El cierre de la ventana gráfica es "sucio" (killall) y debería ser nativo.
