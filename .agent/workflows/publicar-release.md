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

1.  **📦 fina-ergen_v..._amd64.AppImage (RECOMENDADO)**: Versión reempaquetada y optimizada. Tiene compresión **XZ** (pesa un 35% menos y descarga más rápido). Contiene parches vitales (`libfuse2`) para garantizar que el ícono de la aplicación y la integración de escritorio funcionen perfectamente en sistemas modernos como **Ubuntu 24.04+** y **Linux Mint 22+**.
2.  **📦 fina-ergen_v..._x86_64.AppImage**: Versión genérica y cruda generada por el compilador de Tauri. Si la primera opción falla en tu distribución, siempre puedes recurrir a esta.

---
_Creado con amor por el equipo de Fina Ergen. ¡Gracias por instalar!_ 🤖✨
```

### 🛠️ PROCEDIMIENTO TÉCNICO
1.  Crear un archivo temporal (ej: `/tmp/notes.md`) con el contenido formateado.
2.  Hacer el commit de los cambios y el tag correspondiente: `git tag -a v... -m "..."`.
3.  Subir cambios: `git push origin master --tags`.
4.  Lanzar el release: `gh release create [TAB] --title "[TITULO]" --notes-file /tmp/notes.md`.
