# Documentación del Módulo de Control de TV (Fina)

Este documento detalla la implementación y uso de las funcionalidades de control de TV para dos televisores Android TV TCL.

## 📺 Dispositivos Configurados

*   **TV 1 (Principal)**
    *   **IP:** `192.168.0.11`
    *   **MAC:** `38:c8:04:31:17:b0` (Utilizada para WoL)
*   **TV 2**
    *   **IP:** `192.168.0.10`
    *   **MAC:** `34:51:80:f9:86:4a` (Utilizada para WoL)

## 🗣 Comandos de Voz Disponibles

### Encendido y Apagado
| Comando | Acción |
| :--- | :--- |
| "Enciende la tele" | Inicia ciclo de conexión WoL + ADB en ambas IPs. |
| "Apaga la tele" | Envía comando de apagado al dispositivo conectado. |

### Control de Volumen (Optimizado)
El volumen se ajusta rápidamente mediante ráfagas de comandos ADB.
| Comando | Acción | Detalles |
| :--- | :--- | :--- |
| "Sube el volumen de la tele" | Sube volumen (+5) | Valor por defecto: 5 puntos. |
| "Sube el volumen de la tele 10" | Sube volumen (+10) | Detecta números (máx 20). |
| "Baja el volumen de la tele" | Baja volumen (-5) | Valor por defecto: 5 puntos. |
| "Baja el volumen de la tele 20" | Baja volumen (-20) | Ráfaga ultra-rápida. |

### Navegación y Apps
| Comando | Acción | Detalles Técnicos |
| :--- | :--- | :--- |
| "Cambia de canal" / "Siguiente" | Canal Siguiente | `KEYCODE_CHANNEL_UP` (166) |
| "Canal anterior" | Canal Anterior | `KEYCODE_CHANNEL_DOWN` (167) |
| "Pon el canal 13" | Canal Numérico | Envía dígitos: `KEYCODE_1` (8), `KEYCODE_3` (10) |
| "Pon el canal 80.1" | Canal Digital | Usa `KEYCODE_NUMPAD_DOT` (158) para el punto. |
| "Vuelve a la tele" | **Modo TV en Vivo** | Mata apps streaming y lanza `com.tcl.tv`. |
| "Pon Netflix en la tele" | Abre App | Lanza `com.netflix.ninja`. |
| "Pon YouTube en la tele" | Abre App | Lanza `com.google.android.youtube.tv`. |
| "Pon Spotify en la tele" | Abre App | Lanza `com.spotify.tv.android`. |
| "Pon Flow en la tele" | Abre App | Lanza `com.telecom.flow`. |

---

## 🛠 Detalles Técnicos de la Implementación

### 1. Script de Encendido (`scripts/tv_on.py`)
*   **Lógica Unificada**: Gestiona ambas IPs simultáneamente.
*   **Wake-on-LAN (WoL)**: Envía "paquetes mágicos" al inicio de cada ciclo para despertar la tarjeta de red.
*   **Autocuración**: Si ADB reporta "already connected" pero el dispositivo no responde (Zombie), fuerza una desconexión y reconecta.
*   **Ciclos**: Realiza hasta 2 ciclos de 30 segundos. Si falla, Fina pregunta interactivamente si quieres reintentar.

### 2. Gestión de Canales (`channels.json`)
El sistema carga un mapeo de nombres a números desde `channels.json`.
*   **Búsqueda Exacta**: "Pon Telefe" -> `80.5`.
*   **Búsqueda Parcial**: "Pon Nacion" -> Encuentra "La Nacion" (`81.2`).
*   **Alias**: Definidos para categorías (ej: "dibujitos" -> `84.2`).

### 3. Control de Aplicaciones (`utils.py`)
*   **Mapeo de Paquetes**: `youtube`, `netflix`, `spotify`, etc.
*   **Volver a TV ("Exit Strategy")**:
    1.  **Kill Apps**: Ejecuta `am force-stop` en apps de streaming.
    2.  **Lanzar TV**: Ejecuta `com.tcl.tv`.

## 🧪 Pruebas
Scripts disponibles en `tests/`:
*   `test_tv_functions.py`: Prueba automatizada de volumen, canal digital y apps.
*   `test_channel_interactive.py`: Consola interactiva para probar búsqueda de canales por nombre.
*   `scan_tv_screen.py`: Utilidad OCR para extraer lista de canales desde la pantalla.

## 📋 Requisitos Previos
*   Las TV deben tener **Depuración USB/Red** activada.
*   El servidor ADB debe estar instalado en el host Linux (`sudo apt install adb`).
