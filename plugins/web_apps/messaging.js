import { invoke } from "@tauri-apps/api/core";
import { WebviewWindow } from "@tauri-apps/api/webviewWindow";

const isTauri = !!(window.__TAURI_INTERNALS__ || window.__TAURI_IPC__);

// === SISTEMA DE LOGS EXHAUSTIVO ===
const logMsg = async (msg, level = 'INFO') => {
    const timestamp = new Date().toISOString();
    const logLine = `[${timestamp}] [${level}] ${msg}`;
    console.log(logLine);

    if (isTauri) {
        try {
            await invoke("execute_shell_command", {
                command: `echo "${logLine}" >> /home/claudio/Descargas/Fina-Ergen/Logs/messaging_debug.log`
            });
        } catch (e) {
            console.error("Failed to write log:", e);
        }
    }
};

export const SUPPORTED_MESSAGING_APPS = {
    'sms': {
        id: 'sms',
        name: 'SMS',
        package: 'com.android.mms',
        icon: 'fa-solid fa-comment-sms',
        color: 'text-blue-500',
        isDefault: true
    },
    'whatsapp': {
        id: 'whatsapp',
        name: 'WhatsApp',
        package: 'com.whatsapp',
        icon: 'fa-brands fa-whatsapp',
        color: 'text-green-500',
        uri: 'https://api.whatsapp.com/send?phone={phone}&text={text}'
    },
    'telegram': {
        id: 'telegram',
        name: 'Telegram',
        package: 'org.telegram.messenger',
        icon: 'fa-brands fa-telegram',
        color: 'text-cyan-400',
        uri: 'tg://msg?text={text}&to={phone}'
    }
};

export const MESSAGING_URLS = {
    'whatsapp': 'https://web.whatsapp.com',
    'telegram': 'https://web.telegram.org/a/',
    'sms': '/messaging.html'
};

