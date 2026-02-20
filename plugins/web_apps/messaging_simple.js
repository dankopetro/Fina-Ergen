import { invoke } from "@tauri-apps/api/core";
import { WebviewWindow } from "@tauri-apps/api/webviewWindow";

const logMsg = async (message, level = "INFO") => {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${level}] ${message}`;
    console.log(`[${level}] ${message}`);
};

let whatsappWindow = null;

export const sendWhatsAppMessage = async (phoneNumber, messageText) => {
    await logMsg("=== INICIO DE ENVÍO ===");
    await logMsg(`Número: ${phoneNumber}`);
    await logMsg(`Mensaje: ${messageText}`);

    try {
        const cleanNumber = phoneNumber.replace(/[^0-9]/g, '');
        const encodedMessage = encodeURIComponent(messageText);
        const whatsappUrl = `https://web.whatsapp.com/send?phone=${cleanNumber}&text=${encodedMessage}`;

        await logMsg(`URL: ${whatsappUrl}`);

        if (!whatsappWindow) {
            whatsappWindow = new WebviewWindow('whatsapp-sender', {
                url: whatsappUrl,
                title: 'Fina WhatsApp',
                width: 1200,
                height: 800,
                visible: false,
                decorations: true,
                skipTaskbar: false
            });
        } else {
            // Si la ventana ya existe, navegamos a la nueva URL del mensaje
            await invoke("execute_js_in_window", {
                windowLabel: 'whatsapp-sender',
                script: `window.location.href = "${whatsappUrl}";`
            });
        }

        // --- LÓGICA DE VISIBILIDAD INTELIGENTE ---
        await logMsg("Verificando estado de sesión...");

        const checkStatusScript = `
            (function() {
                const isQR = !!document.querySelector('canvas') || !!document.querySelector('[data-ref]');
                const isLoggedIn = !!document.querySelector('#side') || !!document.querySelector('[data-icon="chat"]');
                if (isQR && !isLoggedIn) return "NEEDS_LOGIN";
                if (isLoggedIn) return "LOGGED_IN";
                return "LOADING";
            })()
        `;

        let wasShown = false;
        // Esperar y verificar estado de login (hasta 15 segundos de polling inicial)
        for (let i = 0; i < 15; i++) {
            const status = await invoke("execute_js_in_window", {
                windowLabel: 'whatsapp-sender',
                script: checkStatusScript
            });

            if (status === "NEEDS_LOGIN") {
                if (!wasShown) {
                    await logMsg("Código QR detectado. Mostrando ventana para login...", "WARN");
                    await whatsappWindow.show();
                    await whatsappWindow.setFocus();
                    wasShown = true;
                }
            } else if (status === "LOGGED_IN") {
                if (wasShown) {
                    await logMsg("Sesión iniciada. Ocultando ventana...");
                    await whatsappWindow.hide();
                }
                break;
            }
            await new Promise(r => setTimeout(r, 1000));
        }

        // Si después del loop principal sigue cargando, damos un margen extra
        await new Promise(r => setTimeout(r, 2000));

        const clickScript = `
            (async function() {
                for (let i = 0; i < 30; i++) {
                    const btn = document.querySelector('span[data-icon="send"]') ||
                               document.querySelector('button[aria-label*="Enviar"]') ||
                               document.querySelector('button[aria-label*="Send"]');
                    if (btn) {
                        btn.click();
                        await new Promise(r => setTimeout(r, 300));
                        btn.click();
                        return true;
                    }
                    await new Promise(r => setTimeout(r, 500));
                }
                return false;
            })();
        `;

        await invoke("execute_js_in_window", {
            windowLabel: 'whatsapp-sender',
            script: clickScript
        });

        await new Promise(r => setTimeout(r, 2000));
        return { success: true };

    } catch (error) {
        await logMsg(`ERROR: ${error.message}`, "ERROR");
        return { error: error.message };
    }
};

export const SUPPORTED_MESSAGING_APPS = {
    sms: {
        id: 'sms',
        name: 'SMS',
        package: 'com.android.mms',
        requiresAdb: true,
        icon: 'fa-solid fa-comment',
        color: 'text-blue-400'
    },
    whatsapp: {
        id: 'whatsapp',
        name: 'WhatsApp',
        package: 'com.whatsapp',
        requiresAdb: false,
        icon: 'fa-brands fa-whatsapp',
        color: 'text-green-400'
    },
    telegram: {
        id: 'telegram',
        name: 'Telegram',
        package: 'org.telegram.messenger',
        requiresAdb: false,
        icon: 'fa-brands fa-telegram',
        color: 'text-blue-400'
    }
};
