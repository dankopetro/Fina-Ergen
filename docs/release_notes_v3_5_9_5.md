# 🚀 Fina Ergen - Release Notes v3.5.9-5

## 🌟 Resumen
Esta actualización se enfoca en la estabilidad del hardware (cámara), la fluidez de la interfaz y la corrección de errores críticos en el empaquetado para asegurar una experiencia perfecta tras la instalación del paquete `.deb`.

## 🛠️ Cambios y Mejoras

### 🧭 Interfaz y Navegación
- **Panel de Control Maestro**: Se cambió la redirección del botón de **Ajustes**. Ahora, al entrar, el sistema te lleva directamente al **Hub de Dominios (Panel Maestro)** en lugar de abrir la pestaña de Inteligencia por defecto. Esto permite una visión global de la configuración de la casa al instante.
- **Versión Unificada**: Se sincronizó el número de versión `3.5.9-5` en el Core (Python), Frontend (Vue) y el manifiesto de Tauri.

### 📸 Biometría y Cámara
- **Detección Robustecida**: Se mejoró el script de entrenamiento facial (`train_face.py`) para escanear múltiples índices de cámara (0, 1, 2) y utilizar el backend **V4L2** en Linux, garantizando compatibilidad con webcams integradas en notebooks.
- **Modo Headless (GUI-Free)**: Se eliminó la dependencia de ventanas de OpenCV para el entrenamiento facial. Ahora el proceso se realiza íntegramente por consola con una **barra de progreso visual**, evitando errores de "Function not implemented" en sistemas sin librerías gráficas de desarrollo.

### 📦 Empaquetado y Distribución
- **Build Targets**: Se restauró la configuración de construcción para generar automáticamente paquetes **.deb, .rpm y AppImage** en GitHub Actions.
- **Resources**: Se aseguró la inclusión de `modismos.json` en el paquete para evitar fallos en la carga de frases regionales tras la instalación.

---
Hecho con ❤️ en Argentina.
#FinaErgen #AIAsistente #Domotica #Linux
