# Arquitectura de Plugins IoT para Fina

## Visión General
Fina está evolucionando de un asistente personal a un centro de control domótico inteligente. Dado que cada usuario tiene dispositivos diferentes (TVs, Timbres, Luces, ACs), la funcionalidad IoT debe ser modular.

Este documento describe la arquitectura propuesta para el sistema de plugins.

## 1. Estructura de un Plugin
Cada plugin será un directorio en `plugins/` (o `fina_plugins/` en Rust) que contiene:

*   **`manifest.json`**: Metadatos del plugin.
*   **`main.py`** (o `.rs`): Lógica de control.
*   **`config_schema.json`**: Esquema de configuración requerida (IP, Token, Modelo).
*   **`discovery.py`**: Script ligero para detectar si el dispositivo existe en la red.

### Ejemplo: Plugin de Timbre (Tuya/Waydroid)
```json
// manifest.json
{
  "id": "doorbell_tuya_waydroid",
  "name": "Tuya Video Doorbell (Waydroid)",
  "description": "Control de timbre Tuya usando emulación Android en Waydroid",
  "version": "1.0.0",
  "type": "camera_audio",
  "dependencies": ["waydroid", "adb", "scrcpy"]
}
```

## 2. Sistema de Auto-Descubrimiento (Discovery)
Fina ejecutará un escaneo periódico (o a demanda) de la red local.

1.  **Escaneo ARP/Ping**: Obtener lista de dispositivos conectados (IP + MAC).
2.  **Identificación OUI**: Identificar fabricante por MAC (ej. "Tuya Smart Inc.", "LG Electronics").
3.  **Matching**:
    *   Si ve una MAC de LG -> Sugerir "LG WebOS TV Plugin".
    *   Si ve una MAC de Espressif/Tuya -> Sugerir "Tuya Plugin".
4.  **Sugerencia al Usuario**:
    *   *"Detecté un nuevo Timbre Inteligente en 192.168.0.5. ¿Quieres configurarlo?"*

## 3. Instalación "En un Clic"
Si el usuario acepta:
1.  Fina descarga el plugin del repositorio de GitHub (`fina-plugins`).
2.  Ejecuta el script de instalación del plugin (ej. `install_dependencies.sh` para instalar `adb` o `scrcpy`).
3.  Pide los datos necesarios según `config_schema.json` (ej. IP, Claves).
4.  Activa el plugin.

## 4. Integración con el Núcleo (Rust/Python)
Los plugins expondrán "Intenciones" estandarizadas que el clasificador de Fina entenderá:

*   **Standard Traits**:
    *   `TurnOn`, `TurnOff` (Luces, TV, AC)
    *   `SetLevel` (Volumen, Brillo, Temperatura)
    *   `GetStatus` (¿Está prendido?, ¿Qué temperatura hace?)
    *   `ViewStream` (Cámaras, Timbres)
    *   `TwoWayAudio` (Timbres)

De esta forma, `"Enciende la luz"` funcionará igual para una lámpara Philips Hue que para una chinada por WiFi, solo cambia el plugin que ejecuta la acción.

## 5. Caso de Estudio: El Timbre Actual
Actualmente tenemos scripts sueltos (`doorbell_monitor.py`, `hangup.py`).
En el futuro, esto se empaquetará así:

*   `plugins/doorbell_tuya/`
    *   `monitor.py` (servicio de fondo)
    *   `actions.py` (contiene `hangup`, `answer`)
    *   `assets/` (iconos, sonidos)

Fina (Rust) cargará este plugin al inicio, lanzará el proceso monitor y registrará los comandos de voz asociados.

---
**Estado Actual**: Prototipo funcional implementado en scripts Python independientes.
**Siguiente Paso**: Refactorizar lógica de TV y Timbre hacia esta estructura modular en la versión Rust.
