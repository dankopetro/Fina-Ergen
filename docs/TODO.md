# Lista de Tareas Pendientes (Fina)

## Deuda Técnica (Prioridad Alta)
- [ ] **Apagado Limpio (Graceful Shutdown)**: 
  - Actualmente usamos `scripts/force_kill.sh` con `pkill -9` para cerrar la ventana Tauri desde Python. Esto es sucio y riesgoso.
  - **Solución Correcta**: Implementar un endpoint o evento en Tauri que escuche una señal de cierre desde el backend (Python) y ejecute `app.exit()` nativamente en Rust.
  
- [ ] **Orquestación de Procesos**:
  - El script `start_fina_rust.sh` lanza procesos en background y usa `pkill` global para limpiar.
  - **Solución**: Usar un gestor de procesos (como supervisord) o mejorar el script bash para atrapar señales (traps) y cerrar ordenadamente PID por PID.

## Mejoras de Funcionalidad
- [ ] **Feedback Visual en Tauri**:
  - Asegurar que el estado "Procesando" no se quede pegado si el backend falla. Implementar timeout en el frontend.
  
- [ ] **Integración de Audio**:
  - Investigar por qué `aplay` a veces bloquea el inicio. Migrar a una librería de reproducción de audio más moderna en Python si es posible.