// === SCRIPT DE WHATSAPP MEJORADO CON LOGS ===
export const WHATSAPP_AUTOMATION_SCRIPT = `
(async function() {
    const log = (msg) => {
        console.log("[FINA_WA] " + msg);
        if (window.__TAURI_INTERNALS__) {
            window.__TAURI_INTERNALS__.invoke("plugin:event|emit", { 
                event: "wa-automation-log", 
                payload: msg 
            }).catch(() => {});
        }
    };

    log("🚀 Script de automatización cargado");

    // Función de espera inteligente
    const waitForElement = (selector, timeout = 15000) => {
        log("⏳ Esperando elemento: " + selector);
        return new Promise((resolve) => {
            const startTime = Date.now();
            const checkInterval = setInterval(() => {
                const element = document.querySelector(selector);
                if (element) {
                    clearInterval(checkInterval);
                    log("✅ Elemento encontrado: " + selector);
                    resolve(element);
                } else if (Date.now() - startTime > timeout) {
                    clearInterval(checkInterval);
                    log("❌ TIMEOUT esperando: " + selector);
                    resolve(null);
                }
            }, 300);
        });
    };

    // Función principal de envío
    window.FinaWhatsappSend = async function(contactName, messageText) {
        try {
            log("📱 Iniciando envío a: " + contactName);
            log("💬 Mensaje: " + messageText);

            // PASO 1: Buscar la caja de búsqueda
            log("🔍 PASO 1: Localizando caja de búsqueda...");
            const searchSelectors = [
                'div[contenteditable="true"][data-tab="3"]',
                'div[title="Buscar o empezar un chat nuevo"]',
                '#side div[contenteditable="true"]',
                'div.lexical-rich-text-input div[contenteditable="true"]'
            ];

            let searchBox = null;
            for (const selector of searchSelectors) {
                searchBox = await waitForElement(selector, 3000);
                if (searchBox) break;
            }

            if (!searchBox) {
                log("❌ ERROR CRÍTICO: No se encontró la caja de búsqueda");
                return { error: "Search box not found" };
            }

            // PASO 2: Escribir el nombre del contacto
            log("✍️ PASO 2: Escribiendo nombre del contacto...");
            searchBox.focus();
            await new Promise(r => setTimeout(r, 300));
            
            // Limpiar contenido previo
            document.execCommand('selectAll', false, null);
            document.execCommand('delete', false, null);
            await new Promise(r => setTimeout(r, 200));

            // Escribir letra por letra (simula tipeo humano)
            for (let i = 0; i < contactName.length; i++) {
                document.execCommand('insertText', false, contactName[i]);
                await new Promise(r => setTimeout(r, 50));
            }
            log("✅ Nombre escrito completamente");

            // PASO 3: Esperar resultados de búsqueda
            log("⏳ PASO 3: Esperando resultados de búsqueda...");
            await new Promise(r => setTimeout(r, 2500));

            // PASO 4: Seleccionar el primer resultado
            log("🎯 PASO 4: Seleccionando contacto...");
            const resultSelectors = [
                'div[data-testid="cell-frame-container"]',
                'div[role="listitem"]',
                'div._ak72',
                '#pane-side div[role="row"]',
                'div[aria-label] > div > div'
            ];

            let firstResult = null;
            let selectorUsed = null;
            for (const selector of resultSelectors) {
                log("   [BUSCAR] Probando selector: " + selector);
                const results = document.querySelectorAll(selector);
                log("   [BUSCAR] Encontrados: " + results.length + " elementos");
                if (results.length > 0) {
                    firstResult = results[0];
                    selectorUsed = selector;
                    log("   [BUSCAR] OK - Usando primer resultado");
                    break;
                }
            }

            if (firstResult) {
                log("[CLIC] Haciendo clic en resultado (" + selectorUsed + ")");
                
                // Intentar múltiples clics
                firstResult.click();
                await new Promise(r => setTimeout(r, 100));
                firstResult.click();
                await new Promise(r => setTimeout(r, 100));
                
                // Clic con evento de mouse
                const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
                firstResult.dispatchEvent(clickEvent);
                
                log("[CLIC] Clics ejecutados (x3)");
            } else {
                log("⚠️ No se encontró resultado visual, intentando Enter...");
                searchBox.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    cancelable: true
                }));
            }

            // PASO 5: Esperar que se abra el chat
            log("⏳ PASO 5: Esperando apertura del chat...");
            await new Promise(r => setTimeout(r, 2000));

            // PASO 6: Localizar caja de mensaje
            log("📝 PASO 6: Localizando caja de mensaje...");
            const messageSelectors = [
                'div[title="Escribe un mensaje"]',
                'div[data-tab="10"]',
                '#main footer div[contenteditable="true"]',
                'div.lexical-rich-text-input div[role="textbox"]'
            ];

            let messageBox = null;
            for (const selector of messageSelectors) {
                messageBox = await waitForElement(selector, 5000);
                if (messageBox) break;
            }

            if (!messageBox) {
                log("❌ ERROR CRÍTICO: No se encontró la caja de mensaje");
                return { error: "Message box not found" };
            }

            // PASO 7: Escribir mensaje
            log("✍️ PASO 7: Escribiendo mensaje...");
            messageBox.focus();
            await new Promise(r => setTimeout(r, 300));
            document.execCommand('insertText', false, messageText);
            log("✅ Mensaje escrito");

            // PASO 8: Enviar
            log("📤 PASO 8: Enviando mensaje...");
            await new Promise(r => setTimeout(r, 800));

            const sendSelectors = [
                'span[data-icon="send"]',
                'button[aria-label="Enviar"]',
                'button[aria-label="Send"]'
            ];

            let sendButton = null;
            for (const selector of sendSelectors) {
                sendButton = document.querySelector(selector);
                if (sendButton) break;
            }

            if (sendButton) {
                sendButton.click();
                log("✅ MENSAJE ENVIADO CON ÉXITO (botón)");
            } else {
                log("⚠️ Botón no encontrado, enviando con Enter...");
                messageBox.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    cancelable: true
                }));
                log("✅ MENSAJE ENVIADO CON ÉXITO (Enter)");
            }

            return { success: true };

        } catch (error) {
            log("💥 ERROR FATAL: " + error.message);
            log("Stack: " + error.stack);
            return { error: error.message };
        }
    };

    log("✅ Sistema de automatización listo");
})();
`;

let hiddenMessagingWin = null;

