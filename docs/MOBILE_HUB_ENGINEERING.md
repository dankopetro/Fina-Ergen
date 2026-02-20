# 🛠️ Hub de Mensajería Invisible (UniversalMobileHub)
**Versión de Ingeniería: 1.0.0**

Este documento detalla el funcionamiento técnico del motor de mensajería de Fina Ergen, diseñado para superar las barreras de seguridad de Android 14 y permitir el envío de SMS sin interacción visual (Screen-Off).

## 1. Concepto de Inyección Binder
Fina no utiliza la interfaz de usuario (UI) para enviar SMS. En lugar de eso, utiliza el puente ADB para realizar una llamada directa al servicio `isms` del framework de Android mediante el comando `service call`.

### Estructura del Comando (Motorola/Universal):
```bash
service call isms 6 i32 [SUB_ID] s16 [PKG] s16 null s16 [DEST] s16 null s16 [MESSAGE] s16 null s16 null
```
*   **isms**: El servicio de telefonía encargado de la mensajería.
*   **Código 6**: Transacción de envío (varía según fabricante; 6 para Motorola, 18 para Google/Samsung genérico).
*   **SUB_ID**: ID de la tarjeta SIM (Subscription ID). Fina detecta automáticamente cuál es la SIM activa (usualmente 1 en dispositivos modernos).
*   **PKG**: Nombre del paquete que solicita el envío (`com.android.shell`).

## 2. Motor de Autodescubrimiento (Universal Discovery)
El script `mobile_hub.py` incluye una lógica de "escaneo de hardware". Si un dispositivo es desconocido, Fina prueba diferentes códigos de transacción (`candidates`) hasta encontrar el que responde correctamente (Parcel 00000000).

| Fabricante | Canal Sugerido | Estado |
| :--- | :--- | :--- |
| Motorola | 6 | **Verificado** |
| Google Pixel | 18 | Probable |
| Samsung | 18 / 20 | Probable |
| Genérico (AOSP) | 18 | Estándar |

## 3. Manejo de Espacios y Caracteres Especiales
Para evitar que el shell de Android trunque los mensajes en el primer espacio, el motor de Fina encapsula el mensaje en comillas escapadas (`\"message\"`) dentro de una cadena de comando única. Esto garantiza que el mensaje llegue íntegro al destinatario.

## 4. Integración con la Interfaz (App.vue)
El backend de Python (`mobile_hub.py`) se comunica con el frontend de Javascript (Vue) mediante el estándar JSON.
*   **Entrada:** Argumentos CLI (`--number`, `--msg`).
*   **Salida:** Un objeto JSON limpio (`{"status": "success", ...}`) para que la UI de Fina pueda mostrar animaciones de éxito o error en tiempo real.

## 5. Mantenimiento del Config
Las configuraciones descubiertas se guardan en `plugins/system/mobile_config.json`, evitando re-escanear el dispositivo en cada uso.

---
**Nota de Seguridad:** Este método requiere que la **Depuración ADB** esté activa. No requiere acceso ROOT, lo que lo hace seguro y compatible con dispositivos de fábrica.
