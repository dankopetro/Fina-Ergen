# 🛡️ Manual del Sistema CENTINELA (Fina Centinela V 2.1.0)

El sistema **Centinela** (anteriormente Sentinel) es la suite de protección activa y monitoreo de hardware de Fina. Proporciona una interfaz táctica para supervisar el estado de tu PC y la seguridad de tu red local.

## 📊 Monitoreo de Hardware (Sección Central)

El panel central muestra métricas en tiempo real obtenidas directamente del núcleo de tu computadora:

*   **CPU**: Porcentaje de carga de procesamiento y frecuencia actual en **MHz**.
*   **RAM**: Porcentaje de uso y desglose exacto de GB usados vs. GB totales.
*   **DISCO**: Estado de ocupación de tu unidad principal y GB exactos disponibles.
*   **RED (M)**: Monitor de tráfico de red en megabytes (Sent/Received desde el arranque).

---

## 💻 Terminal Centinela (Panel Derecho)

Este panel no es solo informativo; es una **consola de comandos interactiva** que permite disparar contramedidas y diagnósticos.

### Comandos Disponibles:

| Comando | Acción |
| :--- | :--- |
| `ayuda` / `help` / `?` | Muestra la lista de comandos disponibles en la terminal. |
| `stats` / `estado` | Genera un reporte rápido de recursos (CPU, RAM, Uptime). |
| `logs` | Sincroniza y muestra los últimos registros reales del sistema (Fina API, errores, comandos de voz). |
| `scan` / `escanear` | Inicia un **Escaneo de Intrusos Real** en tu red local para detectar dispositivos desconocidos. |
| `block [IP]` | Simula la adición de una dirección IP a la lista negra del Firewall. |
| `reset` / `reiniciar` | Reinicia el núcleo de seguridad de Fina (recarga la interfaz). |
| `clear` | (Próximamente) Limpia la pantalla de la terminal. |

---

## 🔍 Escaneo de Intrusos Real

A diferencia de versiones anteriores que mostraban datos simulados, el comando `scan` en la Terminal Centinela ahora realiza una búsqueda activa en tu subred. 

**¿Cómo funciona?**
1. Determina tu dirección IP local.
2. Escanea las direcciones activas en tu rango habitual (192.168.0.x o 192.168.1.x).
3. Reporta el número de dispositivos encontrados y sus direcciones IP en el registro de la terminal.

---

## �️ Requisitos del Sistema

Para que todas las funciones de **Centinela** operen correctamente, el sistema debe contar con:

1.  **Nmap (Escaneo Real)**: Obligatorio para el comando `scan`.
    *   *Instalación:* `sudo apt install nmap`
2.  **Psutil (Métricas)**: Librería de Python para leer CPU, RAM y Red.
    *   *Instalación:* Ya se incluye en el `requirements.txt` de Fina.

---

## �🛡️ Niveles de Amenaza

La interfaz dinámica de Centinela ajusta sus efectos visuales según el estado del sistema:
*   **Radar Activo**: Muestra pulsos visuales cuando se detecta actividad de red sospechosa.
*   **Nivel 4 (Almirante)**: Indica que tienes acceso total a todas las funciones de administración y borrado de logs.
*   **Barra de Amenaza**: Se eleva automáticamente si el uso de CPU supera el 85% o si se registran múltiples errores de autenticación en la red.
