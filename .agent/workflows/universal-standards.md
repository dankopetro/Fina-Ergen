---
description: Estándares de Codificación Universal y Portabilidad para Fina Ergen
---
Este documento es de lectura OBLIGATORIA antes de cada modificación de código. Define las reglas críticas para mantener a Fina Ergen funcional en cualquier entorno Linux.

### 🚫 REGLAS DE ORO (PROHIBIDO)
1.  **CERO Rutas Hardcoded**: Nunca uses `/home/claudio`, `/home/admin` o similares.
2.  **CERO Dependencias Fantasma**: No añadas librerías que no existan en repositorios estándar de Debian/Mint/Fedora sin proveer un script de instalación o binario.
3.  **CERO Placeholders**: No asumas que un archivo existe en una ruta fija.

### ✅ MANDATORIO (OBLIGATORIO)
1.  **Detección Dinámica**: Usa siempre `os.path.dirname(os.path.abspath(__file__))` en Python o `ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` en Bash.
2.  **Entorno Virtual (VENV)**: El código debe buscar siempre el ejecutable de Python dentro de un entorno virtual (`.venv` o similar) antes de recurrir al sistema.
3.  **Configuración en XDG**: Todos los archivos de persistencia (`settings.json`, `contacts.json`) deben residir en `~/.config/Fina/` (siguiendo el estándar XDG).
4.  **Híbrido X11/Wayland**: Siempre que interactúes con el portapapeles o capturas, verifica si el usuario está en X11 o Wayland.

### 📋 CHECKLIST PRE-COMMIT
- [ ] ¿He verificado que no hay rutas absolutas a mi carpeta personal?
- [ ] ¿He probado que el script de lanzamiento funciona si la carpeta se mueve de lugar?
- [ ] ¿He actualizado los requerimientos si añadí una librería nueva?
- [ ] ¿El acceso directo (.desktop) generado es relativo al HOME del usuario actual?

*Fina Ergen es para todos los humanos, no solo para su desarrollador.*
