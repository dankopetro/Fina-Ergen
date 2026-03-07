---
description: Protocolo de Publicación de Releases en GitHub para Fina Ergen
---

Este protocolo es de cumplimiento OBLIGATORIO para el Agente AI (Antigravity) cada vez que el usuario solicite un lanzamiento o release en GitHub.

### 📜 REGLAS DE ORO DEL RELEASE
1.  **Estética con Iconos (Mandatorio)**: Todo release debe usar emojis para categorizar las secciones (ej: ✨ Añadido, 🩹 Arreglado, 🎙️ Audio, 🖥️ UI). No enviar texto plano aburrido.
2.  **Estructura de Contenido**: Las características nuevas y arreglos de bugs deben ir al principio del mensaje.
3.  **El Bloque de Descargas va AL FINAL**: La guía de qué archivo descargar (`amd64` vs `x86_64`) debe cerrar siempre la publicación.

### 🚀 BLOQUE DE DESCARGA ESTÁNDAR (COPIAR Y PEGAR AL CIERRE)

```markdown
---
### 🚀 ¿Qué archivo descargar en cada Release?
A partir de las versiones `v3.5.x`, en la página de **Releases** encontrarás dos formatos de instaladores `.AppImage`:

1.  **📦 fina-ergen_v..._amd64.deb**: Versión para sistemas basados en Debian (Ubuntu/Mint).
2.  **📦 fina-ergen-v...-1.x86_64.rpm**: Versión nativa para Fedora, CentOS, openSUSE y sistemas basados en RedHat.
3.  **📦 fina-ergen_v..._patched_amd64.AppImage (RECOMENDADO)**: Versión universal reempaquetada y optimizada. Tiene compresión **XZ** y parches vitales (`libfuse2`) para garantizar integración en sistemas modernos (Ubuntu 24.04+).
4.  **📦 fina-ergen_v..._amd64.AppImage**: Versión cruda del compilador Tauri. Usar si la opción parcheada falla.

---
_Creado con amor por el equipo de Fina Ergen. ¡Gracias por instalar!_ 🤖✨
```

### 🛠️ PROCEDIMIENTO TÉCNICO

#### 0. Sincronización de Versión (MANDATORIO)
Antes de crear el Tag o el Release, verifica que los siguientes archivos tengan exactamente el mismo número de versión (ej: `3.5.8-9`) y fecha/hora actualizada:
1.  **`src/App.vue`**: Constantes `version` (con fecha y hora) y `buildDate`.
2.  **`package.json`**: Campo `"version"`.
3.  **`src-tauri/tauri.conf.json`**: Campo `"version"`.
4.  **`CHANGELOG.md`**: Nueva entrada con la versión y descripción del Hotfix/Mejora.
5.  **`src-tauri/binaries/brain-x86_64...`**: Comentario de versión en la cabecera.
6.  **`Market Repository`**: Si se modificaron plugins en `.local_lab/Fina-Plugins-Market-Working/`, se DEBE hacer commit y push en dicho repositorio de forma independiente.

#### 1. Preparación y Validación
1.  Ejecutar `.local_lab/tools/fix_vue_syntax.py` sobre `src/App.vue`.
2.  Crear un archivo temporal (ej: `/tmp/notes.md`) con el contenido formateado y con iconos.
3.  Hacer el commit de los cambios finales.

#### 2. Etiquetado y Push
1.  Crear el tag correspondiente: `git tag v3.x.x-x`.
2.  Subir cambios y tags: `git push origin master && git push origin v3.x.x-x`.

#### 3. Publicación
1.  Lanzar el release: `gh release create v... --title "Fina Ergen v..." --notes-file /tmp/notes.md`.
