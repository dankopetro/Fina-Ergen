# Tareas Pendientes Post-Sesión (15/02/2026)

## 📱 Funcionalidad Móvil (Celular)
- [ ] **Integración WhatsApp Web:** Planificar módulo de navegador embebido para setup inicial y evitar dependencias de ADB para mensajería.
- [ ] **Leer E-mails:** Reactivar `read_unread_emails` (actualmente está mockeado o desactivado en `App.vue`/`utils.py`). Necesitamos credenciales de Gmail/IMAP configuradas en `settings.json`.

## 🗣️ Interfaz y Personalidad
- [ ] **Saludo Variable:** Corregir el saludo inicial en el panel (UI) para que diga "Buenas tardes" o "Buenas noches" según la hora, no solo "Buenos días". Revisar lógica en `App.vue` (posiblemente hardcodeado o mal calculado).
- [ ] **Versión:** Actualizar número de versión en todos los archivos (`App.vue`, `package.json`, `MANUAL_DE_USUARIO.md`) a la nueva versión estable.

## 🛠️ Mantenimiento
- [ ] **Validación Timbre:** Confirmar que el fix de `doorbell-ring` funciona correctamente en escenario real.
