# Roadmap Fina 2.0: Arquitectura Robusta y Modular

## 1. Reingeniería del Frontend (Rust/Tauri)
El estado actual es un híbrido frágil donde Python gestiona la lógica y Rust es solo una ventana "tonta". El objetivo es una integración nativa.

- [ ] **Comunicación Real (IPC)**: 
  - Abandonar el polling HTTP (`GET /api/state`).
  - Implementar **Tauri Commands** para que el frontend invoque funciones del backend directamente.
  - Usar **WebSockets** o **Sidecar** para eventos en tiempo real (ej: visualizador de onda de audio fluido).
- [ ] **Gestión de Ciclo de Vida**:
  - Rust debe ser el proceso PADRE ("The Host").
  - Rust lanza el backend Python como un "Sidecar" (subproceso) al iniciar y LO MATA al cerrar la ventana.
  - Esto elimina la necesidad de `start_fina_rust.sh` y scripts de `pkill` suicidas.
- [ ] **Interfaz Reactiva**:
  - Reescribir el frontend en React/Vue + Tailwind (o Leptos si somos puristas de Rust) para animaciones fluidas y menor consumo.

## 2. Sistema de Plugins (Fina Modular)
Actualmente, cada nueva función requiere editar `main.py` y `intents.json`. Esto es insostenible.

- **Arquitectura Propuesta**:
  - Carpeta `plugins/`. Cada plugin es una subcarpeta con:
    - `manifest.json`: Define comandos, intents y dependencias.
    - `plugin.py`: Código Python con una clase estándar `FinaPlugin`.
  - **Carga Dinámica**: Al arrancar, Fina escanea `plugins/`, carga los intents en memoria y registra los handlers.
  - **Ventaja**: Puedes agregar "Control de Luces" o "Precios de Crypto" simplemente soltando una carpeta, sin tocar el núcleo.

## 3. Refactorización del Núcleo (Core)
- [ ] **Separación de Responsabilidades**:
  - `AudioEngine`: Singleton para entrada/salida de audio (evitar conflictos alsa).
  - `IntentManager`: Motor agnóstico que recibe texto y despacha eventos a plugins.
- [ ] **ContextAwareness**: Memoria a corto plazo de la conversación (para no repetir "Hola").

## 4. Domótica e IoT (Integración Local Premium)
- [ ] **Timbre Tuya Local**:
  - Implementar monitoreo vía `tinytuya` usando la **Local Key** y la **IP Estática**.
  - Evitar notificaciones de nube para una latencia cero.
  - Sincronizar el evento de "botón presionado" con una respuesta inmediata de Fina ("Alguien toca la puerta, Claudio").
- [ ] **Control de Dispositivos**: Crear el primer Plugin oficial usando los datos de IoT locales.

---

## Pasos para la Migración a Rust Robusto (Plan de Acción)
1. **Crear nuevo proyecto Tauri limpio**.
2. Configurar `tauri.conf.json` para definir `python-backend` como binario sidecar.
3. Escribir lógica en Rust (`main.rs`) para orquestar el inicio/fin del proceso Python.
4. Exponer eventos `on_voice_detected`, `on_intent` desde Python a Rust vía Stdin/Stdout o Socket local.
5. Migrar la UI actual a este nuevo esqueleto.
