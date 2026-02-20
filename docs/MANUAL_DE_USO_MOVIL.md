# 📱 Guía de Integración Móvil - Fina Ergen

Fina Ergen ahora se extiende más allá del escritorio, permitiéndote interactuar con tu teléfono Android directamente desde la interfaz.

## 1. Vinculación del Dispositivo
Para que Fina pueda enviar mensajes o llamar por ti, primero debes decirle qué teléfono usar.
1.  Ve a la pestaña **Ajustes** (ícono de engranaje).
2.  Entra en **Nódulos de Conectividad**.
3.  Haz clic en **"Escanear Red"**. Fina buscará tus dispositivos.
4.  Busca tu teléfono en la lista. Si no tiene nombre, dale a **"Asignar"**, ponle un nombre (ej: "Móvil Claudio") y selecciona el ícono de **Celular**.
5.  **IMPORTANTE:** Haz clic en la **Estrella** al lado de tu dispositivo para marcarlo como **Principal**. Se pondrá amarilla. Fina recordará esta elección.

## 2. Uso de la Agenda
Una vez vinculado, la pestaña **Agenda** se convierte en tu centro de comando.
*   **Mensajería:**
    *   Haz clic en el botón **"Mensajería"**.
    *   Verás que ahora indica el nombre de tu móvil conectado (ej: "Sincronizado: iPhone Claudio").
    *   Se abrirá una ventana emergente ("Modal") donde podrás escribir:
        *   **Destinatario:** Número telefónico o nombre del contacto.
        *   **Mensaje:** El texto que deseas enviar.
    *   Al hacer clic en **"Enviar Mensaje"**, Fina enviará la orden a tu teléfono.
*   **Llamadas:**
    *   Haz clic en **"Llamada"**.
    *   Ingresa el número y Fina iniciará la llamada en tu teléfono inmediatamente (te ahorrará tener que buscar el contacto y marcar).

## 3. Requisitos Técnicos
*   **Sistema Android:** Funciona con cualquier dispositivo Android moderno.
*   **Depuración:** Tu teléfono debe tener la **Depuración por USB/Inalámbrica** activada en las *Opciones de Desarrollador*.
*   **Autorización:** Fina usa `adb` (Android Debug Bridge) para comunicarse de forma segura. Si es la primera vez que lo usas, mira la pantalla de tu teléfono y **autoriza la conexión** cuando Fina intente conectarse.

## 4. Solución de Problemas
*   **"Error: Sin Dispositivo":** Asegúrate de haber marcado la **Estrella** en Ajustes. Fina necesita saber cuál es el principal.
*   **No conecta:** Verifica que el teléfono esté en la misma red Wi-Fi y que no esté bloqueado o en modo suspensión profunda.
