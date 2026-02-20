# Tareas Críticas Pre-Lanzamiento (Must Have)
Antes de empaquetar la aplicación para distribución (v1.0 Pública), se deben resolver los siguientes puntos para garantizar que Fina sea multiusuario y no esté hardcodeada para "Claudio".

## 1. Onboarding de Primer Uso (First Run Experience)
- [ ] Crear pantalla de bienvenida al detectar que `settings.json` está vacío o incompleto.
- [ ] Solicitar **Nombre de Usuario** del sistema (y validarlo con `os.getlogin()`).
- [ ] Guía paso a paso para configurar las APIs críticas:
    - OpenAI / Mistral (Inteligencia)
    - ElevenLabs (Voz)
    - Tuya / SmartLife (Dispositivos)
- [ ] Botón de "Auto-Detectar Hardware" inicial.

## 2. Eliminación de Hardcoding
- [ ] Revisar todos los scripts Python en `iot/` y `plugins/` buscando strings "Claudio" o rutas absolutas a `/home/claudio/`.
- [ ] Reemplazar rutas fijas por `os.path.expanduser("~")` o relativas al proyecto.
- [ ] Asegurarse de que `settings.json` no venga pre-cargado con mis datos personales (crear un `settings.template.json`).

## 3. Asistente de Configuración
- [ ] Agregar tooltips o enlaces de ayuda en la sección de Ajustes para que el usuario sepa dónde conseguir cada API Key (ej: "¿Dónde encuentro mi ID de ElevenLabs?").
- [ ] Validar permisos (micrófono, cámara, dialout para Arduino) y guiar al usuario si faltan (ej: `sudo usermod -aG dialout $USER`).

## 4. Validación Biométrica Universal
- [ ] Asegurar que `fprintd` y `cv2` funcionen con el usuario actual del sistema, no hardcodeado. (Parcialmente hecho, revisar casos de borde).
- [ ] Manejo de errores amigable si el usuario no tiene hardware biométrico (ej: no tiene lector de huellas).
