---
description: Estándares de Codificación Universal y Portabilidad para Fina Ergen
---
Este documento es de lectura OBLIGATORIA antes de cada modificación de código. Define las reglas críticas para mantener a Fina Ergen funcional en cualquier entorno Linux.

### 🚫 REGLAS DE ORO (PROHIBIDO)
1.  **CERO Rutas Hardcoded**: Nunca uses `/home/claudio`, `/home/admin` o similares.
2.  **CERO Dependencias Fantasma**: No añadas librerías que no existan en repositorios estándar de Debian/Mint/Fedora sin proveer un script de instalación o binario.
3.  **CERO Placeholders**: No asumas que un archivo existe en una ruta fija.
4.  **CERO `linuxdeploy` (Para AppImage)**: Jamás dependas del bundler nativo de Tauri para AppImage ni de utilidades nativas que usen `linuxdeploy`, dado que falla silenciosamente en distribuciones modernas. Para construir `.AppImage` en Github Actions o local, construye SÓLO el paquete de Debian (`npm run tauri build -- --bundles deb`) y luego extrae manualmente el `/usr` del `.deb` para construir un `AppDir` usando `appimagetool`.

### ✅ MANDATORIO (OBLIGATORIO)
1.  **Detección Dinámica**: Usa siempre `os.path.dirname(os.path.abspath(__file__))` en Python o `ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` en Bash.
2.  **Entorno Virtual (VENV)**: El código debe buscar siempre el ejecutable de Python dentro de un entorno virtual (`.venv` o similar) antes de recurrir al sistema.
3.  **Configuración en XDG**: Todos los archivos de persistencia (`settings.json`, `contacts.json`) deben residir en `~/.config/Fina/` (siguiendo el estándar XDG).
4.  **Híbrido X11/Wayland**: Siempre que interactúes con el portapapeles o capturas, verifica si el usuario está en X11 o Wayland.
5.  **Protocolo de Release**: Es OBLIGATORIO seguir el formato visual y estructural definido en `.agent/workflows/publicar-release.md` para cualquier publicación en GitHub.
6.  **Laboratorio Local (`.local_lab/`)**: CUALQUIER script de prueba, archivo de texto temporal, log de desarrollo o experimento que se genere debe ser obligatoriamente guardado o creado dentro de la carpeta `.local_lab/`. Esta carpeta está ignorada por GitHub y mantiene la raíz del proyecto limpia.

### 📋 CHECKLIST PRE-COMMIT
- [ ] ¿He verificado que no hay rutas absolutas a mi carpeta personal?
- [ ] ¿He probado que el script de lanzamiento funciona si la carpeta se mueve de lugar?
- [ ] ¿He actualizado los requerimientos si añadí una librería nueva?
- [ ] ¿El acceso directo (.desktop) generado es relativo al HOME del usuario actual?

*Fina Ergen es para todos los humanos, no solo para su desarrollador.*
