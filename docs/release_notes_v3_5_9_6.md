# 🚀 Fina Ergen - Release Notes v3.5.9-6 (Primer Contacto Perfecto)

## 🌟 Resumen
Esta actualización se enfoca por completo en mejorar la experiencia de primer uso (First Boot) para usuarios novatos y en perfeccionar la portabilidad del empaquetado AppImage. Hemos logrado un entorno de instalación empático, transparente y guiado visualmente sin tocar la terminal.

## 🛠️ Cambios y Mejoras

### 🧠 Instalación Tolerante a la Ansiedad
- Se construyó una **barra de progreso simulada** para el instalador asíncrono. Los procesos de compilación extremadamente pesados de C++ (como `dlib` o `pytorch`) ahora engañan visualmente al usuario elevando la barra hasta un 99% a intervalos regulares. Esto previene que usuarios nuevos eliminen el proceso al ver que la barra queda congelada en 85%.

### 🌍 Instalador Bilingüe Universal
- Los avisos, pop-ups y dialogos de la primera configuración (Zenity) ya no están codificados en un idioma. El *sidecar* detector ahora lee la variable del sistema de Linux (`LANG`) e inyecta la ventana en **inglés o español** dinámicamente antes de arrancar Python.

### 📦 Corrección Estructural del AppImage
- Se resolvió un bug de enrutamiento por el cual el asistente de carga y los recursos se desorientaban en arquitecturas *squashfs*. Se añadieron directivas relativas de escape permitiéndole al motor buscar tanto en `/usr/lib/` como en el entorno emulado temporal de Tauri.

### 🔌 Detección Gráfica de Dependencias Faltantes
- Fina evolucionó la forma de alertar la ausencia de comandos críticos a nivel de Sistema Operativo (`nmap`, `vlc`, etc). En vez de imprimirlo silenciadamente a la consola, el `main.py` disparará un cartel gráfico (Zenity) brindando explícitamente el comando `sudo apt install` para guiar al usuario a obtener la experiencia total.

### 📖 Manual Dinámico y Contextual
- El backend en Rust (Tauri) fue actualizado. Al presionar el botón "Ayuda/Manual" desde el Frontend, Rust detectara el idioma de tu S.O. y decidirá si debe abrirte el PDF con la guía de usuario hispana (`Manual_Guia_Configuracion_Fina.pdf`) o la anglosajona (`Manual_Configuration_Guide_Fina_EN.pdf`).

---
Hecho con ❤️ en Argentina.
#FinaErgen #AIAsistente #Domotica #Linux
