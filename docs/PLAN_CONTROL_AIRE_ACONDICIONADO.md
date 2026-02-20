# Plan de Implementación: Control de Aires Acondicionados en Fina

Este documento resume el plan para integrar el control de aires acondicionados WiFi en el asistente Fina.

## 1. Estructura de Archivos
Se propone una estructura modular dentro de una nueva carpeta `iot/`:

- `iot/air_conditioner.py`: Clase base y lógica de control (encendido, apagado, temperatura, modo).
- `iot/discovery.py`: Script para escaneo automático de la red en busca de nuevos dispositivos.

## 2. Tecnologías y Librerías Consideradas
Dependiendo del hardware del usuario, se utilizará una de las siguientes opciones:

- **Opción A (Tuya / SmartLife / Genéricos):** Uso de la librería `tinytuya`. Es la más compatible con la mayoría de ACs WiFi económicos.
- **Opción B (Midea / Toshiba / Comfee / Carrier):** Uso de la librería `msmart`.
- **Opción C (Broadlink / IR Blasters):** Uso de `broadlink` para controlar aires mediante emisores infrarrojos WiFi (como el RM Mini).

## 3. Flujo de Trabajo
1.  **Identificación:** El usuario debe confirmar la marca o la aplicación móvil que utiliza.
2.  **Instalación de Dependencias:** `pip install` de la librería seleccionada.
3.  **Creación del Script de Control:** Implementación de las funciones `turn_on`, `turn_off`, `set_temp`.
4.  **Integración en Fina:**
    - Añadir los comandos al `intents.json`.
    - Modificar `main.py` para procesar los nuevos comandos de voz.

---
**Estado:** Pendiente de confirmación de hardware por parte del usuario.