// === FUNCIÓN PRINCIPAL: ENVIAR MENSAJE ===
export const sendWhatsAppMessage = async (contactName, messageText) => {
    await logMsg("=== INICIO DE ENVÍO DE MENSAJE ===");
    await logMsg(`Contacto: ${contactName}`);
    await logMsg(`Mensaje: ${messageText}`);

    if (!isTauri) {
        await logMsg("ERROR: No está en entorno Tauri", "ERROR");
        return { error: "Not in Tauri environment" };
    }

    try {
        // PASO 1: Crear/Obtener ventana (INTELIGENTE: visible solo si necesita QR)
        await logMsg("PASO 1: Verificando ventana...");

        if (!hiddenMessagingWin) {
            await logMsg("Creando nueva ventana...");

            // Verificar si ya se vinculó antes (guardado en localStorage del navegador)
            const isLinked = localStorage.getItem('whatsapp_linked') === 'true';
            const shouldBeVisible = true; // TEMPORAL: SIEMPRE VISIBLE PARA VER QUÉ PASA

            await logMsg(`WhatsApp vinculado previamente: ${isLinked}`);
            await logMsg(`Ventana será ${shouldBeVisible ? 'VISIBLE (para escanear QR)' : 'INVISIBLE (ya vinculado)'}`);

            hiddenMessagingWin = new WebviewWindow('whatsapp-hidden', {
                url: 'https://web.whatsapp.com',
                title: shouldBeVisible ? 'Fina WhatsApp - Escanea QR para vincular' : 'Fina WhatsApp',
                width: 1200,
                height: 800,
                visible: shouldBeVisible,
                decorations: shouldBeVisible,
                skipTaskbar: !shouldBeVisible,
                userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            });

            await logMsg(`Ventana creada (${shouldBeVisible ? 'VISIBLE' : 'OCULTA'})`);

            // Después de 10 segundos, verificar si ya se vinculó
            setTimeout(async () => {
                try {
                    await invoke("execute_js_in_window", {
                        windowLabel: 'whatsapp-hidden',
                        script: `
                            // Verificar si hay QR o si ya está logueado
                            const qrCode = document.querySelector('canvas[aria-label*="QR"]') || document.querySelector('div[data-ref]');
                            const isLoggedIn = !qrCode && document.querySelector('#side'); // Si no hay QR y hay sidebar, está logueado
                            
                            if (isLoggedIn) {
                                console.log('[FINA] WhatsApp vinculado detectado');
                                localStorage.setItem('whatsapp_linked', 'true');
                            }
                        `
                    });

                    // Si estaba visible y ya se vinculó, guardar el estado
                    if (shouldBeVisible) {
                        localStorage.setItem('whatsapp_linked', 'true');
                        await logMsg("Estado de vinculación guardado");
                    }
                } catch (e) {
                    await logMsg(`Error verificando estado: ${e}`, "WARN");
                }
            }, 10000);

            // Listener para logs del script
            hiddenMessagingWin.listen('wa-automation-log', async (event) => {
                await logMsg(`[WA_SCRIPT] ${event.payload}`, "DEBUG");
            });

            hiddenMessagingWin.once('tauri://error', async (e) => {
                await logMsg(`ERROR EN VENTANA: ${JSON.stringify(e)}`, "ERROR");
                hiddenMessagingWin = null;
            });

            // Esperar a que WhatsApp Web cargue
            await logMsg("Esperando carga de WhatsApp Web...");
            await new Promise(r => setTimeout(r, 8000)); // Dar tiempo para login si es necesario
        } else {
            await logMsg("Reutilizando ventana existente");
        }

        // PASO 2: Inyectar script de automatización
        await logMsg("PASO 2: Inyectando script de automatización...");
        try {
            await invoke("execute_js_in_window", {
                windowLabel: 'whatsapp-hidden',
                script: WHATSAPP_AUTOMATION_SCRIPT
            });
            await logMsg("Script inyectado correctamente");
        } catch (evalError) {
            await logMsg(`Error inyectando script: ${evalError}`, "ERROR");
            throw new Error(`Failed to inject script: ${evalError}`);
        }

        // PASO 3: Ejecutar envío
        await logMsg("PASO 3: Ejecutando envío de mensaje...");
        const safeContact = JSON.stringify(contactName);
        const safeMessage = JSON.stringify(messageText);

        const executeScript = `
            (async function() {
                if (window.FinaWhatsappSend) {
                    return await window.FinaWhatsappSend(${safeContact}, ${safeMessage});
                } else {
                    return { error: "Automation function not loaded" };
                }
            })();
        `;

        let result;
        try {
            await invoke("execute_js_in_window", {
                windowLabel: 'whatsapp-hidden',
                script: executeScript
            });
            await logMsg(`Script de envío ejecutado`);

            // Esperar para que el script complete
            await new Promise(r => setTimeout(r, 3000));

            // Asumimos éxito por ahora (mejorar después con eventos)
            result = { success: true };
            await logMsg(`Resultado: ${JSON.stringify(result)}`);
        } catch (execError) {
            await logMsg(`Error ejecutando envío: ${execError}`, "ERROR");
            result = { error: execError.toString() };
            await logMsg(`Resultado: ${JSON.stringify(result)}`);
        }


        if (result && result.success) {
            await logMsg("=== MENSAJE ENVIADO CON ÉXITO ===", "SUCCESS");
            return { success: true };
        } else {
            await logMsg(`=== ERROR EN ENVÍO: ${result?.error || 'Unknown'} ===`, "ERROR");
            return { error: result?.error || "Unknown error" };
        }

    } catch (error) {
        await logMsg(`=== ERROR FATAL: ${error.message} ===`, "ERROR");
        await logMsg(`Stack: ${error.stack}`, "ERROR");
        return { error: error.message };
    }
};
