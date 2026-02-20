# Instrucciones para obtener las Claves de Tuya (Local Key)

Para que Fina pueda controlar tu timbre y ver la cámara, necesitamos las "llaves" digitales del dispositivo. Sigue estos pasos cuidadosamente:

1.  **Crear cuenta en Tuya IoT:**
    *   Ve a [iot.tuya.com](https://iot.tuya.com) y regístrate (es gratis).

2.  **Crear un Proyecto Cloud:**
    *   En el panel izquierdo, ve a **Cloud** > **Development**.
    *   Click en **Create Cloud Project**.
    *   Nombre: `FinaHome`.
    *   Industry: `Smart Home`.
    *   Data Center: Selecciona el más cercano a tu país (ej: **Western America** suele funcionar bien para Latam/Global).
    *   Development Method: **Smart Home**.

3.  **Vincular tu App Tuya:**
    *   Dentro de tu nuevo proyecto, ve a la pestaña **Devices** > **Link Tuya App Account**.
    *   Click en **Add App Account**.
    *   Aparecerá un código QR. Escanéalo con tu celular usando la App de Tuya (Perfil > ícono de escáner arriba a la derecha).
    *   Confirma en el celular.

4.  **Obtener las Claves:**
    *   Ahora verás tu lista de dispositivos en la web.
    *   Busca tu **Timbre / Video Doorbell**.
    *   Copia el **Device ID** (ID de dispositivo).
    *   Ve a la pestaña **API Explorer** (a la izquierda) > **Smart Home Device System** > **Device Management** > **Get Device Details**.
    *   Pega el `Device ID` y dale a "Submit Request".
    *   En la respuesta (derecha), busca el campo `"local_key"`. ¡Esa es la clave secreta!

---
**Una vez tengas estos datos, dímelos o guárdalos en un archivo seguro, Fina los necesitará:**
*   **Device ID:** (ej: `bf4328...`)
*   **Local Key:** (ej: `a3f89...`)
*   **Region:** (ej: `us`)
