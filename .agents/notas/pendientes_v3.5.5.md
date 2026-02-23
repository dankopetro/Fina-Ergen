# 📋 Pendientes para Fina Ergen v3.5.5

## 🔐 1. Autorización en PCs sin huella digital (PRIORITARIO)

**Contexto:** Danko no tiene lector de huella. Al pedir autorización, Fina habla pero la UI
no muestra ningún campo para ingresar la contraseña. El usuario no sabe dónde escribir.

**La UI se colgó** mientras la voz seguía funcionando → bug de estado de UI a investigar.

**Soluciones a implementar (una o todas):**

### A. Campo de contraseña visual en la UI
- Cuando Fina pide autorización, mostrar un campo de texto `<input type="password">`
  visible y enfocado automáticamente en la pantalla.
- Después de ingresar:
  - ✅ Si es correcta → campo desaparece, Fina confirma y ejecuta.
  - ❌ Si es incorrecta → mostrar mensaje de error rojo y limpiar el campo.
- El campo debe desaparecer solo si el usuario no interactúa en ~30 segundos.

### B. Autorización por voz
- Fina pregunta: *"¿Cuál es tu contraseña?"*
- El usuario la dice en voz alta (con sigilo si es necesario).
- Reconocimiento de voz → comparación.
- ⚠️ Consideración de seguridad: la voz puede escucharse.

### C. Autorización por rostro (cámara de la PC)
- Si la PC tiene cámara, Fina puede usar face_recognition para verificar identidad.
- Similar a la biometría de voz pero visual.
- Ventaja: no requiere escribir ni hablar.

---

## 🐛 2. Bug: UI se congela durante autorización
- La UI de Fina se "colgó" mientras la voz seguía funcionando.
- Investigar si es un problema de bloqueo del hilo principal esperando respuesta de
  autorización sin timeout de UI.
- Asegurarse de que el estado de la UI se actualice aunque el backend esté esperando input.

---

## 📦 3. Pendiente de build (no compilar hasta confirmar que todo funciona bien)
- Quitar `tv`, `doorbell` y `clima` del bundle del .deb (ya modificado en tauri.conf.json).
- Esos plugins van al **Marketplace de Plugins**, no al instalador base.
- Solo van en el .deb los plugins **core**: `biometria`, `system`, `web_apps`.
- Compilar, probar, y si todo OK → hacer release **v3.5.5**.

---

## ✅ Estado actual (logros de la sesión 23/02/2026)
- [x] Puerto 18000 migrado en todo el proyecto
- [x] Fina habla (Piper TTS funcional con libs bundled)
- [x] Biometría de voz cargando correctamente
- [x] Instalador Zenity con progreso visual
- [x] Plugins TV, Clima y Doorbell EXCLUIDOS del bundle (corrección en tauri.conf.json)
- [ ] Autorización por contraseña/voz/rostro en UI → **PENDIENTE**
- [ ] Bug UI congelada durante auth → **PENDIENTE**
- [ ] Build y release v3.5.5 → **PENDIENTE**
