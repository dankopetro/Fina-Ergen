# Documentación Técnica: Minimización al Tray en Linux (X11/Weston)

Esta guía detalla el procedimiento técnico implementado en Fina Phoenix para capturar una ventana de Weston y enviarla a la bandeja de sistema (System Tray) de forma programática.

## Requisitos del Sistema
Para que este flujo funcione, deben estar instaladas las siguientes herramientas:
- `wmctrl`: Para interactuar con el gestor de ventanas (EWMH).
- `xdotool`: Herramienta de automatización de X11 (como fallback).
- `kdocker`: El motor que realiza el "docking" de la ventana en el tray.
- `xprop`: Para modificar propiedades de bajo nivel de la ventana X11.

## Procedimiento Técnico (Paso a Paso)

### 1. Identificación de la Ventana (WID)
El primer paso es obtener el **Window ID (WID)** en formato hexadecimal. La ventana de Weston suele tener un título que contiene "Weston".

**Comando principal (wmctrl + AWK):**
```bash
wmctrl -l | grep -iE 'Weston|weston' | tail -1 | awk '{print $1}'
```
*   `wmctrl -l`: Lista todas las ventanas abiertas.
*   `awk '{print $1}'`: **CRÍTICO.** Se usa `awk` en lugar de `cut` porque `wmctrl` formatea la salida con espacios variables para alinear columnas. `cut` fallaría si hay espacios extra.
*   `tail -1`: Se asegura de tomar la instancia más reciente.

**Fallback (xdotool):**
```bash
xdotool search --name 'Weston' || xdotool search --class 'weston'
```

### 2. Manipulación de Propiedades X11 (Ocultación de UI)
Antes de enviar al tray, es fundamental que la ventana no aparezca en la barra de tareas principal ni en el selector de aplicaciones (Pager/Alt-Tab). Para ello se utilizan los "Atom" de `_NET_WM_STATE`.

**Comando:**
```bash
xprop -id <WID> -f _NET_WM_STATE 32a -set _NET_WM_STATE _NET_WM_STATE_SKIP_TASKBAR,_NET_WM_STATE_SKIP_PAGER
```
*   `_NET_WM_STATE_SKIP_TASKBAR`: Indica al panel que no muestre el botón de la ventana.
*   `_NET_WM_STATE_SKIP_PAGER`: Indica al sistema que no la muestre en el conmutador de espacios de trabajo ni en Alt-Tab.

### 3. Acoplamiento al Tray (Docking)
Finalmente, se utiliza `kdocker` para "tragar" la ventana y representarla mediante un icono en el tray.

**Comando:**
```bash
kdocker -w <WID> -t -r -q -i /ruta/al/icono.png
```
**Flags utilizados:**
- `-w <WID>`: Especifica la ventana destino por su ID hexadecimal.
- `-t`: (Taskbar) Refuerza la ocultación en la barra de tareas.
- `-r`: (Remove) Remueve la ventana del tray si el proceso padre muere.
- `-q`: (Quiet) Modo silencioso, evita notificaciones innecesarias de kdocker.
- `-i`: Permite definir un icono personalizado (PNG o SVG).

## Solución de Problemas Comunes

### 1. Error: "Could not find a matching window"
Si `kdocker` arroja este error incluso cuando la ventana existe, suele deberse a dos causas:
*   **Identificador Incorrecto:** El WID extraído tiene espacios o caracteres basura. **Solución:** Usar siempre `awk '{print $1}'` para limpiar el ID.
*   **Icono Inválido:** Si se pasa un path de icono (`-i`) que no existe, kdocker a veces falla con un mensaje genérico. **Solución:** Validar que el archivo `.png` o `.xpm` exista antes de llamar al comando, o usar iconos de sistema estándar (`/usr/share/pixmaps/`).

### 2. Múltiples Carteles de Error / Iconos Duplicados
Si se ejecuta el script de minimización varias veces, pueden acumularse instancias de `kdocker` "huérfanas" intentando capturar la misma ventana.
**Solución:** Siempre ejecutar una limpieza previa al inicio del script:
```bash
pkill kdocker || true
```

### 3. La Ventana Reaparece
Si la aplicación (Waydroid/Weston) se reinicia o cambia de estado, puede perderse el acople.
**Solución:** El script debe ser llamado *después* de que la ventana gráfica esté totalmente establecida. Un bucle de espera (`while/sleep`) buscando el WID es obligatorio.

---
*Documento generado para el proyecto Fina Phoenix - 2026 (Revisión: Enero 29)*
