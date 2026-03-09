<script setup>
import { ref, onMounted, computed, onUnmounted, reactive, watch } from "vue";
import { invoke as tauriInvoke } from "@tauri-apps/api/core";
import { getCurrentWindow as tauriGetWindow } from "@tauri-apps/api/window";
import { WebviewWindow } from "@tauri-apps/api/webviewWindow";
import { listen as tauriListen, emit } from "@tauri-apps/api/event";
import {
    SUPPORTED_MESSAGING_APPS,
    sendWhatsAppMessage
} from "../plugins/web_apps/messaging_simple.js";
import QRCode from 'qrcode';
import FinaAvatar from "./components/FinaAvatar.vue";
import WeatherModule from "./components/WeatherModule.vue";
import iconAvatar from "./assets/iconoergen.png";

// --- DIAGNÓSTICO DE ERRORES FATALES ---
window.onerror = function (msg, url, line, col, error) {
    fetch("http://127.0.0.1:18000/api/state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "error", process: `JS FATAL: ${msg} (${line}:${col})` })
    }).catch(() => { });
};
window.onunhandledrejection = function (e) {
    let reason = e.reason;
    if (reason && reason.message) reason = reason.message;
    fetch("http://127.0.0.1:18000/api/state", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "error", process: `PROMISE REJECT: ${reason}` })
    }).catch(() => { });
};

// --- TAURI SAFETY WRAPPERS ---
// V2 detection uses __TAURI_INTERNALS__ or check if window.__TAURI__ is present in some configurations
const isTauri = !!(window.__TAURI_INTERNALS__ || window.__TAURI_IPC__);

const invoke = async (cmd, args = {}) => {
    if (!isTauri) {
        console.warn(`[BROWSER MOCK] invoke("${cmd}")`, args);
        if (cmd === "execute_shell_command") {
            const c = args.command || "";
            if (c.includes("get_stats.py")) return JSON.stringify({ cpu: { percent: 12 }, ram: { percent: 45, used: 8, total: 16 }, disk: { percent: 30, free: 250 }, uptime: "1d 4h" });
            if (c.includes("read_emails")) return JSON.stringify({ status: "success", emails: [{ subject: "Browser Mock Email", from: "Tauri Mock", date: "Now" }] });
            if (c.includes("doorbell_status.py")) return "85";
            if (c.includes("clima_api.py")) return JSON.stringify({ main: { temp: 22, humidity: 40 }, weather: [{ id: 800, icon: "01d" }], cod: 200 });
        }
        return "OK";
    }
    return await tauriInvoke(cmd, args);
};

// --- RECURSOS DINÁMICOS ---
const pythonExecutable = ref("python3");
const projectRoot = ref("");
const configDir = ref("");

const syncSystemInfo = async () => {
    if (!isTauri) return;
    try {
        const res = await fetch("http://127.0.0.1:18000/api/system/info");
        const data = await res.json();
        if (data.python_path) {
            pythonExecutable.value = data.python_path;
            projectRoot.value = data.project_root || projectRoot.value;
            configDir.value = data.config_dir || configDir.value;
            console.log("✅ Fina System Info:", { python: pythonExecutable.value, root: projectRoot.value, config: configDir.value });
        }
    } catch (e) {
        // Backend no listo, reintentar en 3s
        setTimeout(syncSystemInfo, 3000);
    }
};

const getCurrentWindow = () => {
    if (!isTauri) {
        return {
            label: "main",
            listen: () => { },
            once: () => { },
            emit: () => { },
            close: () => { },
            minimize: () => { },
            maximize: () => { },
            unmaximize: () => { },
            isMaximized: () => Promise.resolve(false),
            setFullscreen: () => { },
            setResizable: () => { },
            setTitle: () => { }
        };
    }
    return tauriGetWindow();
};

const listen = async (event, handler) => {
    if (!isTauri) {
        console.warn(`[BROWSER MOCK] listen("${event}")`);
        return () => { };
    }
    return await tauriListen(event, handler);
};

const submitUniversalPin = async () => {
    if (universalPinInput.value.length === 6) {
        try {
            await emit("plugin-pin-response", { plugin_id: universalPinData.value.plugin_id, pin: universalPinInput.value, ip: universalPinData.value.ip });
            showUniversalPinModal.value = false;
            universalPinInput.value = "";
            addChatMessage(t('ui_pairing_sent', 'PIN enviado. Procesando...'));
        } catch (e) {
            console.error("Error enviando PIN:", e);
        }
    }
};

// --- STATE ---
const i18nData = ref({});
const userSettings = ref({
    apis: {
        GITHUB_TOKEN: "",
        OPENAI_API_KEY: "",
        ELEVENLABS_API_KEY: "",
        FINA_VOICE_ID: "",
        WEATHER_API_KEY: "",
        WEATHER_CITY_ID: "",
        NEWS_API_KEY: "",
        UNSPLASH_ACCESS_KEY: "",
        RUNAWAY_API_KEY: "",
        EMAIL_USER: "",
        EMAIL_PASSWORD: "",
        VOICE_MODELS_PATH: "",
        VOSK_MODEL_PATH: "",
        AC_IP: "",
        USER_NAME: "Usuario"
    },
    tvs: [],
    devices: [], // Generic devices storage
    disabled_channels: [],
    tv_apps: {},
    linked_apps: []
});

const t = (key, fallback = "") => {
    const lang = userSettings.value.apis?.FINA_LANGUAGE || "en";
    const translations = i18nData.value[lang] || {};
    const englishFallback = i18nData.value["en"] || {};
    return translations[key] || englishFallback[key] || fallback || key;
};

const finaState = ref({
    status: "idle",
    process: t('systems_ready', 'SISTEMA LISTO'),
    intensity: 0.0,
    showPasswordField: false,
    authError: false
});
const authPassword = ref("");
const isFetchingMails = ref(false);
const mailError = ref(""); // Para capturar errores como 'App Password required'
const isSendingComm = ref(false);
const showMobileHelpModal = ref(false);
const mobileHelpContext = ref('offline'); // 'offline' or 'missing'
const mobileHelpTitle = computed(() => mobileHelpContext.value === 'missing' ? t('ui_mobile_link', 'Vincular Celular') : t('ui_mobile_offline', 'Celular Desconectado'));
const mobileHelpDescription = computed(() => mobileHelpContext.value === 'missing'
    ? t('ui_mobile_pair_desc', 'Para que Fina pueda enviar mensajes y hacer llamadas, necesitas vincular un dispositivo principal.')
    : t('ui_mobile_offline_desc', 'Fina no puede comunicarse con tu celular. Sigue los pasos abajo para reconectar.'));
const showPairingModal = ref(false);
const pairingIP = ref('');
const pairingPort = ref('');
const pairingCode = ref('');
const detectedAndroidVersion = ref(0);
const qrCodeDataURL = ref('');
const contacts = ref({}); // { "Nombre": "Numero" }
const userData = ref({ notes: [], reminders: [] });
const showUniversalPinModal = ref(false);
const universalPinData = ref({ title: "Configuración", device: "Dispositivo", plugin_id: "", ip: "" });
const universalPinInput = ref("");

const installedMessagingApps = ref(['sms']); // IDs de apps instaladas
const selectedMessagingApp = ref('sms'); // ID de app seleccionada

const isSidebarCollapsed = ref(true);
const activeTab = ref("dashboard");
const audioIntensity = ref(0.2);
const speechAnimationInterval = ref(null);
const showDoorbell = ref(false);
const streamUrl = ref("");
const streamKey = ref(0);
const heartbeatSeconds = ref(0);
const showCredits = ref(false);
const showAdvanced = ref(false);
const activeSettingsTab = ref('general');
const activeSettingsDomain = ref(null);
const activeTvRoom = ref('Living');
const roomList = ['Dormitorio', 'Living', 'Comedor', 'Cocina', 'Cobertizo', 'Deco'];
const activeBioTab = ref('huella');
const activeCameraView = ref('grid');
const version = "Fina Ergen v 3.5.8-17 (09/03/2026 09:53)";
const buildDate = "Lun 09 Mar 2026 09:53";

const showOptInModal = ref(false);
const newDetectedApps = ref([]);

// --- CHAT LOG SYSTEM ---
const chatHistory = ref([]);
const addChatMessage = (text, timeout = 7000) => {
    const id = Date.now();
    chatHistory.value.push({
        id: id,
        text: text.startsWith('Fina:') ? text : `Fina: ${text}`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
    if (chatHistory.value.length > 5) chatHistory.value.shift();

    // Auto-eliminar después del tiempo definido (si es > 0)
    if (timeout > 0) {
        setTimeout(() => {
            const index = chatHistory.value.findIndex(m => m.id === id);
            if (index > -1) {
                chatHistory.value.splice(index, 1);
            }
        }, timeout);
    }
};

// --- LOGGING ---
console.log(`🔥 ${version} | Created: ${buildDate}`);


const currentTime = ref("");
const currentDate = ref("");
const weatherTemp = ref(null);
const weatherHumidity = ref(45);
const weatherWind = ref(0);
const weatherFeelsLike = ref(0);
const weatherDesc = ref("Despejado");
const weatherCityName = ref("Buenos Aires");
const weatherForecast = ref([]);
const weatherCode = ref(0);
const isDay = ref(1);
const activeCasaView = ref("main");
const doorbellBattery = ref("90");

const acState = ref({
    power: false,
    temp: 24,
    indoor: 25,
    mode: "cool",
    swing: false,
    turbo: false,
    fan: "auto",
    eco: false,
    display: true,
    sleep: false,
    outdoor: 28,
    humidity: 45,
    watts: 0,
    total_kwh: 0,
    monthly_kwh: 0
});

const activeTvIp = ref(null);
const tvStatuses = ref({});
const scannedDevices = ref([]);
const adbDevices = ref([]);
const mobileHubError = ref(null); // Error visual para el hub
const isScanningNetwork = ref(false);
const activeTvAppsView = ref(false); // New state for toggling Apps view
const activeTvSearch = ref(""); // Búsqueda de apps
const isScanningTv = ref(false); // Para canales o apps

const systemStats = ref({
    cpu: 0,
    ram: { percent: 0, used: 0, total: 0 },
    disk: { percent: 0, free: 0 },
    uptime: "0h 0m"
});

const appMetadata = {
    'youtube': { icon: 'fa-brands fa-youtube', color: 'text-red-500', glow: 'shadow-red-500/40' },
    'netflix': { icon: 'fa-solid fa-n', color: 'text-red-600', glow: 'shadow-red-700/40' },
    'ninja': { icon: 'fa-solid fa-n', color: 'text-red-600', glow: 'shadow-red-700/40' },
    'spotify': { icon: 'fa-brands fa-spotify', color: 'text-green-500', glow: 'shadow-green-500/40' },
    'prime video': { icon: 'fa-brands fa-amazon', color: 'text-blue-400', glow: 'shadow-blue-500/40' },
    'amazonvideo': { icon: 'fa-brands fa-amazon', color: 'text-blue-400', glow: 'shadow-blue-500/40' },
    'disneyplus': { icon: 'fa-solid fa-plus', color: 'text-blue-600', glow: 'shadow-blue-700/40' },
    'twitch': { icon: 'fa-brands fa-twitch', color: 'text-purple-500', glow: 'shadow-purple-500/40' },
    'flow': { icon: 'fa-solid fa-film', color: 'text-cyan-400', glow: 'shadow-cyan-500/40' },
    'mediashell': { icon: 'fa-solid fa-cast', color: 'text-blue-500', glow: 'shadow-blue-500/40' },
    'hbo': { icon: 'fa-solid fa-h', color: 'text-blue-700', glow: 'shadow-blue-900/40' },
    'hbomax': { icon: 'fa-solid fa-h', color: 'text-blue-700', glow: 'shadow-blue-900/40' },
    'apple tv': { icon: 'fa-brands fa-apple', color: 'text-white', glow: 'shadow-white/20' },
    'plex': { icon: 'fa-brands fa-plex', color: 'text-orange-500', glow: 'shadow-orange-500/40' },
    'kodi': { icon: 'fa-solid fa-k', color: 'text-blue-400', glow: 'shadow-blue-500/40' },
    'stremio': { icon: 'fa-solid fa-play', color: 'text-purple-400', glow: 'shadow-purple-500/40' }
};

const openConfigManual = async () => {
    try {
        await invoke('open_manual');
    } catch (e) {
        addChatMessage("❌ Error: " + e, 5000);
    }
};

const filteredTvApps = computed(() => {
    const apps = userSettings.value.tv_apps || {};
    if (!activeTvSearch.value) return apps;
    const search = activeTvSearch.value.toLowerCase();
    const filtered = {};
    Object.keys(apps).forEach(name => {
        if (name.toLowerCase().includes(search)) {
            filtered[name] = apps[name];
        }
    });
    return filtered;
});

const getSystemStats = async () => {
    const pyPath = pythonExecutable.value;
    const scriptPath = `${projectRoot.value}/plugins/system/get_stats.py`;
    try {
        const output = await invoke("execute_shell_command", { command: `timeout 3 ${pyPath} "${scriptPath}"` });
        systemStats.value = JSON.parse(output);
    } catch (e) {
        // console.error("Stats error", e); // Silent fail
        logError(`Stats Error: ${e}`);
    }
};
const sentinelLogs = ref([]);
const showSentinel = ref(false);
const sentinelInput = ref("");
const sentinelHistogram = ref(Array.from({ length: 16 }, () => Math.floor(Math.random() * 90) + 10));
const neuralActivity = ref(35);
const ergenStatus = ref("NOMINAL");
const activeModel = ref("Ergen-3.2-Ultra");
const thoughtStream = ref([
    "Sincronizando núcleos neuronales...",
    "Analizando patrones de comportamiento...",
    "Optimizando respuesta sensorial...",
    "Base de datos Ergen actualizada."
]);

const updateNeuralState = () => {
    setInterval(() => {
        neuralActivity.value = Math.floor(Math.random() * (85 - 20) + 20);
        if (neuralActivity.value > 80) ergenStatus.value = "PENSAMIENTO PROFUNDO";
        else ergenStatus.value = "NOMINAL";

        if (Math.random() > 0.8) {
            const thoughts = [
                "Procesando entrada de voz...",
                t('ui_scanning_nodes', 'Escaneando nodos locales...'),
                "Ajustando parámetros de latencia...",
                "Ergen Core estable.",
                "Actualizando heurísticas...",
                "Refinando modelo predictivo..."
            ];
            thoughtStream.value.unshift(thoughts[Math.floor(Math.random() * thoughts.length)]);
            if (thoughtStream.value.length > 5) thoughtStream.value.pop();
        }
    }, 4000);
};

onMounted(() => {
    startSentinelDemo();
    updateNeuralState();
    syncAllDevices(true);
    syncSystemInfo();

    listen("plugin-request-pin", (event) => {
        console.log("📥 Recibida petición de PIN de plugin:", event.payload);
        universalPinData.value = {
            title: event.payload.title || "Vincular Dispositivo",
            device: event.payload.device || "Android TV",
            plugin_id: event.payload.plugin_id,
            ip: event.payload.ip
        };
        universalPinInput.value = "";
        showUniversalPinModal.value = true;
    });

    listen("plugin-pin-response-status", (event) => {
        if (event.payload.status === "success") {
            addChatMessage("✅ Dispositivo vinculado con éxito.");
            showUniversalPinModal.value = false;
        } else {
            addChatMessage("❌ Error en vinculación: " + event.payload.message);
        }
    });
});

const handleSentinelCommand = async () => {
    if (!sentinelInput.value) return;
    const cmd = sentinelInput.value.toLowerCase().trim();
    addSentinelLog(`> ${cmd}`);

    // Command Logic
    if (cmd === 'help' || cmd === 'ayuda' || cmd === '?') {
        addSentinelLog("[INFO] COMANDOS: stats, logs, scan, block [IP], reset");
    } else if (cmd === 'stats' || cmd === 'estado') {
        addSentinelLog(`[STATS] CPU: ${systemStats.value.cpu?.percent}% | RAM: ${systemStats.value.ram?.percent}%`);
        addSentinelLog(`[SISTEMA] UPTIME: ${systemStats.value.uptime}`);
    } else if (cmd === 'scan' || cmd === 'escanear') {
        addSentinelLog("[SCAN] ESCANEANDO RED LOCAL (NMAP)...");
        try {
            const py = pythonExecutable.value;
            const script = "plugins/system/network_guardian.py";
            const output = await invoke("execute_shell_command", { command: `${py} "${script}" scan` });
            const res = JSON.parse(output);
            if (res.status === 'success') {
                addSentinelLog(`[SCAN] ESCANEO COMPLETO EN ${res.subnet}`);
                addSentinelLog(`[INFO] DISPOSITIVOS DETECTADOS: ${res.hosts_found}`);
                res.ips.slice(0, 5).forEach(ip => addSentinelLog(`[IP] DETECTADA: ${ip}`));
                if (res.ips.length > 5) addSentinelLog(`[INFO] ... Y ${res.ips.length - 5} MÁS.`);
            } else {
                addSentinelLog(`[ERROR] FALLO EN ESCANEO: ${res.message}`);
            }
        } catch (e) {
            addSentinelLog(`[ERROR] SCRIPTERROR: ${e}`);
        }
    } else if (cmd.startsWith('block') || cmd.startsWith('bloquear')) {
        const ip = cmd.split(' ')[1] || "DESCONOCIDA";
        addSentinelLog(`[FIREWALL] BLOQUEANDO IP: ${ip}`);
        addSentinelLog(`[SUCCESS] IP ${ip} AÑADIDA A LISTA NEGRA.`);
    } else if (cmd === 'reset' || cmd === 'reiniciar') {
        addSentinelLog("[DANGER] REINICIANDO NÚCLEO DE SEGURIDAD...");
        setTimeout(() => location.reload(), 1500);
    } else if (cmd === 'logs') {
        fetchSystemLogs();
        addSentinelLog("[INFO] SINCRONIZANDO LOGS DE SISTEMA.");
    } else {
        addSentinelLog(`[ERROR] COMANDO '${cmd}' NO RECONOCIDO.`);
    }

    logVoice(sentinelInput.value); // Keep logging to file
    sentinelInput.value = "";
};
const addSentinelLog = (msg) => {
    sentinelLogs.value.unshift({ time: new Date().toLocaleTimeString(), msg });
    if (sentinelLogs.value.length > 20) sentinelLogs.value.pop();
};
// LOGGING SYSTEM
const logVoice = async (cmd) => {
    try {
        const py = pythonExecutable.value;
        const script = `${projectRoot.value}/plugins/system/log_manager.py`;
        await invoke("execute_shell_command", { command: `${py} "${script}" log_cmd "${cmd}"` });
        addSentinelLog(`[VOZ] ${cmd}`);
    } catch (e) { console.error(e); }
};

const logError = async (err) => {
    try {
        const py = pythonExecutable.value;
        const script = `${projectRoot.value}/plugins/system/log_manager.py`;
        await invoke("execute_shell_command", { command: `${py} "${script}" log_err "${err}"` });
        addSentinelLog(`[ERROR] ${err}`);
    } catch (e) { console.error(e); }
};

const fetchSystemLogs = async () => {
    try {
        const py = pythonExecutable.value;
        const script = `${projectRoot.value}/plugins/system/log_manager.py`;
        const output = await invoke("execute_shell_command", { command: `${py} "${script}" read` });
        if (output) {
            const lines = output.split('\n').filter(l => l.trim());
            // Merge with sentinelLogs but avoid dups? simpler to just prepend new ones if possible.
            // For now, let's just push them if they are not there.
            // Actually, let's just use sentinelLogs for live feed and fetchSystemLogs for history if needed.
            // Better: addSentinelLog adds to UI. Let's make fetchSystemLogs parse and add to UI.
            lines.forEach(l => {
                if (!sentinelLogs.value.find(existing => existing.raw === l)) {
                    sentinelLogs.value.unshift({ time: l.substring(1, 20), msg: l.substring(22), raw: l });
                }
            });
            // Limitar historial para no saturar memoria
            if (sentinelLogs.value.length > 50) {
                sentinelLogs.value = sentinelLogs.value.slice(0, 50);
            }
        }
    } catch (e) { }
};

const startSentinelDemo = () => {
    // Initial fetch
    fetchSystemLogs();

    setInterval(() => {
        if (!showSentinel.value) return;

        // Random fake traffic + Real polling
        if (Math.random() > 0.7) fetchSystemLogs();

        // Update histogram
        sentinelHistogram.value = sentinelHistogram.value.map(v => {
            const delta = (Math.random() * 20) - 10;
            return Math.max(10, Math.min(100, v + delta));
        });

        const ips = ["127.0.0.1", "192.168.0.1"]; // Placeholder, should be loaded from settings if needed
        const threats = ["ESCANEO PUERTOS", "INTENTO SSH", "PING FLOOD", "PAQUETE DESCARTADO", "FALLO AUTH"];
        const randIp = ips[Math.floor(Math.random() * ips.length)];
        const randThreat = threats[Math.floor(Math.random() * threats.length)];

        // Only show fake if no real logs recently? No, mix them.
        addSentinelLog(`[SISTEMA] ${randThreat} DESDE ${randIp}`);
    }, 2000);
};


// --- EMAIL SYSTEM (LOCAL) ---
// Obtiene correos directamente de Gmail usando credenciales locales en settings.json.
// Independiente de la conexión del celular.
const recentEmails = ref([]);
const fetchRecentEmails = async () => {
    if (isFetchingMails.value) return;
    isFetchingMails.value = true;
    mailError.value = ""; // Limpiar error previo
    try {
        const py = pythonExecutable.value;
        const script = `${projectRoot.value}/scripts/mail_reader.py`;
        // Timeout de 15s para evitar cuelgues de red/auth
        const output = await invoke("execute_shell_command", { command: `timeout 15 ${py} "${script}"` });
        const res = JSON.parse(output);
        if (res.status === 'success') {
            recentEmails.value = res.emails;
        } else {
            console.error("Mail Reader Error:", res.message);
            mailError.value = res.message;
            // Si el error es de auth, vaciamos la lista para mostrar el mensaje de error en la UI
            if (res.error_type === 'auth_app_password') {
                recentEmails.value = [];
            }
        }
    } catch (e) {
        console.error("Error fetching emails:", e);
        mailError.value = "Error de conexión con el servidor de correo.";
    } finally {
        isFetchingMails.value = false;
    }
};

const sendMobileSMS = async (number, msg, forceApp = null) => {
    if (isSendingComm.value && !forceApp) return;
    isSendingComm.value = true;

    const appId = forceApp || selectedMessagingApp.value;
    const appInfo = SUPPORTED_MESSAGING_APPS[appId] || SUPPORTED_MESSAGING_APPS['sms'];

    // 1. SI ES SMS, REQUERIMOS DISPOSITIVO FÍSICO (ADB)
    if (appId === 'sms') {
        let dev = linkedMobileDevice.value;

        // INTENTO DE RECUPERACIÓN: Si no hay dispositivo vinculado, buscar cualquiera en ADB
        if (!dev) {
            try {
                const adbOutput = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
                const lines = adbOutput.split('\n').filter(line => line.includes('\tdevice'));
                if (lines.length > 0) {
                    const deviceId = lines[0].split('\t')[0];
                    // Si es IP, la usamos. Si es serial USB, también sirve.
                    dev = { ip: deviceId, name: 'Android Device' };
                    console.log("⚠️ Usando dispositivo ADB detectado al vuelo:", dev);
                }
            } catch (e) {
                console.warn("Fallo detección ADB al vuelo:", e);
            }
        }

        if (!dev) {
            notifyFina(t("ui_no_mobile_linked", "SIN CELULAR VINCULADO"));
            isSendingComm.value = false;
            mobileHelpContext.value = 'missing';
            showMobileHelpModal.value = true;
            return;
        }

        await invoke("execute_shell_command", {
            command: `echo "[$(date -uIs)] [INFO] [JS] Iniciando proceso SMS para ${number}" >> ./Logs/messaging_debug.log`
        }).catch(() => { });

        finaState.value.process = `CONECTANDO CON DISPOSITIVO...`;

        try {
            // 1. Verificar si el ID necesita conexión (si es IP)
            if (dev.ip.includes('.')) {
                const check = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
                if (!check.includes(dev.ip)) {
                    await invoke("execute_shell_command", { command: `timeout 3 adb connect ${dev.ip.includes(':') ? dev.ip : dev.ip + ':5555'}` }).catch(() => { });
                }
            }

            const py = pythonExecutable.value;
            const script = `${projectRoot.value}/plugins/system/mobile_hub.py`;

            // 2. Ejecutar envío y CAPTURAR salida
            const rawOutput = await invoke("execute_shell_command", {
                command: `timeout 15 ${py} "${script}" send_sms --ip ${dev.ip} --number "${number}" --msg "${msg}"`
            });

            // Limpiar posible basura antes/después del JSON
            const jsonStart = rawOutput.indexOf('{');
            const jsonEnd = rawOutput.lastIndexOf('}') + 1;
            const output = (jsonStart !== -1 && jsonEnd !== -1) ? rawOutput.substring(jsonStart, jsonEnd) : rawOutput;

            await invoke("execute_shell_command", {
                command: `echo "[$(date -uIs)] [INFO] [JS] Respuesta de Python (Limpia): ${output.trim().replace(/"/g, '\\"')}" >> ./Logs/messaging_debug.log`
            }).catch(() => { });

            const response = JSON.parse(output);

            if (response.status === 'success') {
                notifyFina(t("ui_sms_processed", "SMS TRAMITADO"));
                addChatMessage(`SMS a ${number}: "${msg}" (Check celular)`);
            } else {
                throw new Error(response.message || "Error desconocido en Python");
            }
        } catch (e) {
            console.error("Error SMS:", e);
            finaState.value.process = t("proc_err_send", "ERROR EN ENVÍO");
            notifyFina(t("ui_sms_failed", "FALLO AL ENVIAR SMS"));

            await invoke("execute_shell_command", {
                command: `echo "[$(date -uIs)] [ERROR] [JS] Fallo en sendMobileSMS: ${e.message.replace(/"/g, '\\"')}" >> ./Logs/messaging_debug.log`
            }).catch(() => { });
        } finally {
            isSendingComm.value = false;
            setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 3000);
        }
    }
    // 2. SI ES WHATSAPP, USAMOS EL NUEVO SISTEMA INVISIBLE
    else if (appId === 'whatsapp') {
        try {
            console.log(`Enviando WhatsApp a: ${number}`);
            finaState.value.process = `ENVIANDO WHATSAPP...`;

            const result = await sendWhatsAppMessage(number, msg);

            if (result.success) {
                notifyFina(t("ui_whatsapp_sent", "WHATSAPP ENVIADO"));
                addChatMessage(`WhatsApp enviado a ${number}: "${msg}"`);
                invoke("execute_shell_command", {
                    command: `${pythonExecutable.value} ${projectRoot.value}/utils.py speak "Mensaje de WhatsApp enviado correctamente."`
                }).catch(() => { });
            } else {
                await logMsg(`ERROR EN ENVÍO: ${result.error}`, "ERROR");
                await invoke("execute_shell_command", {
                    command: `${pythonExecutable.value} ${projectRoot.value}/utils.py speak "No pude enviar el mensaje de WhatsApp. Revisa los logs."`
                }).catch(() => { });
            }

        } catch (e) {
            console.error("Error WhatsApp:", e);
            finaState.value.process = t("proc_err_whatsapp", "ERROR WHATSAPP");
        } finally {
            isSendingComm.value = false;
            setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 2000);
        }
    }
    // 3. OTRAS APPS WEB (Telegram, etc) - Por ahora no implementadas
    else {
        notifyFina(`${appInfo.name.toUpperCase()} NO IMPLEMENTADO AÚN`);
        isSendingComm.value = false;
    }
};


// Detectar versión de Android del dispositivo conectado por USB
const detectAndroidVersion = async () => {
    try {
        const versionOutput = await invoke("execute_shell_command", {
            command: "timeout 3 adb shell getprop ro.build.version.release"
        });
        const version = parseInt(versionOutput.trim());
        detectedAndroidVersion.value = version;
        console.log(`📱 Android detectado: ${version}`);
        return version;
    } catch (e) {
        console.warn("No se pudo detectar versión de Android:", e);
        return 0;
    }
};

// Generar QR para emparejamiento Android 14+
const generatePairingQR = async () => {
    try {
        // 1. Obtener IP local de la PC
        const ipCmd = "ip -4 addr show | grep -oP '(?<=inet\\s)\\d+(\\.\\d+){3}' | grep -v '127.0.0.1' | head -n 1";
        const localIP = (await invoke("execute_shell_command", { command: ipCmd })).trim();

        if (!localIP) {
            throw new Error("No se pudo detectar la IP local");
        }

        // 2. Generar código de emparejamiento aleatorio (6 dígitos)
        const pairingCodeGenerated = Math.floor(100000 + Math.random() * 900000).toString();

        // 3. Puerto de emparejamiento (ADB usa 37000-44000 típicamente)
        const pairingPortGenerated = '37847'; // Puerto fijo para simplificar

        console.log(`📱 Generando QR: ${localIP}:${pairingPortGenerated} con código ${pairingCodeGenerated}`);

        // 4. Iniciar servidor de emparejamiento ADB en background
        // El formato es: adb pair <IP>:<PORT> <CODE>
        // Pero necesitamos que ADB actúe como servidor, no cliente
        // Para eso usamos: adb pair <PORT> y esperamos que el celular se conecte
        const pairServerCmd = `timeout 60 adb pair ${pairingPortGenerated} ${pairingCodeGenerated}`;

        // Ejecutar en background
        invoke("execute_shell_command", { command: pairServerCmd }).catch(() => {
            console.log("Servidor de emparejamiento finalizado");
        });

        // 5. Generar QR con el formato correcto para Android
        // El formato del QR para ADB wireless es:
        // WIFI:T:ADB;S:<IP>:<PORT>;P:<CODE>;;
        const qrData = `WIFI:T:ADB;S:${localIP}:${pairingPortGenerated};P:${pairingCodeGenerated};;`;

        // 6. Generar imagen QR
        const qrImageURL = await QRCode.toDataURL(qrData, {
            width: 300,
            margin: 2,
            color: {
                dark: '#06b6d4',  // cyan-500
                light: '#0a0a15'  // background
            }
        });

        qrCodeDataURL.value = qrImageURL;
        pairingIP.value = localIP;
        pairingPort.value = pairingPortGenerated;
        pairingCode.value = pairingCodeGenerated;

        const hint = "Escanea el código QR desde tu celular para emparejar.";
        invoke("execute_shell_command", {
            command: `${pythonExecutable.value} ${projectRoot.value}/utils.py speak "${hint}"`
        }).catch(() => { });

        return true;
    } catch (e) {
        console.error("Error generando QR:", e);
        const hint = "No pude generar el código QR. Verifica la conexión de red.";
        invoke("execute_shell_command", {
            command: `${pythonExecutable.value} ${projectRoot.value}/utils.py speak "${hint}"`
        }).catch(() => { });
        return false;
    }
};

// Emparejar dispositivo Android 14+ usando wireless debugging
const pairAndroid14Device = async () => {
    // Esta función ahora solo se llama cuando el usuario confirma el emparejamiento
    // El QR ya fue generado y escaneado
    return true;
};

// Función para reintentar conexión después de que el usuario siga las instrucciones

const submitAuthPassword = async () => {
    if (!authPassword.value) return;
    try {
        await fetch("http://127.0.0.1:18000/api/auth/password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password: authPassword.value })
        });
        authPassword.value = "";
        finaState.value.authError = false;
        // La UI se ocultará cuando el polling detecte que show_password_field es false
    } catch (e) {
        console.error("Error submitting password:", e);
    }
};

// --- APP DETECTION ---
const logPerf = (msg) => {
    const timestamp = new Date().toISOString();
    const logMsg = `[PERF_LOG][${timestamp}] ${msg}`;
    console.log(logMsg);
    invoke("execute_shell_command", {
        command: `echo "${logMsg}" >> ./Logs/perf_debug.log`
    }).catch(() => { });
};

// --- APP DETECTION (PURE LIVE - NO SETTINGS DEPENDENCY) ---
const detectMessagingApps = async () => {
    try {
        logPerf("🕵️ [LIVE] Escaneando apps instaladas en celular...");

        // SIEMPRE empezamos con SMS (nativo)
        installedMessagingApps.value = ['sms'];

        // Escaneo ADB en tiempo real
        const output = await invoke("execute_shell_command", { command: "timeout 4 adb shell pm list packages" });

        const detectedNow = [];
        Object.values(SUPPORTED_MESSAGING_APPS).forEach(app => {
            if (app.id === 'sms') return; // SMS ya está
            if (output.includes(`package:${app.package}`)) {
                detectedNow.push(app.id);
                logPerf(`✓ Detectada: ${app.name}`);
            }
        });

        // Actualizar lista visual DIRECTAMENTE con lo detectado
        installedMessagingApps.value = ['sms', ...detectedNow];

        logPerf(`[LIVE] Apps disponibles ahora: ${installedMessagingApps.value.join(', ')}`);

    } catch (e) {
        logPerf(`[LIVE] ADB no disponible. Solo SMS estará disponible.`);
        installedMessagingApps.value = ['sms'];
    }
};

// ELIMINADO: Ya no hay vinculación manual, todo es detección automática


const retryMobileConnection = async () => {
    const dev = linkedMobileDevice.value;
    if (!dev || !dev.ip) {
        finaState.value.process = t("proc_no_device", "NO HAY DISPOSITIVO CONFIGURADO");
        return;
    }

    finaState.value.process = `BUSCANDO ${dev.name.toUpperCase()}...`;

    // 0. INTENTO DE RECONEXIÓN INALÁMBRICA RÁPIDA (ANTES DE PEDIR CABLE)
    try {
        console.log(`Intentando reconexión inalámbrica a ${dev.ip}...`);
        await invoke("execute_shell_command", { command: `timeout 3 adb connect ${dev.ip}:5555` }).catch(() => { });

        // Verificar si revivió
        const quickCheck = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
        if (quickCheck.includes(dev.ip) && !quickCheck.includes("offline")) {
            finaState.value.process = `${dev.name.toUpperCase()} RECONECTADO`;
            detectMessagingApps(); // Detectar apps al conectar
            addChatMessage(`${dev.name} reconectado inalámbricamente con éxito.`);

            showPairingModal.value = false;
            showMobileHelpModal.value = false;

            setTimeout(() => {
                showCommModal.value = true;
                if (finaState.value.process.includes("CONECTADO") || finaState.value.process.includes("RECONECTADO"))
                    finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");
            }, 1500);
            return; // ¡ÉXITO SIN CABLE!
        }
    } catch (e) {
        console.log("Reconexión rápida falló, procediendo a flujo USB/QR...");
    }

    // SI LLEGAMOS ACÁ, FALLÓ LA RECONEXIÓN AUTOMÁTICA -> PEDIMOS CABLE
    finaState.value.process = t("proc_usb_req", "SOLICITANDO CONEXIÓN USB...");

    try {
        // 1. Verificar si hay algún dispositivo conectado por USB
        const devicesOut = await invoke("execute_shell_command", { command: "timeout 3 adb devices" });
        console.log("📱 Dispositivos ADB:", devicesOut);

        let usbDeviceId = null;
        let deviceStatus = null;

        const lines = devicesOut.split('\n');
        for (const line of lines) {
            if (!line.trim() || line.includes('List of devices')) continue;
            if (line.includes('.') || line.includes(':')) continue; // Excluir IPs

            const match = line.match(/^([^\s]+)\s+(device|unauthorized)/);
            if (match) {
                usbDeviceId = match[1];
                deviceStatus = match[2];
                break;
            }
        }

        if (!usbDeviceId) {
            // No hay USB tampoco -> Error real
            throw new Error("No hay dispositivo USB conectado");
        }

        console.log(`📱 Dispositivo USB encontrado: ${usbDeviceId} (${deviceStatus})`);

        // 2. Si está "unauthorized", esperar a que el usuario autorice
        if (deviceStatus === 'unauthorized') {
            finaState.value.process = t("proc_wait_auth", "ESPERANDO AUTORIZACIÓN EN EL CELULAR...");
            const hint = "Por favor, acepta la autorización de depuración USB en la pantalla de tu celular.";
            invoke("execute_shell_command", {
                command: `${pythonExecutable.value} ${projectRoot.value}/utils.py speak "${hint}"`
            }).catch(() => { });

            let authorized = false;
            for (let i = 0; i < 15; i++) {
                await new Promise(resolve => setTimeout(resolve, 1000));
                const checkDevices = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
                if (checkDevices.includes(`${usbDeviceId}\tdevice`) || checkDevices.includes(`${usbDeviceId} device`)) {
                    authorized = true;
                    break;
                }
            }
            if (!authorized) throw new Error("No se autorizó la depuración USB");
        }

        // 3. Detectar versión (informativo)
        const androidVersion = await detectAndroidVersion();

        // 4. MODO ROBUSTO: Activar tcpip 5555
        finaState.value.process = t("proc_wifi_config", "CONFIGURANDO MODO INALÁMBRICO...");
        await invoke("execute_shell_command", { command: `timeout 4 adb -s ${usbDeviceId} tcpip 5555` }).catch(() => { });
        await new Promise(resolve => setTimeout(resolve, 2000));

        // 5. Intentar conectar
        finaState.value.process = `CONECTANDO A ${dev.ip}...`;
        await invoke("execute_shell_command", { command: `timeout 4 adb connect ${dev.ip}:5555` }).catch(() => { });

        // 6. Verificar estado final
        const finalDevicesCheck = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
        const isListed = finalDevicesCheck.includes(dev.ip);
        const isOffline = finalDevicesCheck.includes("offline") || finalDevicesCheck.includes("unauthorized");

        if (isListed && !isOffline) {
            finaState.value.process = `${dev.name.toUpperCase()} CONECTADO`;
            detectMessagingApps(); // Detectar apps al conectar
            const hint = `Conexión restablecida. Ya puedes desconectar el cable USB.`;
            invoke("execute_shell_command", {
                command: `${pythonExecutable.value} ${projectRoot.value}/utils.py speak "${hint}"`
            }).catch(() => { });

            addChatMessage(`Conexión con ${dev.name} restablecida. Puedes quitar el cable.`);

            showPairingModal.value = false;
            showMobileHelpModal.value = false;

            setTimeout(() => {
                showCommModal.value = true;
                if (finaState.value.process.includes("CONECTADO")) finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");
            }, 2000);
            return;
        }

        // Fallback QR Android 14+
        if (androidVersion >= 14) {
            const wirelessCheck = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
            if (!wirelessCheck.includes(dev.ip)) {
                await generatePairingQR();
                showPairingModal.value = true;
                const hint = `${dev.name} usa Android ${androidVersion}. La conexión automática falló. Escanea el QR.`;
                invoke("execute_shell_command", {
                    command: `${pythonExecutable.value} ${projectRoot.value}/utils.py speak "${hint}"`
                }).catch(() => { });
                return;
            }
        }

        throw new Error("No se pudo establecer conexión inalámbrica");

    } catch (e) {
        console.error("Error conexión:", e);
        // Solo mostrar error si falló también la conexión USB
        if (e.message.includes("No hay dispositivo USB conectado")) {
            finaState.value.process = t("proc_wait_usb", "ESPERANDO CONEXIÓN USB...");
            // No hacemos nada, el usuario verá el modal pidiendo el cable
        } else {
            finaState.value.process = t("proc_err_conn", "ERROR DE CONEXIÓN");
        }
    }
};;;

const initiateMobileCall = async (number) => {
    if (isSendingComm.value) return;
    isSendingComm.value = true;
    const dev = linkedMobileDevice.value;
    if (!dev) {
        notifyFina(t("ui_no_mobile_linked", "SIN CELULAR VINCULADO"));
        isSendingComm.value = false;
        return;
    }

    finaState.value.process = `LLAMANDO VÍA ${dev.name.toUpperCase()}...`;

    try {
        const py = pythonExecutable.value;
        const script = `${projectRoot.value}/plugins/system/mobile_hub.py`;

        // 1. Try Connection (Blocking wait con timeout)
        if (dev.ip) {
            await invoke("execute_shell_command", { command: `timeout 4 adb connect ${dev.ip}` }).catch(() => { });
        }

        // 2. Check connectivity
        const devicesOut = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
        const isListed = devicesOut.includes(dev.ip);
        const isOffline = devicesOut.includes("offline") || devicesOut.includes("unauthorized");

        if (!dev.ip || !isListed || isOffline) {
            throw new Error("Device offline");
        }

        // Call con timeout
        await invoke("execute_shell_command", { command: `timeout 15 ${py} "${script}" make_call --ip ${dev.ip} --number "${number}"` });
        notifyFina(t("ui_call_in_progress", "LLAMADA EN PROCESO"));
    } catch (e) {
        console.error("Call Error:", e);
        mobileHubError.value = `⚠️ Error: ${dev.name} desconectado.`;
        finaState.value.process = `ERROR AL LLAMAR`;

        // Vocal feedback e instrucciones
        const hint = `No puedo iniciar la llamada porque el celular ${dev.name} está fuera de línea. Revisa la guía de conexión en pantalla.`;
        invoke("execute_shell_command", {
            command: `${pythonExecutable.value} ${projectRoot.value}/utils.py speak "${hint}"`
        }).catch(() => { });

        // MOSTRAR AYUDA VISUAL PROACTIVA
        mobileHelpContext.value = 'offline';
        showMobileHelpModal.value = true;

        setTimeout(() => {
            mobileHubError.value = null;
            if (finaState.value.process === 'ERROR AL LLAMAR') finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");
        }, 8000);
    } finally {
        isSendingComm.value = false;
    }
};

const showMarket = ref(false);
const marketPlugins = ref([]);
const isMarketLoading = ref(false);

const openPluginStore = async () => {
    finaState.value.process = t("proc_open_market", "ABRIENDO MARKET DE PLUGINS");
    showMarket.value = true;
    isMarketLoading.value = true;

    try {
        // Obtener lista de instalados primero
        const localResp = await fetch("http://127.0.0.1:18000/api/plugins");
        const installedLocal = localResp.ok ? await localResp.json() : [];
        const installedNames = installedLocal.map(p => p.name.toLowerCase());

        const categories = ["TVs", "Decos", "Doorbells", "AirConditioning"];
        const plugins = [];

        for (const cat of categories) {
            const resp = await fetch(`https://api.github.com/repos/dankopetro/Fina-Plugins-Market/contents/${cat}`);
            if (!resp.ok) continue;
            const items = await resp.json();

            for (const brand of items) {
                if (brand.type === 'dir') {
                    // Fetch models inside brand
                    const modelResp = await fetch(brand.url);
                    const models = await modelResp.json();
                    for (const model of models) {
                        if (model.type === 'dir') {
                            const pName = model.name;
                            plugins.push({
                                name: pName,
                                brand: brand.name,
                                category: cat,
                                path: `${brand.name}/${model.name}`,
                                installed: installedNames.includes(pName.toLowerCase())
                            });
                        }
                    }
                }
            }
        }
        marketPlugins.value = plugins;
        finaState.value.process = t("proc_market_ready", "MARKET LISTO");
    } catch (e) {
        console.error("Market error:", e);
        finaState.value.process = t("proc_err_market", "ERROR AL CARGAR MARKET");
    } finally {
        isMarketLoading.value = false;
    }
};

const installMarketPlugin = async (plugin) => {
    finaState.value.process = `INSTALANDO ${plugin.name.toUpperCase()}...`;
    try {
        const res = await invoke("install_market_plugin", {
            category: plugin.category,
            subpath: plugin.path
        });
        addChatMessage(`Plugin ${plugin.name} instalado con éxito.`);
        finaState.value.process = t("proc_inst_done", "INSTALACIÓN COMPLETADA");
        setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 2000);
    } catch (e) {
        console.error("Install error:", e);
        addChatMessage("Error al instalar plugin: " + e);
        finaState.value.process = t("proc_err_inst", "ERROR EN INSTALACIÓN");
    }
};

const isTvConnected = computed(() => {
    // If we have an active IP and it is marked as true in statuses
    if (!activeTvIp.value) return false;
    // Check if the current room matches the active IP (consistency check)
    const roomTv = userSettings.value.tvs?.find(t => t.room === activeTvRoom.value);
    if (roomTv && roomTv.ip !== activeTvIp.value) return false;

    // Check status map
    if (activeTvIp.value && tvStatuses.value[activeTvIp.value]) return true;

    return false;
});
const assigningDeviceIp = ref(null); // Track which device is opening the assignment menu
const customDeviceName = ref(""); // Temporary hold for custom name input
const customDeviceRoom = ref("Living"); // Temporary hold for room assignment

// --- TIMER SYSTEM ---
const timerState = reactive({
    active: false,
    duration: 0,
    remaining: 0,
    label: "",
    interval: null,
    lastId: null
});

const startVisualTimer = (duration, label) => {
    if (timerState.interval) clearInterval(timerState.interval);
    timerState.active = true;
    timerState.duration = duration;
    timerState.remaining = duration;
    timerState.label = label;

    timerState.interval = setInterval(() => {
        timerState.remaining--;
        if (timerState.remaining <= 0) {
            clearInterval(timerState.interval);
            timerState.label = "¡TIEMPO CUMPLIDO!";
            timerState.remaining = 0;

            // Mantener mensaje final visible 5 segundos
            setTimeout(() => {
                stopVisualTimer();
            }, 5000);
        }
    }, 1000);
};

const stopVisualTimer = () => {
    timerState.active = false;
    if (timerState.interval) clearInterval(timerState.interval);
};

// Formato MM:SS
const formatTimer = computed(() => {
    const m = Math.floor(timerState.remaining / 60).toString().padStart(2, '0');
    const s = Math.floor(timerState.remaining % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
});

// Porcentaje para círculo SVG
const timerProgress = computed(() => {
    if (!timerState.duration) return 0;
    return (timerState.remaining / timerState.duration) * 283; // 283 es perímetro aprox r=45
});

// Watcher para sincronizar activeTvIp con la habitación seleccionada
watch([activeTvRoom, () => userSettings.value.tvs], () => {
    if (userSettings.value.tvs) {
        const tv = userSettings.value.tvs.find(t => t.room === activeTvRoom.value);
        if (tv) {
            // ONLY set IP if TV is enabled
            if (tv.enabled !== false) {
                activeTvIp.value = tv.ip;
                // Trigger detection for this specific IP
                detectTvIp(true);
            } else {
                activeTvIp.value = null; // Explicitly null if disabled
            }
        } else {
            activeTvIp.value = null;
        }
    }
}, { deep: true, immediate: true });

const deviceTypesList = [
    { id: 'TV', label: 'Smart TV', icon: 'fa-tv', color: 'text-purple-400', bg: 'bg-purple-500/10 hover:bg-purple-500/20' },
    { id: 'Aire', label: 'Climatización', icon: 'fa-snowflake', color: 'text-cyan-400', bg: 'bg-cyan-500/10 hover:bg-cyan-500/20' },
    { id: 'Luz', label: 'Iluminación', icon: 'fa-lightbulb', color: 'text-yellow-400', bg: 'bg-yellow-500/10 hover:bg-yellow-500/20' },
    { id: 'Enchufe', label: 'Enchufe', icon: 'fa-plug', color: 'text-green-400', bg: 'bg-green-500/10 hover:bg-green-500/20' },
    { id: 'Camara', label: 'Cámara', icon: 'fa-video', color: 'text-red-400', bg: 'bg-red-500/10 hover:bg-red-500/20' },
    { id: 'Robot', label: 'Robot', icon: 'fa-robot', color: 'text-indigo-400', bg: 'bg-indigo-500/10 hover:bg-indigo-500/20' },
    { id: 'Cerradura', label: 'Cerradura', icon: 'fa-lock', color: 'text-orange-400', bg: 'bg-orange-500/10 hover:bg-orange-500/20' },
    { id: 'Celular', label: 'Celular', icon: 'fa-mobile-screen', color: 'text-pink-400', bg: 'bg-pink-500/10 hover:bg-pink-500/20' },
    { id: 'PC', label: 'PC/Tablet', icon: 'fa-laptop', color: 'text-slate-300', bg: 'bg-slate-500/10 hover:bg-slate-500/20' },
    { id: 'Motor', label: 'Motor/Persiana', icon: 'fa-gears', color: 'text-zinc-400', bg: 'bg-zinc-500/10 hover:bg-zinc-500/20' },
    { id: 'Solar', label: 'Panel Solar', icon: 'fa-solar-panel', color: 'text-amber-400', bg: 'bg-amber-500/10 hover:bg-amber-500/20' },
    { id: 'Sensor', label: 'Sensor', icon: 'fa-rss', color: 'text-blue-400', bg: 'bg-blue-500/10 hover:bg-blue-500/20' },
    { id: 'Audio', label: 'Altavoz', icon: 'fa-music', color: 'text-violet-400', bg: 'bg-violet-500/10 hover:bg-violet-500/20' },
    { id: 'Router', label: 'Router/AP', icon: 'fa-route', color: 'text-indigo-300', bg: 'bg-indigo-500/10 hover:bg-indigo-500/20' },
    { id: 'Deco', label: 'Decodificador', icon: 'fa-box', color: 'text-pink-300', bg: 'bg-pink-500/10 hover:bg-pink-500/20' },
    { id: 'Otro', label: 'Personalizado', icon: 'fa-pen', color: 'text-white', bg: 'bg-white/10 hover:bg-white/20' }
];

const scanNetwork = async () => {
    finaState.value.process = t("proc_scanning_net", "ESCANEANDO RED...");
    isScanningNetwork.value = true;
    try {
        // Usar comando Tauri directo (Rust) que conoce la ruta real del bundle
        const output = await invoke("scan_network_devices");
        scannedDevices.value = JSON.parse(output);
        console.log("Red escaneada:", scannedDevices.value);
        finaState.value.process = `DETECTADOS ${scannedDevices.value.length} DISPOSITIVOS`;
        syncDevicesWithSettings();
    } catch (error) {
        console.error("Error escaneando red:", error);
        finaState.value.process = t("proc_err_scan", "ERROR AL ESCANEAR");
        addChatMessage(`Fina: ⚠ No pude escanear la red: ${error}`);
    } finally {
        isScanningNetwork.value = false;
        setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 3000);
    }
};

const networkStatusMessage = computed(() => {
    return scannedDevices.value.length > 0
        ? `${scannedDevices.value.length} Dispositivos en red`
        : 'Escanee para ver dispositivos';
});

const syncDevicesWithSettings = () => {
    // Check if scanned IPs match known TVs or ACs in settings
    scannedDevices.value.forEach(dev => {
        // Check TVs
        if (userSettings.value.tvs) {
            const knownTv = userSettings.value.tvs.find(tv => tv.ip === dev.ip);
            if (knownTv) {
                dev.assignedType = 'TV';
                dev.assignedName = knownTv.name || 'TV';
                dev.assignedRoom = knownTv.room;
            }
        }
        // Check AC
        if (userSettings.value.apis?.AC_IP === dev.ip) {
            dev.assignedType = 'Aire';
            dev.assignedName = 'Principal';
        }

        // Check Generic Devices
        if (userSettings.value.devices) {
            const knownDev = userSettings.value.devices.find(d => d.ip === dev.ip || (d.mac && d.mac === dev.mac));
            if (knownDev) {
                dev.assignedType = knownDev.type;
                dev.assignedName = knownDev.name;
                dev.isPrimary = knownDev.isPrimary || false;
            }
        }
    });
};

const assignDeviceType = (device, type, name) => {
    // Handle 'Otro' / Custom input flow
    if (type === 'Otro' && !name) {
        device.pendingType = 'Otro';
        const vendorName = device.vendor || "Dispositivo";
        customDeviceName.value = vendorName.split(' ')[0] + " 1";
        return; // Wait for user input
    }

    // 1. GLOBAL CLEANUP: Remove this IP from all lists to avoid duplicates or type conflicts
    // Remove from TVs
    if (userSettings.value.tvs) {
        // Also remove if room matches target room (to enforce 1 TV per room), but only if we are assigning a TV
        if (type === 'TV') {
            userSettings.value.tvs = userSettings.value.tvs.filter(t => t.ip !== device.ip && t.room !== customDeviceRoom.value);
        } else {
            userSettings.value.tvs = userSettings.value.tvs.filter(t => t.ip !== device.ip);
        }
    }
    // Remove from AC
    if (userSettings.value.apis?.AC_IP === device.ip) {
        userSettings.value.apis.AC_IP = "";
    }
    // Remove from Generic Devices
    if (userSettings.value.devices) {
        userSettings.value.devices = userSettings.value.devices.filter(d => d.ip !== device.ip);
    }

    // 2. ASSIGN NEW TYPE
    if (type === 'TV') {
        if (!userSettings.value.tvs) userSettings.value.tvs = [];
        userSettings.value.tvs.push({
            ip: device.ip,
            mac: device.mac || "",
            name: name || customDeviceName.value || `TV ${customDeviceRoom.value} `,
            room: customDeviceRoom.value || "Living",
            enabled: true
        });
        if (activeTvRoom.value === customDeviceRoom.value) {
            activeTvIp.value = device.ip;
        }
    } else if (type === 'Aire') {
        if (!userSettings.value.apis) userSettings.value.apis = {};
        userSettings.value.apis.AC_IP = device.ip;
    } else {
        // Generic Devices
        if (!userSettings.value.devices) userSettings.value.devices = [];
        userSettings.value.devices.push({
            ip: device.ip,
            mac: device.mac || "",
            type: type === 'Otro' ? 'Personalizado' : type,
            name: (type === 'Celular' && customDeviceName.value) ? customDeviceName.value : (name || type),
            icon: deviceTypesList.find(t => t.id === type)?.icon || 'fa-circle-question'
        });
    }

    // Common Cleanup
    saveSettings();
    syncDevicesWithSettings(); // Re-sync to update UI
    device.pendingType = null;
    device.pendingRoom = null;
    assigningDeviceIp.value = null; // Close menu

    finaState.value.process = t("proc_dev_assigned", "DISPOSITIVO ASIGNADO");
    setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 2000);
};

const weatherDisplay = computed(() => {
    if (weatherTemp.value === null || weatherTemp.value === "--") return "--";
    return `${weatherTemp.value}°C`;
});

// --- COMMUNICATION MODAL STATE ---
const showCommModal = ref(false);
const commMode = ref('sms'); // 'sms' or 'call'
const commTarget = ref('');
const commBody = ref('');

const openCommModal = (mode) => {
    commMode.value = mode;
    commTarget.value = '';
    commBody.value = '';
    showCommModal.value = true;
};

const sendCommAction = async () => {
    if (!commTarget.value) return;

    // RESOLVER NOMBRE A NÚMERO
    let target = commTarget.value.trim();
    const contactMatch = Object.keys(contacts.value).find(name =>
        name.toLowerCase() === target.toLowerCase()
    );

    if (contactMatch) {
        console.log(`🔍 Resolviendo contacto "${target}" -> ${contacts.value[contactMatch]} `);
        target = contacts.value[contactMatch];
    }

    // LIMPIEZA DE FORMATO: Quitar espacios, guiones y paréntesis para el comando ADB
    const isInternational = target.startsWith('+');
    target = (isInternational ? '+' : '') + target.replace(/[^0-9]/g, '');

    console.log(`📱 Número final procesado: ${target} `);

    showCommModal.value = false;

    if (commMode.value === 'sms') {
        if (!commBody.value) return;
        await sendMobileSMS(target, commBody.value);
    } else {
        await initiateMobileCall(target);
    }
};

const linkedMobileDevice = computed(() => {
    // Prioritize device marked as primary
    const primary = userSettings.value.devices?.find(d => d.type === 'Celular' && d.isPrimary);
    if (primary) return primary;

    // Legacy: Prioritize name
    const namedPrincipal = userSettings.value.devices?.find(d => d.type === 'Celular' && d.name.toLowerCase().includes('principal'));
    if (namedPrincipal) return namedPrincipal;

    // Fallback to first found
    return userSettings.value.devices?.find(d => d.type === 'Celular');
});

const setPrimaryMobile = (scannedDev) => {
    // Find the device in userSettings
    if (!userSettings.value.devices) return;

    // Reset all cellulars
    userSettings.value.devices.forEach(d => {
        if (d.type === 'Celular') d.isPrimary = false;
    });

    // Set target as primary
    const target = userSettings.value.devices.find(d => d.ip === scannedDev.ip);
    if (target) {
        target.isPrimary = true;
        // Update scannedDev for immediate UI reflection
        scannedDevices.value.forEach(d => {
            if (d.assignedType === 'Celular') d.isPrimary = false;
            if (d.ip === scannedDev.ip) d.isPrimary = true;
        });
        saveSettings();
        finaState.value.process = t("proc_dev_updated", "DISPOSITIVO PRINCIPAL ACTUALIZADO");
        setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 2000);
    }
};

const isMessagingAvailable = computed(() => {
    return !!linkedMobileDevice.value || installedMessagingApps.value.length > 0;
});

const openMessagingCenter = async () => {
    try {
        console.log("🚀 Abriendo Centro de Mensajería...");
        let win = await WebviewWindow.getByLabel('messaging');
        if (win) {
            await win.show();
            await win.setFocus();
        } else {
            win = new WebviewWindow('messaging', {
                url: '/messaging.html',
                title: 'Fina Messaging Center',
                width: 1000,
                height: 750,
                center: true,
                decorations: true,
                focus: true
            });
        }
    } catch (e) {
        console.error("Error abriendo centro de mensajería:", e);
        addChatMessage("❌ Error al abrir centro de mensajería");
    }
};

const handleMessagingClick = () => {
    // Abrimos el modal SIEMPRE.
    openCommModal('sms');

    // Detección proactiva al abrir el modal
    detectMessagingApps();

    // Si no hay celular vinculado pero hay apps detectadas, solo avisamos
    if (!linkedMobileDevice.value) {
        const hint = `Hola ${userSettings.value.apis.USER_NAME || 'Usuario'}. No veo un celular vinculado por cable, pero he detectado ${installedMessagingApps.value.length} servicios de mensajería disponibles.`;
        invoke("execute_shell_command", {
            command: `${pythonExecutable.value} ${projectRoot.value}/utils.py speak "${hint}"`
        }).catch(() => { });
    }
};

const handleCallClick = () => {
    openCommModal('call');
    if (!linkedMobileDevice.value) {
        mobileHelpContext.value = 'missing';
        showMobileHelpModal.value = true;

        const hint = "No puedo iniciar llamadas sin un dispositivo vinculado. Por favor, revisa la guía en pantalla.";
        invoke("execute_shell_command", {
            command: `python3 ${projectRoot.value}/utils.py speak "${hint}"`
        }).catch(() => { });
    }
};

const acBtnLabel = computed(() => {
    return acState.value.power ? 'APAGAR EQUIPO' : 'ENCENDER AIRE';
});

const updateClock = () => {
    const now = new Date();
    const lang = userSettings.value.apis?.FINA_LANGUAGE || 'es';
    const locale = lang === 'en' ? 'en-US' : lang === 'fr' ? 'fr-FR' : lang === 'pt' ? 'pt-BR' : lang === 'de' ? 'de-DE' : 'es-AR';
    currentTime.value = now.toLocaleTimeString(locale, {
        hour: '2-digit', minute: '2-digit', hour12: false
    }).toLowerCase();

    // Format: Sábado, 14 Febrero 2026 (adaptado al idioma)
    const options = { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' };
    let dateStr = now.toLocaleDateString(locale, options);
    currentDate.value = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
};

// --- CLIMA LA PLATA (OPENWEATHER - ESTRICTO) ---
const updateWeather = async () => {
    try {
        // Obtener credenciales de Ajustes (o usar defaults temporales si está vacío para evitar error al inicio)
        const apiKey = userSettings.value.apis?.WEATHER_API_KEY || "";
        const cityId = userSettings.value.apis?.WEATHER_CITY_ID || "";

        if (!apiKey || !cityId) {
            // Si no hay configuración, no hacemos nada (o mostramos --)
            weatherTemp.value = "--";
            return;
        }

        const pyPath = pythonExecutable.value;
        const scriptPath = `${projectRoot.value}/iot/clima_api.py`;

        const lang = userSettings.value.apis?.FINA_LANGUAGE || 'es';
        // Ejecutar script con argumentos (incluye idioma para descripciones traducidas)
        const jsonStr = await invoke("execute_shell_command", { command: `timeout 10 ${pyPath} "${scriptPath}" "${apiKey}" "${cityId}" "${lang}"` });

        if (!jsonStr || jsonStr.trim() === "") throw new Error("Empty response");

        const data = JSON.parse(jsonStr);

        if (data.cod && parseInt(data.cod) !== 200) {
            throw new Error("API Error: " + data.message);
        }

        if (data && data.main && data.weather) {
            weatherTemp.value = Math.round(data.main.temp);
            weatherHumidity.value = data.main.humidity;
            weatherCode.value = data.weather[0].id;
            isDay.value = data.weather[0].icon.includes('d') ? 1 : 0;

            // New Extended Data
            if (data.wind) weatherWind.value = Math.round(data.wind.speed * 3.6); // m/s to km/h
            if (data.main.feels_like !== undefined) weatherFeelsLike.value = data.main.feels_like;
            if (data.weather[0].description) {
                // Capitalize
                const d = data.weather[0].description;
                weatherDesc.value = d.charAt(0).toUpperCase() + d.slice(1);
            }
            if (data.name) weatherCityName.value = data.name;

            // --- FETCH FORECAST (Background) ---
            const forecastScript = `${projectRoot.value}/iot/clima_forecast.py`;
            // No await needed, run parallel
            invoke("execute_shell_command", { command: `timeout 5 ${pyPath} "${forecastScript}" "${apiKey}" "${cityId}"` })
                .then(out => {
                    try {
                        const fData = JSON.parse(out);
                        if (Array.isArray(fData)) {
                            weatherForecast.value = fData;
                        }
                    } catch (e) { console.log("Forecast parse error", e); }
                })
                .catch(e => console.log("Forecast fetch error", e));
        }
    } catch (e) {
        // En caso de error, mostramos ERR para debug
        console.error("Clima error:", e);
        weatherTemp.value = "ERR";
    }
};

const weatherIcon = computed(() => {
    const code = weatherCode.value;
    if (!isDay.value && code === 800) return "fa-moon";
    if (code === 800) return "fa-sun";
    if (code >= 801 && code <= 804) return "fa-cloud-sun"; if (code >= 701 && code <= 781) return "fa-smog"; if (code >= 500
        && code <= 531) return "fa-cloud-showers-heavy"; if (code >= 600 && code <= 622) return "fa-snowflake"; if
        (code >= 200 && code <= 232) return "fa-bolt-lightning"; return "fa-cloud";
}); const
    testDoorbell = async () => {
        showDoorbell.value = true;
        finaState.value.process = t("proc_doorbell_conn", "Conectando con el timbre...");

        // Disparar secuencia de backend (Wake + Cast TV) - UNIVERSAL MARKET TEST
        const pyPath = pythonExecutable.value;
        const findMonitor = `find "${projectRoot.value}/.local_lab/Fina-Plugins-Market-Working/Doorbells" -name "monitor.py" | head -n 1`;
        
        try {
            const scriptPath = (await invoke("execute_shell_command", { command: findMonitor })).trim();
            if (scriptPath) {
                invoke("spawn_shell_command", { command: `${pyPath} "${scriptPath}" --trigger` }).catch(e =>
                    console.error("Error trigger:", e));
            }
        } catch (e) {}

        invoke('start_streamer').catch(() => { });
        setTimeout(() => {
            streamUrl.value = "http://127.0.0.1:8555/view?t=" + Date.now();
            streamKey.value = Date.now();
        }, 500); // Video disponible mucho antes ahora
    };

const hangUp = async () => {
    try {
        const pyPath = pythonExecutable.value;
        const findHangup = `find "${projectRoot.value}/.local_lab/Fina-Plugins-Market-Working/Doorbells" -name "hangup_doorbell.py" | head -n 1`;
        
        const scriptPath = (await invoke("execute_shell_command", { command: findHangup })).trim();
        if (scriptPath) {
            await invoke("spawn_shell_command", { command: `${pyPath} "${scriptPath}"` });
        }

        showDoorbell.value = false;
        finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");
    } catch (error) {
        console.error("Error colgando:", error);
        showDoorbell.value = false; // Cerrar igual
        finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");
    }
};

const systemStatus = computed(() => {
    // Lógica Semáforo solicitada por Usuario
    // Amarillo: Inicio / Cargando (Hasta "SISTEMA LISTO")
    // Verde: Sistema Listo / Idle / Listen (Operativo)
    // Rojo: Stopped / Error

    // Si contiene "INICIADO", "CARGANDO", "CLIENTE REINICIADO" -> AMARILLO "EN PROCESO"
    const p = (finaState.value.process || "").toUpperCase();

    if (finaState.value.status === 'stopped') {
        return { text: t("sys_stopped_short", "DETENIDO"), color: "text-red-500", dot: "bg-red-500 shadow-[0_0_8px_red]" };
    }

    if (p.includes("INICIADO") || p.includes("CARGANDO") || p.includes("ESPERANDO")) {
        return {
            text: t("sys_process_short", "EN PROCESO"), color: "text-amber-400", dot: "bg-amber-500 shadow-[0_0_8px_amber] animate-pulse"
        };
    }

    // Default Verde (Listening, Speaking, Idle, Sistema Listo)
    // Pero si está hablando, podemos poner "RESPONDIENDO" (Cyan) o mantener "EN EJECUCIÓN" (Verde)?
    // Usuario pidió "En Ejecución" con punto verde una vez que Fina da el OK.

    if (finaState.value.status === 'speaking') {
        return {
            text: t("sys_exec_short", "EN EJECUCIÓN"), color: "text-emerald-400", dot: "bg-emerald-500 shadow-[0_0_10px_lime] animate-pulse"
        };
    }

    return {
        text: t("sys_exec_short", "EN EJECUCIÓN"), color: "text-emerald-400", dot: "bg-emerald-500 shadow-[0_0_10px_lime]"
    };
});

const getGreeting = () => {
    const hour = new Date().getHours();
    const name = userSettings.value.apis.USER_NAME || "Usuario";
    if (hour >= 6 && hour < 12) return `${t("sys_morning", "Buenos Días")} ${name}`;
    if (hour >= 12 && hour < 20) return `${t("sys_afternoon", "Buenas Tardes")} ${name}`;
    return `${t("sys_evening", "Buenas Noches")} ${name}`; // 20:00 - 05:59
};

const notifyFina = (msg, duration = 4000) => {
    if (finaState.value.status === 'speaking' || finaState.value.status === 'listening') return;
    finaState.value.process = msg.toUpperCase();
    setTimeout(() => {
        if (finaState.value.process === msg.toUpperCase()) {
            finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");
        }
    }, duration);
};

// --- REFRESH SYSTEMS ---
const refreshAcStatus = async (silent = false) => {
    // REFRESH AIR CONDITIONER (UNIVERSAL MARKET TEST)
    const ac_ip = userSettings.value.apis.AC_IP || "";
    if (!ac_ip) return;

    const pyPath = pythonExecutable.value;
    const findClima = `find "${projectRoot.value}/.local_lab/Fina-Plugins-Market-Working/AirConditioning" -name "clima.py" | head -n 1`;

    try {
        const scriptPath = (await invoke("execute_shell_command", { command: findClima })).trim();
        if (!scriptPath) return;

        let command = `${pyPath} "${scriptPath}" --status --ip ${ac_ip}`;
        if (silent) command += " --silent";

        const output = await invoke("execute_shell_command", { command });
        console.log("Sincronizando Aire...", output);

        const tempMatch = output.match(/ a ([\d.]+)°C/i);
        const indoorMatch = output.match(/Int: ([\d.]+)°C/i);
        const outdoorMatch = output.match(/Ext: ([\d.]+|--)/i);
        const humidityMatch = output.match(/Humedad: ([\d.]+)/i);
        const modeMatch = output.match(/modo (\w+)/i);
        const powerMatch = output.match(/(está|esta) encendido/i);
        const wattsMatch = output.match(/Consumo:\s*(\d+)W/i);
        const kwhMatch = output.match(/Acumulado:\s*([\d.]+)kWh/i);
        const monthlyMatch = output.match(/monthly_kwh":\s*([\d.]+)/i); // Extraemos del JSON payload en el log si es necesario, o añadimos al msg

        if (tempMatch) acState.value.temp = Math.round(parseFloat(tempMatch[1]));
        if (indoorMatch) acState.value.indoor = Math.round(parseFloat(indoorMatch[1]));
        if (outdoorMatch) acState.value.outdoor = Math.round(parseFloat(outdoorMatch[1]));
        if (humidityMatch) acState.value.humidity = Math.round(parseFloat(humidityMatch[1]));
        if (modeMatch) acState.value.mode = modeMatch[1].toLowerCase();
        if (wattsMatch) acState.value.watts = parseInt(wattsMatch[1]);
        if (kwhMatch) acState.value.total_kwh = parseFloat(kwhMatch[1]);
        
        // Intentar parsear el JSON de la respuesta directamente si está presente para mayor exactitud
        try {
            const jsonMatch = output.match(/\{"power":.*\}/);
            if (jsonMatch) {
                const acData = JSON.parse(jsonMatch[0]);
                if (acData.monthly_kwh !== undefined) acState.value.monthly_kwh = acData.monthly_kwh;
                if (acData.total_kwh !== undefined) acState.value.total_kwh = acData.total_kwh;
            }
        } catch(e) {}

        acState.value.power = !!powerMatch;
    } catch (e) {
        console.error("Error refreshing AC status:", e);
    }
};

const refreshDoorbellStatus = async () => {
    const pyPath = pythonExecutable.value;
    const findScript = `find "${projectRoot.value}/.local_lab/Fina-Plugins-Market-Working/Doorbells" -name "doorbell_status.py" | head -n 1`;

    try {
        const scriptPath = (await invoke("execute_shell_command", { command: findScript })).trim();
        if (!scriptPath) return;

        const output = await invoke("execute_shell_command", { command: `${pyPath} "${scriptPath}"` });
        if (output && output.trim() !== "" && !isNaN(parseInt(output))) {
            doorbellBattery.value = output.trim();
            console.log("✅ Batería Timbre sincronizada:", doorbellBattery.value + "%");
        }
    } catch (e) {
        console.error("Error refreshing doorbell status:", e);
    }
};



const fetchSettings = async (maxRetries = 60, delayMs = 1000) => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch("http://127.0.0.1:18000/api/settings");
            if (!response.ok) throw new Error(`API HTTP ${response.status}`);
            const loaded = await response.json();
            console.log(`📂 Settings OK (intento ${attempt}):`, loaded);

            // MERGE INTELIGENTE (Evita que undefined rompa el UI)
            if (loaded.apis) {
                // Formato Nuevo { apis: {...}, tvs: [...] }
                userSettings.value.apis = { ...userSettings.value.apis, ...loaded.apis };
                if (loaded.tvs) userSettings.value.tvs = loaded.tvs;
                if (loaded.devices) userSettings.value.devices = loaded.devices;
                if (loaded.disabled_channels) userSettings.value.disabled_channels = loaded.disabled_channels;
                if (loaded.tv_apps) userSettings.value.tv_apps = loaded.tv_apps;
                if (loaded.linked_apps) userSettings.value.linked_apps = loaded.linked_apps;
            } else {
                // Formato Viejo/Plano { GITHUB_TOKEN: "..." }
                // Asumimos que todo lo plano va a apis
                userSettings.value.apis = { ...userSettings.value.apis, ...loaded };
                if (loaded.tvs) userSettings.value.tvs = loaded.tvs;
                if (loaded.devices) userSettings.value.devices = loaded.devices;
                if (loaded.disabled_channels) userSettings.value.disabled_channels = loaded.disabled_channels;
                if (loaded.tv_apps) userSettings.value.tv_apps = loaded.tv_apps;
                if (loaded.linked_apps) userSettings.value.linked_apps = loaded.linked_apps;
            }

            console.log("✅ Settings Merged:", userSettings.value);
            updateWeather();
            return; // Éxito => salir del loop
        } catch (e) {
            if (attempt < maxRetries) {
                console.warn(`⏳ API no lista aún (intento ${attempt}/${maxRetries}). Reintentando en ${delayMs}ms...`);
                await new Promise(r => setTimeout(r, delayMs));
            } else {
                console.warn("⚠️ API no respondió tras todos los intentos. Usando defaults.");
            }
        }
    }
};

const fetchContacts = async () => {
    try {
        const response = await fetch("http://127.0.0.1:18000/api/contacts");
        if (response.ok) {
            contacts.value = await response.json();
            console.log("👥 Contactos cargados vía API:", Object.keys(contacts.value).length);
        }
    } catch (e) {
        console.error("Error loading contacts:", e);
    }
};

const fetchUserData = async () => {
    try {
        const response = await fetch("http://127.0.0.1:18000/api/userdata");
        if (response.ok) {
            userData.value = await response.json();
            console.log("📝 Datos de usuario cargados:", userData.value);
        }
    } catch (e) {
        console.error("Error loading user data:", e);
    }
};

const syncContactsFromMobile = async (force = false) => {
    const lastSync = localStorage.getItem('last_contact_sync');
    const now = Date.now();
    const oneDay = 24 * 60 * 60 * 1000;

    if (!force && lastSync && (now - parseInt(lastSync) < oneDay)) {
        console.log("⏭️ Sincronización de contactos saltada (ya sincronizado hoy)");
        return;
    }

    try {
        const pyPath = pythonExecutable.value;
        const script = `${projectRoot.value}/plugins/system/sync_contacts.py`;

        console.log("🔄 Sincronizando contactos desde el móvil...");
        await invoke("execute_shell_command", { command: `${pyPath} "${script}"` });

        localStorage.setItem('last_contact_sync', now.toString());
        await fetchContacts();
    } catch (e) {
        console.error("Error sincronizando contactos:", e);
    }
};

const importFromCore = async () => {
    finaState.value.process = t("proc_importing", "IMPORTANDO DESDE CORE...");
    try {
        const rootPath = ".";
        // En Fina-Ergen ya no hay carpeta 'test/fina-ergen', todo es local.
        console.log("Sincronización core saltada: Ya estamos en la carpeta raíz.");

        await fetchSettings();
        finaState.value.process = t("proc_import_done", "IMPORTACIÓN EXITOSA");
        setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 3000);
    } catch (e) {
        console.error("Error importing:", e);
        finaState.value.process = t("proc_err_import", "ERROR EN IMPORTACIÓN");
    }
};

const showPass = reactive({
    eleven: false,
    weather: false,
    github: false,
    email: false,
    news: false,
    openai: false,
    unsplash: false,
    runaway: false
});

const saveSettings = async () => {
    finaState.value.process = t("proc_saving", "GUARDANDO AJUSTES...");
    try {
        const jsonContent = JSON.stringify(userSettings.value);
        // Escapamos comillas simples para que no rompa el argumento de bash '...'
        const safeJson = jsonContent.replace(/'/g, "'\\''");

        const pyPath = pythonExecutable.value;
        const scriptPath = `${projectRoot.value}/iot/save_settings.py`;

        // Pasamos el JSON como argumento único entre comillas simples
        const cmd = `${pyPath} "${scriptPath}" '${safeJson}'`;

        const output = await invoke("execute_shell_command", { command: cmd });
        console.log("Save output:", output);

        finaState.value.process = t("proc_saved", "AJUSTES GUARDADOS");
        setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 3000);

        // Refrescar clima con nuevos datos inmediatamente
        updateWeather();

    } catch (e) {
        console.error("Save Error:", e);
        finaState.value.process = t("proc_err_save", "ERROR AL GUARDAR");
    }
};

const appWindow = getCurrentWindow();
const toggleSidebar = () => isSidebarCollapsed.value = !isSidebarCollapsed.value;

const sendTvCommand = async (script, args = "") => {
    finaState.value.process = t("proc_tv_cmd", "COMANDO TV...");

    // Lógica dinámica de IP
    if (!activeTvIp.value) {
        await detectTvIp(true); // Intenta detectar silenciosamente antes de mandar
    }

    let ip = activeTvIp.value;
    const activeTv = userSettings.value.tvs?.find(t => t.room === activeTvRoom.value) || userSettings.value.tvs?.[0];

    if (!ip) ip = activeTv?.ip;
    if (!ip) {
        finaState.value.process = t("proc_ip_undef", "IP NO DEFINIDA");
        return;
    }

    // NORMALIZACIÓN DEL MODELO (DINÁMICO DESDE SETTINGS)
    if (!activeTv?.type) {
        console.error("❌ Error: No se ha definido el tipo (modelo) para este dispositivo en settings.json");
        finaState.value.process = t("proc_err_no_model", "MODELO NO DEFINIDO");
        return;
    }
    const model = activeTv.type.toLowerCase().replace(/_/g, '');
    const mac = activeTv?.mac || "";
    const pyPath = pythonExecutable.value;

    // MOTOR DE BÚSQUEDA DINÁMICO DE MERCADO (Robusto)
    const userPluginsPath = `${configDir.value}/plugins`;
    const marketPath = `${projectRoot.value}/.local_lab/Fina-Plugins-Market-Working`;
    
    // Búsqueda más flexible que tolere subcarpetas o variaciones del nombre del modelo
    const findCommand = `find "${userPluginsPath}" "${marketPath}" -ipath "*${model}*${script}" 2>/dev/null | head -n 1`;
    
    try {
        console.log(`📺 Buscando comando TV (${model}): ${script}`);
        // Verificamos si existe el script y obtenemos su ruta absoluta
        const pathCheck = await invoke("execute_shell_command", { command: findCommand });
        
        if (!pathCheck || pathCheck.trim() === "") {
            console.error(`❌ Script no encontrado: ${script} para el modelo ${model}`);
            finaState.value.process = t("proc_err_not_found", "SCRIPT NO ENCONTRADO");
            return;
        }

        const scriptPath = pathCheck.trim();
        let finalCmd = `${pyPath} "${scriptPath}" --ip ${ip}`;
        
        // Manejo de MAC para scripts que la requieren
        const macScripts = ["tv_on.py", "tv_power.py", "tv_input.py", "deco_on.py", "deco_power.py"];
        if (mac && macScripts.includes(script)) {
            finalCmd += ` --mac ${mac}`;
        }
        if (args) finalCmd += ` ${args}`;

        console.log(`🚀 Ejecutando: ${finalCmd}`);
        await invoke("spawn_shell_command", { command: finalCmd });
        
        setTimeout(() => {
            if (finaState.value.process === "COMANDO TV...") finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");
        }, 2000);
    } catch (e) {
        console.error("TV Error:", e);
        finaState.value.process = t("proc_err_tv", "ERROR TV");
    }
};

const volInterval = ref(null);

const stopVol = () => {
    if (volInterval.value) {
        clearInterval(volInterval.value);
        volInterval.value = null;
    }
};

const startVolUp = () => {
    stopVol();
    tvVolUp();
    volInterval.value = setInterval(tvVolUp, 200);
};

const startVolDown = () => {
    stopVol();
    tvVolDown();
    volInterval.value = setInterval(tvVolDown, 200);
};

const tvVolUp = () => sendTvCommand("tv_volume_up.py");
const tvVolDown = () => sendTvCommand("tv_volume_down.py");
const tvMute = () => sendTvCommand("tv_mute.py");
const setTvVolume = (val) => sendTvCommand("tv_set_volume.py", `${val}`);

const tvChNext = () => sendTvCommand("tv_channel_up.py");
const tvChPrev = () => sendTvCommand("tv_channel_down.py");
const tvPower = () => sendTvCommand("tv_power.py");
const tvInput = () => sendTvCommand("tv_input.py");
const tvDeco = () => {
    // Si estamos en la habitación Deco, el comando debería ser diferente?
    // Pero si estamos en Dormitorio/Living, queremos cambiar a HDMI (Telecentro)
    // El usuario pidió: "para ir el boton HDMI abrias ese menu bajabas 2 lugares y hacias enter"
    // Esto ya está en set_input_deco.py actualizado.

    // Si la habitación activa es Deco, quizás queremos ir al Home del Android TV o algo así.
    // Pero asumiendo que el botón es para cambiar INPUT en una TV normal:
    sendTvCommand("set_input_deco.py");
};

const setDecoInput = () => {
    sendTvCommand("set_input_deco.py");
};

// FUNCIÓN DE ESTILO PARA ONDAS DE SONIDO (Optimizada GPU)
const getBarStyle = (n) => {
    return {
        height: '60px', // Altura base del contenedor radial
        left: '50%',
        top: '50%',
        marginTop: '-150px', // Radio del círculo
        transformOrigin: '50% 150px', // Centro de rotación
        transform: `rotate(${n * 2}deg)` // 360 / 180 barras = 2 grados por barra
    };
};

// FUNCIÓN DE DETECCIÓN DE TV INTELIGENTE
const detectTvIp = async (silent = false) => {
    if (!silent) finaState.value.process = t("proc_looking_tv", "BUSCANDO TV...");

    // 1. Intentar conectar preventivamente a las TVs conocidas (SOLO SI NO ESTAMOS EN MODO SILENCIOSO)
    // Para evitar saturar ADB al inicio si ya hay conexiones vivas
    if (!silent && userSettings.value.tvs && Array.isArray(userSettings.value.tvs)) {
        // Asegurar que ADB esté corriendo
        await invoke("spawn_shell_command", { command: `adb start-server` }).catch(() => { });

        for (const tv of userSettings.value.tvs) {
            if (tv.ip) {
                // Timeout MUY corto para no colgar UI
                await invoke("spawn_shell_command", { command: `timeout 2 adb connect ${tv.ip}` }).catch(() => { });
            }
        }
    }

    // 2. Intentar leer cache del sistema (generado por python scripts)
    try {
        const cacheRaw = await invoke("execute_shell_command", { command: "cat /tmp/fina_last_tv_ip" });
        const cachedIp = cacheRaw.trim();
        if (cachedIp && cachedIp.length > 7) {
            // Validar que la IP en cache pertenezca a una TV configurada
            const isKnownTv = userSettings.value.tvs?.some(t => t.ip === cachedIp);
            if (!isKnownTv) {
                console.log("IP en cache no es una TV válida. Ignorando.");
            } else {
                // Priorizar la IP asignada a la habitación actual si existe
                const tvForRoom = userSettings.value.tvs?.find(t => t.room === activeTvRoom.value);
                const ipToTest = (tvForRoom && tvForRoom.ip) ? tvForRoom.ip : cachedIp;

                try {
                    await invoke("execute_shell_command", { command: `ping -c 1 -W 0.5 ${ipToTest}` });
                    console.log(`✅ TV Detectada (${activeTvRoom.value}): ${ipToTest}`);
                    activeTvIp.value = ipToTest;
                    tvStatuses.value[ipToTest] = true;

                    const connectedTv = userSettings.value.tvs?.find(t => t.ip === ipToTest);
                    const displayName = connectedTv ? connectedTv.name.toUpperCase() : ipToTest;
                    if (!silent) finaState.value.process = `TV CONECTADA: ${displayName}`;
                    if (!silent) setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 2000);
                    return;
                } catch {
                    console.log("Cache o IP de habitación no responde.");
                }
            }
        }
    } catch { }

    // 2. Escaneo estricto solo a IPs configuradas como TV
    const candidates = [];
    if (userSettings.value.tvs && Array.isArray(userSettings.value.tvs)) {
        userSettings.value.tvs.forEach(tv => {
            // Only check enabled TVs
            if (tv.ip && tv.enabled !== false && !candidates.includes(tv.ip)) candidates.push(tv.ip);
        });
    }

    if (candidates.length === 0) {
        // No valid candidates, do nothing or clear
        return;
    }

    // Check paralelo
    const checks = candidates.map(async (ip) => {
        try {
            await invoke("execute_shell_command", { command: `ping -c 1 -W 0.5 ${ip}` });
            return ip;
        } catch { return null; }
    });

    const results = await Promise.all(checks);
    const alive = results.filter(ip => ip !== null);

    // Update global status map
    candidates.forEach(ip => {
        tvStatuses.value[ip] = alive.includes(ip);
    });

    // Priorizar ABSOLUTAMENTE la TV de la habitación seleccionada
    const currentRoomTv = userSettings.value.tvs?.find(t => t.room === activeTvRoom.value);

    if (currentRoomTv) {
        // Ensure we are targeting the correct IP
        activeTvIp.value = currentRoomTv.ip;

        if (tvStatuses.value[currentRoomTv.ip]) {
            const displayName = currentRoomTv.name || currentRoomTv.room || currentRoomTv.ip;
            if (!silent) finaState.value.process = `TV CONECTADA: ${displayName}`;
        } else {
            // Si no responde, NO cambiamos a otra IP. Se queda en esta (que no responde).
            // Esto hace que el indicador se ponga Rojo.
            if (!silent) finaState.value.process = `${currentRoomTv.name} OFFLINE`;
        }
    }
    // Removed all fallbacks to candidates[0] or alive[0].
    // If current room TV is offline, it stays offline.

    // Actualizar cache solo si es válido Y está vivo
    if (activeTvIp.value && tvStatuses.value[activeTvIp.value]) {
        invoke("execute_shell_command", {
            command: `echo ${activeTvIp.value} > /tmp/fina_last_tv_ip`
        }).catch(() => { });
    }

    if (!silent) setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 2000);
};

// FUNCIÓN MAESTRA DE SINCRONIZACIÓN DE DISPOSITIVOS (Optimizada)
let lastSync = 0;
const syncAllDevices = async (force = false, silent = false) => {
    const now = Date.now();
    if (!force && now - lastSync < 30000) return; // if (!silent)
    finaState.value.process = t("proc_checking_states", "CORROBORANDO ESTADOS"); lastSync = now;
    await Promise.all([
        refreshAcStatus(silent),
        refreshDoorbellStatus(),
        detectTvIp(silent)
    ]);
};

const setTab = (tab) => {
    activeTab.value = tab;
    showDoorbell.value = false;
    // Reset sub-vistas para siempre empezar desde el inicio
    activeCasaView.value = "main";
    activeTvAppsView.value = false;
    activeTvSearch.value = "";
    showCommModal.value = false;
    activeSettingsDomain.value = "inteligencia";
    // Al entrar en Casa, seleccionar primera habitación de TV disponible
    if (tab === 'clima' && userSettings.value.tvs?.length > 0) {
        activeTvRoom.value = userSettings.value.tvs[0].room || 'Living';
    }
    if (window.innerWidth < 768) isSidebarCollapsed.value = true;
};
const minimizeWindow = async () => {
    if (appWindow) await appWindow.minimize();
};
const toggleMaximize = async () => {
    if (!appWindow) return;
    const isMax = await appWindow.isMaximized();
    if (isMax) await appWindow.unmaximize();
    else await appWindow.maximize();
};
const closeWindow = async () => {
    finaState.value.process = t("proc_shutting_down", "APAGANDO SISTEMA...");
    try {
        // Limpiar ADB antes de cerrar
        await invoke("execute_shell_command", {
            command: "pkill -f adb || killall -9 adb 2>/dev/null; sleep 1; adb start-server && adb devices"
        }).catch(() => { });

        await invoke("exit_app");
    } catch (e) {
        console.error("Error exiting app:", e);
    }
    // Fallback in case backend exit is delayed
    if (appWindow) await appWindow.close();
};

onMounted(async () => {
    try {
        const i18nResp = await fetch("http://127.0.0.1:18000/api/i18n");
        if (i18nResp.ok) i18nData.value = await i18nResp.json();
    } catch (e) { console.error("i18n load error", e); }

    syncSystemInfo(); // Obtener rutas del backend inmediatamente
    updateClock();
    setInterval(updateClock, 1000);
    setInterval(getSystemStats, 5000);
    getSystemStats();
    await fetchSettings();
    await fetchContacts(); // Cargar la agenda local
    await fetchUserData(); // Cargar recordatorios y notas
    syncContactsFromMobile(); // Intentar sincronizar desde el móvil de forma asíncrona
    updateWeather();
    setInterval(updateWeather, 60000); // Actualizar cada 1 minuto para mayor reactividad

    // ACTUALIZACIÓN DE CORREOS (Cada 5 min)
    fetchRecentEmails();
    setInterval(fetchRecentEmails, 300000);

    // SECUENCIA DE ARRANQUE [BALANCEADA PARA MAXIMIZAR]
    try {
        finaState.value.process = t("proc_loading_sys", "CARGANDO SISTEMA");
        addChatMessage(t('ui_sys_online'));

        // --- VERIFICACIÓN DE PRIMERA CONFIGURACIÓN ---
        // Esperar 12s: permite que fetchSettings complete sus reintentos (hasta 10s)
        setTimeout(() => {
            const criticalKeys = ['MISTRAL_API_KEY', 'OPENAI_API_KEY', 'WEATHER_API_KEY'];
            const isUnconfigured = criticalKeys.every(k => !userSettings.value.apis[k]);
            if (isUnconfigured) {
                addChatMessage(t('ui_first_time'), 0);
            }
        }, 12000);

        await new Promise(r => setTimeout(r, 1000));

        // 1. Estados iniciales en paralelo
        Promise.all([
            refreshAcStatus().catch(() => { }),
            refreshDoorbellStatus().catch(() => { })
        ]);

        await new Promise(r => setTimeout(r, 800));

        // 2. ADB / Móvil
        const mobileDev = linkedMobileDevice.value;
        if (mobileDev && mobileDev.ip) {
            finaState.value.process = t("proc_linking_mobile", "VINCULANDO MÓVIL");
            invoke("execute_shell_command", { command: `timeout 2 adb connect ${mobileDev.ip}:5555` })
                .catch(() => { });
        }



        // 3. Saludo
        const greeting = getGreeting();
        finaState.value.status = "speaking";
        finaState.value.process = t("proc_sys_op", "SISTEMA OPERATIVO");
        addChatMessage(greeting);
        await new Promise(r => setTimeout(r, 1500));
        finaState.value.status = "idle";
        finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");

        // 4. Detección de Apps 5 segundos después de que el sistema esté listo [STRICT]
        setTimeout(() => {
            console.log("⏰ Iniciando detección de apps post-arranque...");
            detectMessagingApps();
        }, 5000);

    } catch (err) {
        console.error("Boot error:", err);
    }

    // Refresco periódico de Aire y Timbre (cada 30 min)
    setInterval(() => {
        refreshAcStatus(true);
        refreshDoorbellStatus();
    }, 1800000);

    // FIX: Polling API REST para recuperar comunicación visual (Texto y Anillos)
    // Esto es necesario porque el puente de eventos Tauri se rompió al mover la arquitectura
    // FIX V2: Polling más rápido (100ms) y simulación de intensidad forzada (Estilo Old
    // School)
    // FIX V2: Polling optimizado (1000ms) para ahorro de memoria
    setInterval(async () => {
        try {
            const response = await fetch("http://127.0.0.1:18000/api/state");
            if (!response.ok) throw new Error("API Error");
            const data = await response.json();

            // Normalizar estado
            const newStatus = (data.status || "idle").toLowerCase();

            // Lógica de Mensajes: Evitar que "SISTEMA LISTO" (idle automático) borre una
            // respuesta valiosa
            // Si el backend manda algo difente a lo que tenemos, lo procesamos
            if (newStatus !== finaState.value.status || data.process !==
                finaState.value.process) {

                // Si la nueva info es "SISTEMA LISTO", solo la aplicamos si ya pasó el tiempo de
                // lectura
                if (data.process === t("sys_ready_short", "SISTEMA LISTO")) {
                    if (!window.lockTextUntil || Date.now() > window.lockTextUntil) {
                        finaState.value.status = newStatus;
                    }
                }
                else {
                    // Si es un mensaje RELEVANTE (no sistema listo), lo mostramos y bloqueamos el borrado por 3s
                    finaState.value.status = newStatus;
                    finaState.value.process = data.process;

                    // Manejo de flag de contraseña
                    if (data.show_password_field !== undefined) {
                        finaState.value.showPasswordField = data.show_password_field;
                        if (!data.show_password_field) authPassword.value = ""; // Limpiar si se oculta
                    }
                    if (data.auth_error !== undefined) {
                        finaState.value.authError = data.auth_error;
                    }

                    if (newStatus === 'speaking' || (data.process && data.process.length > 3)) {
                        window.lockTextUntil = Date.now() + 3000;
                    }
                }
            }

            // Intensidad siempre se actualiza
            finaState.value.intensity = data.intensity || 0.0;

            // --- PROCESAR COMANDOS PENDIENTES (Puente Brain->UI) ---
            if (data.pending_command) {
                const cmd = data.pending_command;
                console.log("📥 Comando recibido vía Polling:", cmd.name);

                if (cmd.name === 'fina-send-message') {
                    sendMobileSMS(cmd.payload.number, cmd.payload.message, cmd.payload.app);
                } else if (cmd.name === 'doorbell-ring') {
                    showDoorbell.value = true;
                    finaState.value.process = t("proc_answering_door", "Atendiendo Timbre");
                    invoke('start_streamer').catch(() => { });
                    setTimeout(() => {
                        streamUrl.value = "http://127.0.0.1:8555/view?t=" + Date.now();
                        streamKey.value = Date.now();
                    }, 2000);
                } else if (cmd.name === 'doorbell-hangup') {
                    showDoorbell.value = false;
                    finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");
                }
            }

            // --- SYNC TIMER VISUAL (ROBUSTO CON ID) ---
            if (data.timer && data.timer.duration) {
                // Verificar ID único para evitar loops de reinicio
                // Si data.timer.id no existe (versión vieja), usamos duration como proxy débil
                const incId = data.timer.id || data.timer.duration;
                const isNew = incId !== timerState.lastId;

                // Solo iniciamos si es NUEVO. Si es el mismo, confiamos en el conteo local.
                if (isNew) {
                    console.log("⏰ Nuevo Timer detectado:", data.timer);
                    startVisualTimer(data.timer.duration, data.timer.label || "TEMPORIZADOR");
                    timerState.lastId = incId;
                }
                // Si el ID es el mismo, NO hacemos nada. Dejamos que el intervalo local (setInterval) maneje la cuenta.
                // Si el local llega a 0 y para, y el backend sigue mandando el estado, al ser el mismo ID, no re-entramos aquí.
            } else {
                // Si el backend limpió a null, paramos todo.
                if (timerState.active) {
                    stopVisualTimer();
                    timerState.lastId = null;
                }
            }

            // Reset contador de errores si todo salió bien
            window.pollErrors = 0;

        } catch (e) {
            // Diagnóstico visual de errores de conexión (DETALLADO PARA USUARIO)
            if (!window.pollErrors) window.pollErrors = 0;
            window.pollErrors++;

            // Mostrar error solo si persiste (tras 15 fallos = 15 seg de espera durante arranque)
            if (window.pollErrors > 15) {
                const errDetail = `${e.name}: ${e.message}`;
                console.error("API Error Poll:", e);
                finaState.value.process = t("proc_wait_api", "ESPERANDO API...");
                finaState.value.status = "offline";
            } else {
                // Durante los primeros segundos, simplemente notificamos el inicio
                if (finaState.value.process === t("sys_ready_short", "SISTEMA LISTO") || !finaState.value.process) {
                    finaState.value.process = t("proc_config_backend", "CONFIGURANDO BACKEND...");
                }
            }
        }
    }, 1000);

    // Watch ya no es tan crítico si simulamos arriba, pero sirve para triggers puntuales
    watch(() => finaState.value.status, (newS) => {
        // Mantener lógica extra si hace falta
    });
    setInterval(() => syncAllDevices(false, true), 60000 * 10); // Sync silencioso cada 10 min

    // EVENTOS DE RETORNO
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            syncAllDevices(false, true);
        }
    });

    setInterval(() => {
        heartbeatSeconds.value = new Date().getSeconds();
    }, 1000);

    await listen('brain-event', (event) => {
        try {
            let data = event.payload;
            if (typeof data === 'string') data = JSON.parse(data.trim());
            if (data.type === 'event' && data.name === 'doorbell-ring') {
                showDoorbell.value = true;
                finaState.value.process = t("proc_answering_door", "Atendiendo Timbre");
                invoke('start_streamer').catch(() => { });
                setTimeout(() => {
                    streamUrl.value = "http://127.0.0.1:8555/view?t=" + Date.now();
                    streamKey.value = Date.now();
                }, 2000);
            } else if (data.name === 'fina-state') {
                // SI RECIBIMOS DATOS DEL CEREBRO, LA API VIVE
                window.pollErrors = 0;

                // Limpiar mensaje de error si existe
                if (finaState.value.process && (finaState.value.process.startsWith("ERR") ||
                    finaState.value.process.startsWith("ERROR"))) {
                    finaState.value.process = "";
                }

                const p = data.payload;
                // Actualizar estado visual
                if (p.status) finaState.value.status = p.status;
                if (p.process) finaState.value.process = p.process;
                if (p.intensity !== undefined) finaState.value.intensity = p.intensity;

                // LÓGICA DE PERSISTENCIA DE MENSAJES
                // Si hay un mensaje importante mostrándose, no dejar que "SISTEMA LISTO" lo pise al instante
                if (window.lockTextUntil && Date.now() < window.lockTextUntil &&
                    (p.process === t("sys_ready_short", "SISTEMA LISTO") || p.process === "ESCUCHANDO...")) {
                    // Ignoramos actualización banal para dejar leer al usuario
                } else {
                    finaState.value.status = p.status || "idle";
                    if (p.process && p.process !== t("sys_ready_short", "SISTEMA LISTO")) {
                        finaState.value.process = p.process;
                    }
                    finaState.value.intensity = p.intensity || 0.0;

                    // --- TIMER SYNC ---
                    if (p.timer !== undefined) {
                        if (p.timer && p.timer.duration) {
                            startVisualTimer(p.timer.duration, p.timer.label);
                        } else {
                            stopVisualTimer();
                        }
                    }

                    if (finaState.value.process !== t("sys_ready_short", "SISTEMA LISTO") && finaState.value.process !== "ESCUCHANDO..." && finaState.value.process !== "Diga 'Fina' para empezar") {
                        window.lockTextUntil = Date.now() + 3000;
                    }
                }
                if (finaState.value.process.length > 5 && finaState.value.status === 'speaking') {
                    addChatMessage(finaState.value.process);
                }
            } else if (data.name === 'fina-send-message') {
                const p = data.payload;
                console.log("📨 Orden de envío recibida del cerebro:", p);
                sendMobileSMS(p.number, p.message, p.app);
            } else if (data.name === 'fina-speak') {
                const speechMsg = data.payload.text || data.payload || "Hablando...";
                finaState.value.status = "speaking";
                finaState.value.process = speechMsg.toUpperCase();
                addChatMessage(speechMsg);

                setTimeout(() => {
                    if (finaState.value.status === 'speaking') finaState.value.status = "idle";
                    if (finaState.value.process === speechMsg.toUpperCase()) {
                        finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");
                    }
                }, 8000);
            } else if (data.name === 'ac-status-update') {
                const p = data.payload;
                acState.value.power = p.power;
                acState.value.temp = p.temp;
                acState.value.mode = p.mode.toLowerCase();
                acState.value.indoor = p.indoor;
                acState.value.outdoor = p.outdoor;
                acState.value.watts = p.watts;
                acState.value.total_kwh = p.total_kwh;
                acState.value.monthly_kwh = p.monthly_kwh;
            } else if (data.type === 'event' && (data.name === 'doorbell-hangup' ||
                data.event === 'doorbell-hangup')) {
                showDoorbell.value = false;
                finaState.value.process = t("sys_ready_short", "SISTEMA LISTO");
            }
        } catch (e) {
            console.error("Error cerebro:", e);
        }
    });
});

const tvChannels = ref({});
const loadTvChannels = async () => {
    try {
        const pyPath = pythonExecutable.value;
        // Escolher arquivo baseado na sala
        const channelFile = activeTvRoom.value === 'Deco' ? 'channels_telecentro.json' : 'channels.json';
        const script = `import json, os;
def get_config_dir():
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config: return os.path.join(xdg_config, "Fina")
    try:
        from pathlib import Path
        return os.path.join(str(Path.home()), ".config", "Fina")
    except: return os.path.expanduser("~/.config/Fina")
path = os.path.join(get_config_dir(), "${channelFile}")
if not os.path.exists(path): path = os.path.join(".", "config", "${channelFile}")
print(json.dumps(json.load(open(path))))`;
        const output = await invoke("execute_shell_command", { command: `${pyPath} -c '${script}'` });
        tvChannels.value = JSON.parse(output);
        console.log(`📺 Canales cargados para ${activeTvRoom.value} desde ${channelFile}`);
    } catch (e) {
        console.error("Error loading channels:", e);
        // Fallback or empty
        tvChannels.value = {};
    }
};

const toggleChannel = (name) => {
    if (!userSettings.value.disabled_channels) userSettings.value.disabled_channels
        = [];
    const index = userSettings.value.disabled_channels.indexOf(name);
    if (index > -1) {
        userSettings.value.disabled_channels.splice(index, 1);
    } else {
        userSettings.value.disabled_channels.push(name);
    }
};

const isChannelEnabled = (name) => {
    if (!userSettings.value.disabled_channels) return true;
    return !userSettings.value.disabled_channels.includes(name);
};

watch(activeTvRoom, async (newRoom) => {
    finaState.value.process = `CAMBIANDO A ${newRoom.toUpperCase()}...`;
    // Forzar IP de la habitación según settings.json
    const targetTv = userSettings.value.tvs?.find(t => t.room === newRoom);
    if (targetTv && targetTv.ip) {
        activeTvIp.value = targetTv.ip;
        console.log(`🎯 Room change: Switching to fixed IP ${targetTv.ip} for ${newRoom}`);
    }
    await loadTvChannels();
});

const cancelTvScan = async () => {
    finaState.value.process = t("proc_cancelling", "CANCELANDO...");
    try {
        await invoke("execute_shell_command", { command: "touch /tmp/fina_cancel_scan" });
        isScanningTv.value = false;
        setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 1500);
    } catch (e) {
        console.error("Cancel error:", e);
    }
};

const scanChannels = async () => {
    const ip = activeTvIp.value;
    if (!ip) {
        finaState.value.process = t("proc_select_tv", "SELECCIONE UNA TV");
        return;
    }
    isScanningTv.value = true;
    finaState.value.process = t("proc_scanning_ch", "ESCANEANDO CANALES...");
    const activeTv = userSettings.value.tvs?.find(t => t.ip === ip);
    if (!activeTv?.type) {
        finaState.value.process = t("proc_err_no_model", "MODELO NO DEFINIDO");
        isScanningTv.value = false;
        return;
    }
    const model = activeTv.type.toLowerCase().replace(/_/g, '');

    const pyPath = pythonExecutable.value;
    const scriptName = "scan_ultra_fast.py";
    const findScript = `find "${projectRoot.value}/.local_lab/Fina-Plugins-Market-Working" -path "*/${model}/${scriptName}" | head -n 1`;

    try {
        const scriptPath = await invoke("execute_shell_command", { command: findScript });
        if (scriptPath && scriptPath.trim() !== "") {
            await invoke("spawn_shell_command", { command: `${pyPath} "${scriptPath.trim()}" --ip ${ip}` });
        }
        // En un scan ultra fast no podemos saber exacto cuando termina si usamos spawn_shell_command
        // pero podemos esperar unos segundos o usar execute_shell_command si el usuario acepta la "espera"
        // Para canales mejor execute para saber cuando termina exacto.
        // await invoke("execute_shell_command", { command: `${pyPath} "${scriptPath}" --ip ${ip}` });

        // Vamos a usar spawn para que la interfaz siga viva, pero bloqueamos botones con isScanningTv
        setTimeout(() => {
            if (isScanningTv.value) {
                isScanningTv.value = false;
                loadTvChannels();
            }
        }, 15000); // 15 segundos es lo que tarda el ultra-fast aprox
    } catch (e) {
        console.error("Scan error:", e);
        isScanningTv.value = false;
    }
};

const tuneChannel = async (val) => {
    console.log("Tuning to channel:", val);
    const channelNum = String(val).split(' ')[0];
    // SIEMPRE ir a TV/Aire primero
    finaState.value.process = t("proc_tv_input", "CAMBIANDO A AIRE...");
    const ip = activeTvIp.value;
    if (!ip) return;
    const activeTv = userSettings.value.tvs?.find(t => t.ip === ip);
    if (!activeTv?.type) return;
    
    const model = activeTv.type.toLowerCase().replace(/_/g, '');
    const pyPath = pythonExecutable.value;
    const userPluginsPath = `${configDir.value}/plugins`;
    const marketPath = `${projectRoot.value}/.local_lab/Fina-Plugins-Market-Working`;

    // MOTOR DE BÚSQUEDA DINÁMICO (Compatible con subcarpetas)
    const findInputCmd = `find "${userPluginsPath}" "${marketPath}" -ipath "*${model}*tv_input.py" 2>/dev/null | head -n 1`;
    const findChCmd = `find "${userPluginsPath}" "${marketPath}" -ipath "*${model}*set_channel.py" 2>/dev/null | head -n 1`;

    try {
        const inputScript = (await invoke("execute_shell_command", { command: findInputCmd })).trim();
        const chScript = (await invoke("execute_shell_command", { command: findChCmd })).trim();

        if (!inputScript || !chScript) {
            console.error(`❌ Scripts no encontrados para ${model}`);
            finaState.value.process = t("proc_err_not_found", "SCRIPT NO ENCONTRADO");
            return;
        }
        // Paso 1: cambiar a TV/Aire
        await invoke("execute_shell_command", { command: `${pyPath} "${inputScript}" --ip ${ip}` });
        // Paso 2 (con delay): enviar canal
        finaState.value.process = `CANAL ${channelNum}...`;
        setTimeout(async () => {
            await invoke("spawn_shell_command", { command: `${pyPath} "${chScript}" --ip ${ip} --channel ${channelNum}` });
            setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 2000);
        }, 1500);
    } catch (e) {
        console.error("Channel tune error:", e);
        finaState.value.process = t("proc_err_tv", "ERROR TV");
    }
};

const sendAcCommand = async (args, msg) => {
    finaState.value.process = msg.toUpperCase();
    const ac_ip = userSettings.value.apis.AC_IP || "";
    if (!ac_ip) return;

    const pyPath = pythonExecutable.value;
    const findClima = `find "${projectRoot.value}/.local_lab/Fina-Plugins-Market-Working/AirConditioning" -name "clima.py" | head -n 1`;

    try {
        const scriptPath = (await invoke("execute_shell_command", { command: findClima })).trim();
        if (!scriptPath) return;

        const command = `${pyPath} "${scriptPath}" ${args} --ip ${ac_ip}`;
        await invoke("spawn_shell_command", { command });
        setTimeout(() => refreshAcStatus(true), 2000);
    } catch (e) {
        console.error("AC Error:", e);
    }
};

const launchTvApp = async (pkg) => {
    const ip = activeTvIp.value;
    if (!ip) {
        finaState.value.process = t("proc_tv_not_sel", "TV NO SELECCIONADA");
        return;
    }
    finaState.value.process = `ABRIENDO APP...`;

    const activeTv = userSettings.value.tvs?.find(t => t.ip === ip);
    if (!activeTv?.type) return;

    const model = activeTv.type.toLowerCase().replace(/_/g, '');
    const pyPath = pythonExecutable.value;
    const script = "launch_app.py";
    const findCmd = `find "${projectRoot.value}/.local_lab/Fina-Plugins-Market-Working" -path "*/${model}/${script}" | head -n 1`;

    try {
        const scriptPath = (await invoke("execute_shell_command", { command: findCmd })).trim();
        if (scriptPath) {
            await invoke("spawn_shell_command", { command: `${pyPath} "${scriptPath}" --package ${pkg} --ip ${ip}` });
            finaState.value.process = t("proc_app_started", "APP INICIADA");
            setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 2000);
        }
    } catch (e) {
        console.error("App launch error:", e);
    }
};

const scanTvApps = async () => {
    const ip = activeTvIp.value;
    if (!ip) {
        finaState.value.process = t("proc_select_tv", "SELECCIONE UNA TV");
        return;
    }
    isScanningTv.value = true;
    finaState.value.process = t("proc_scanning_apps", "ESCANEANDO APPS...");

    const activeTv = userSettings.value.tvs?.find(t => t.ip === ip);
    if (!activeTv?.type) return;

    const model = activeTv.type.toLowerCase().replace(/_/g, '');
    const pyPath = pythonExecutable.value;
    const script = "list_tv_apps.py";
    const findCmd = `find "${projectRoot.value}/.local_lab/Fina-Plugins-Market-Working" -path "*/${model}/${script}" | head -n 1`;

    try {
        const scriptPath = (await invoke("execute_shell_command", { command: findCmd })).trim();
        if (scriptPath) {
            await invoke("execute_shell_command", { command: `${pyPath} "${scriptPath}" --ip ${ip}` });
            await fetchSettings();
            finaState.value.process = t("proc_apps_scanned", "APPS ESCANEADAS");
        }
        isScanningTv.value = false;
        setTimeout(() => finaState.value.process = t("sys_ready_short", "SISTEMA LISTO"), 2000);
    } catch (e) {
        console.error("Scan apps error:", e);
        finaState.value.process = t("proc_err_scan_apps", "ERROR ESCANEO APPS");
        isScanningTv.value = false;
    }
};

const toggleAcPower = () => sendAcCommand(`--power ${acState.value.power ? 'off' : 'on'}`, "Cambiando Energía...");
const changeAcTemp = (delta) => {
    const newTemp = acState.value.temp + delta;
    sendAcCommand(`--temp ${newTemp}`, `Temp a ${newTemp}°`);
};
const setAcMode = (mode) => sendAcCommand(`--mode ${mode}`, `Modo ${mode}`);
const toggleAcTurbo = () => sendAcCommand(`--turbo ${acState.value.turbo ? 'off' : 'on'}`, "Turbo toggle");
const toggleAcSwing = () => sendAcCommand(`--swing ${acState.value.swing ? 'off' : 'on'}`, "Swing toggle");

const enrollVoice = () => {
    finaState.value.process = t("proc_training_voice", "ENTRENANDO VOZ...");
    const interactive = `${projectRoot.value}/plugins/biometria/run_interactive.sh`;
    const py = pythonExecutable.value;
    const script = `${projectRoot.value}/plugins/biometria/train_voice.py`;
    invoke("spawn_shell_command", { command: `${interactive} "${py} ${script}"` }).catch(e => console.error(e));
};

const enrollFace = () => {
    finaState.value.process = t("proc_training_face", "ENTRENANDO CARA...");
    const interactive = `${projectRoot.value}/plugins/biometria/run_interactive.sh`;
    const py = pythonExecutable.value;
    const script = `${projectRoot.value}/plugins/biometria/train_face.py`;
    invoke("spawn_shell_command", { command: `${interactive} "${py} ${script}"` }).catch(e => console.error(e));
};

const enrollFinger = () => {
    finaState.value.process = t("proc_reg_fingerprint", "REGISTRANDO HUELLA...");
    const interactive = `${projectRoot.value}/plugins/biometria/run_interactive.sh`;
    const py = pythonExecutable.value;
    const script = `${projectRoot.value}/plugins/biometria/enroll_finger.py`;
    invoke("spawn_shell_command", { command: `${interactive} "${py} ${script}"` }).catch(e => console.error(e));
};

const registerMasterPassword = () => {
    const cmd = 'kgx -e "bash -c \'echo Ingrese nueva contraseña maestra mín 10 chars mayús nums signos; read -s pass; echo $pass > ~/.fina_master_pass; echo Contraseña guardada; sleep 3\'"';
    invoke("spawn_shell_command", { command: cmd }).catch(() => { });
    finaState.value.process = "REGISTRO DE CONTRASEÑA";
};

const selectFolder = async (settingKey) => {
    try {
        const result = await invoke("execute_shell_command", { command: "zenity --file-selection --directory --title='Seleccionar Carpeta'" });
        if (result && result.trim()) {
            userSettings.value.apis[settingKey] = result.trim();
        }
    } catch (e) {
        console.error("Error al seleccionar carpeta con zenity:", e);
    }
};
</script>

<template>
    <div class="flex h-screen w-screen overflow-hidden bg-[#010409] font-sans text-slate-100 selection:bg-cyan-500/20">
        <!-- SIDEBAR -->
        <aside
            class="relative z-20 flex flex-col border-r border-white/5 bg-slate-900/50 backdrop-blur-2xl transition-all duration-300 py-6 shrink-0"
            :class="isSidebarCollapsed ? 'w-20' : 'w-64'">
            <div class="flex items-center px-6 mb-12 cursor-pointer group" @click="toggleSidebar">
                <div
                    class="h-10 w-10 flex items-center justify-center rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-700 shadow-xl shadow-cyan-900/40 group-hover:scale-105 transition-transform overflow-hidden">
                    <img :src="iconAvatar" class="w-full h-full object-cover scale-150" />
                </div>
                <span v-if="!isSidebarCollapsed"
                    class="ml-4 font-black text-xl text-white tracking-tighter uppercase whitespace-nowrap animate-in fade-in slide-in-from-left-2 duration-300">Fina
                    Ergen</span>
            </div>

            <nav class="flex-1 px-3 space-y-2">
                <button @click="setTab('dashboard')"
                    class="group flex items-center h-14 rounded-2xl transition-all w-full px-4"
                    :class="activeTab === 'dashboard' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-lg shadow-cyan-500/5' : 'text-slate-500 hover:bg-white/5 hover:text-slate-300'">
                    <i class="fa-solid fa-gauge-high text-lg w-10"></i>
                    <span v-if="!isSidebarCollapsed"
                        class="text-sm font-black tracking-widest uppercase leading-none">{{ t('ui_dashboard', 'Panel') }}</span>
                </button>
                <button @click="setTab('clima')"
                    class="group flex items-center h-14 rounded-2xl transition-all w-full px-4"
                    :class="activeTab === 'clima' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-lg shadow-cyan-500/5' : 'text-slate-500 hover:bg-white/5 hover:text-slate-300'">
                    <i class="fa-solid fa-house-laptop text-lg w-10"></i>
                    <span v-if="!isSidebarCollapsed"
                        class="text-sm font-black tracking-widest uppercase leading-none">{{ t('ui_iot', 'Casa') }}</span>
                </button>
                <button @click="setTab('seguridad')"
                    class="group flex items-center h-14 rounded-2xl transition-all w-full px-4"
                    :class="activeTab === 'seguridad' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-lg shadow-cyan-500/5' : 'text-slate-500 hover:bg-white/5 hover:text-slate-300'">
                    <i class="fa-solid fa-shield-virus text-lg w-10"></i>
                    <span v-if="!isSidebarCollapsed"
                        class="text-sm font-black tracking-widest uppercase leading-none">{{ t('ui_biometrics', 'Seguridad') }}</span>
                </button>
                <button @click="setTab('agenda')"
                    class="group flex items-center h-14 rounded-2xl transition-all w-full px-4"
                    :class="activeTab === 'agenda' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-lg shadow-cyan-500/5' : 'text-slate-500 hover:bg-white/5 hover:text-slate-300'">
                    <i class="fa-solid fa-calendar-check text-lg w-10"></i>
                    <span v-if="!isSidebarCollapsed"
                        class="text-sm font-black tracking-widest uppercase leading-none">{{ t('ui_agenda', 'Agenda') }}</span>
                </button>
                <button @click="setTab('ajustes')"
                    class="group flex items-center h-14 rounded-2xl transition-all w-full px-4 text-slate-600 hover:bg-white/5 hover:text-slate-400">
                    <i class="fa-solid fa-sliders text-lg w-10"></i>
                    <span v-if="!isSidebarCollapsed"
                        class="text-sm font-black tracking-widest uppercase leading-none">{{ t('ui_settings', 'Ajustes') }}</span>
                </button>
            </nav>

            <div class="p-3 border-t border-white/5 mt-auto">
                <!-- BOTON ACERCA DE CON PUNTO VERDE [ESTRICTO] -->
                <div class="flex items-center h-14 rounded-2xl hover:bg-white/5 transition-all cursor-pointer group px-4 overflow-hidden"
                    @click="showCredits = true">
                    <div class="relative w-10 h-10 flex items-center justify-center shrink-0">
                        <img :src="iconAvatar" class="h-8 w-8 rounded-full border border-cyan-500/40 object-cover" />
                        <span
                            class="absolute bottom-1 right-1 w-2.5 h-2.5 bg-green-500 border-2 border-[#0a0f1e] rounded-full shadow-[0_0_5px_rgba(34,197,94,0.8)]"></span>
                    </div>
                    <div v-if="!isSidebarCollapsed" class="ml-2 flex flex-col">
                        <span class="text-[9px] font-black text-slate-300 uppercase tracking-widest leading-none">{{ t('ui_assistant', 'Assistant') }}</span>
                        <span
                            class="text-[8px] font-mono text-cyan-500/60 font-bold uppercase tracking-tighter leading-none">{{ version.replace(' Edition', '') }}</span>
                    </div>
                </div>
            </div>
        </aside>

        <!-- MAIN CONTENT -->
        <main
            class="relative z-10 flex flex-1 flex-col overflow-hidden bg-gradient-to-b from-slate-950/70 to-black h-screen">
            <!-- HEADER -->
            <header data-tauri-drag-region
                class="flex h-16 items-center justify-between px-10 py-2 shrink-0 border-b border-white/5">
                <div class="flex items-center gap-10">
                    <h2
                        class="text-[26px] font-bold text-cyan-400 tracking-tight font-sans tabular-nums drop-shadow-[0_0_10px_rgba(34,211,238,0.3)] uppercase">
                        {{ currentTime }}</h2>
                    <div v-if="activeTab !== 'dashboard'"
                        class="flex items-center gap-3 px-4 py-1.5 rounded-xl bg-slate-900/50 border border-white/5 shadow-inner">
                        <i class="fa-solid" :class="weatherIcon + ' text-orange-500 text-sm'"></i>
                        <span class="text-xs font-black text-slate-400 tracking-widest">{{ weatherDisplay }}</span>
                    </div>
                    <div
                        class="flex items-center gap-2 px-4 py-1.5 rounded-xl border border-cyan-500/20 bg-cyan-900/10">
                        <div class="w-1.5 h-1.5 rounded-full" :class="systemStatus.dot"></div>
                        <span class="text-[10px] font-black tracking-[0.25em] uppercase leading-none"
                            :class="systemStatus.color">{{ systemStatus.text }}</span>
                    </div>
                </div>

                <div class="flex items-center gap-2 no-drag">
                    <button @click="minimizeWindow"
                        class="h-9 w-9 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-400 transition-all"><i
                            class="fa-solid fa-minus text-xs"></i></button>
                    <button @click="toggleMaximize"
                        class="h-9 w-9 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-400 transition-all"><i
                            class="fa-regular fa-square text-xs"></i></button>
                    <button @click="closeWindow"
                        class="h-9 w-9 rounded-lg bg-white/5 hover:bg-red-500/80 hover:text-white flex items-center justify-center text-slate-400 transition-all"><i
                            class="fa-solid fa-xmark text-sm"></i></button>
                </div>
            </header>

            <!-- AREA FIJA CENTRAL (CEREBRO) -->
            <div class="absolute inset-0 z-0 flex flex-col items-center justify-center pointer-events-none pb-20 transition-all duration-500"
                :class="isSidebarCollapsed ? '' : 'pl-64'">
                <!-- WEATHER MODULE (DEEP DIVE) -->
                <div v-if="activeTab === 'dashboard'"
                    class="absolute top-24 z-50 pointer-events-auto animate-in fade-in slide-in-from-left-8 duration-700 transition-all"
                    :class="isSidebarCollapsed ? 'left-24' : 'left-[265px]'">
                    <WeatherModule :temperature="typeof weatherTemp === 'number' ? weatherTemp : 0"
                        :humidity="weatherHumidity" :windSpeed="weatherWind" :feelsLike="weatherFeelsLike"
                        :description="weatherDesc" :cityName="weatherCityName" :weatherCode="weatherCode" :isDay="isDay"
                        :currentDate="currentDate" :forecast="weatherForecast" :t="t" />
                </div>

                <!-- CHAT BUBBLES -->
                <div class="absolute top-20 right-10 flex flex-col gap-3 items-end max-w-xs pointer-events-none">
                    <transition-group name="list">
                        <div v-for="msg in chatHistory" :key="msg.id"
                            class="px-4 py-2 bg-slate-900/80 backdrop-blur-xl border border-cyan-500/30 rounded-2xl rounded-tr-none shadow-xl animate-in fade-in slide-in-from-right-4">
                            <p class="text-[11px] text-cyan-100 font-medium whitespace-pre-line">
                                {{ msg.text }}</p>
                            <span class="text-[8px] text-cyan-500/50 font-black mt-1 block uppercase">{{ msg.time }}</span>
                        </div>
                    </transition-group>
                </div>

                <!-- NUEVO AVATAR: Fina Avatar Component -->
                <div class="relative flex items-center justify-center scale-110">
                    <FinaAvatar :status="finaState.status" :intensity="finaState.intensity" />

                    <!-- TIMER OVERLAY GLOBAL -->
                    <div v-if="timerState.active"
                        class="fixed inset-0 z-50 flex items-center justify-center pointer-events-none pb-12">
                        <div
                            class="relative w-[360px] h-[360px] flex items-center justify-center animate-in fade-in zoom-in duration-700 pl-40">
                            <!-- Adjusted padding/margin if needed -->
                            <!-- Anillo SVG -->
                            <svg class="absolute inset-0 w-full h-full -rotate-90 drop-shadow-[0_0_30px_rgba(34,211,238,0.5)]"
                                viewBox="0 0 100 100">
                                <circle cx="50" cy="50" r="46" fill="none" class="stroke-cyan-900/40"
                                    stroke-width="1.5" />
                                <circle cx="50" cy="50" r="46" fill="none"
                                    class="stroke-cyan-400 transition-all duration-1000 ease-linear" stroke-width="2"
                                    stroke-dasharray="289"
                                    :stroke-dashoffset="289 - ((timerState.remaining / timerState.duration) * 289)"
                                    stroke-linecap="round" />
                            </svg>
                            <!-- Texto -->
                            <div class="absolute -bottom-16 flex flex-col items-center gap-2 translate-x-3">
                                <div
                                    class="text-5xl font-black font-mono tracking-tighter text-white drop-shadow-[0_0_15px_rgba(0,0,0,1)] tabular-nums font-['JetBrains_Mono']">
                                    {{ formatTimer }}</div>
                                <div
                                    class="text-[10px] font-bold text-cyan-300 uppercase tracking-[0.4em] bg-slate-950/90 px-4 py-1.5 rounded-full border border-cyan-500/30 shadow-xl backdrop-blur-md">
                                    {{ timerState.label || 'TIMER' }}</div>
                            </div>
                        </div>
                    </div>

                    <!-- PASSWORS INPUT OVERLAY -->
                    <div v-if="finaState.showPasswordField"
                        class="absolute z-50 flex flex-col items-center gap-4 animate-in fade-in zoom-in duration-300">
                        <div class="relative group">
                            <input type="password" v-model="authPassword" @keyup.enter="submitAuthPassword"
                                :placeholder="t('ui_password', 'CONTRASEÑA')" autofocus
                                class="w-64 px-6 py-4 bg-slate-950/90 backdrop-blur-2xl border-2 border-cyan-500/50 rounded-2xl text-center text-xl font-black tracking-widest text-cyan-400 focus:outline-none focus:border-cyan-400 transition-all shadow-[0_0_20px_rgba(34,211,238,0.2)] placeholder:text-cyan-900" />
                            <div
                                class="absolute inset-0 rounded-2xl border border-cyan-400/20 pointer-events-none group-hover:border-cyan-400/40 transition-colors">
                            </div>
                        </div>
                        <p v-if="finaState.authError"
                            class="text-xs font-black text-red-500 uppercase tracking-widest animate-pulse">{{ t('auth_fail', 'Contraseña Incorrecta') }}</p>
                        <p class="text-[10px] font-bold text-cyan-700 uppercase tracking-[0.3em]">{{ t('ui_validate', 'Presiona Enter para Validar') }}</p>
                    </div>
                </div>

                <!-- ESTADO DE PROCESO (TEXTO ABAJO) -->
                <!-- Nota: El usuario pidió quitar 'Fina is listening...' de la imagen, pero aquí mostramos el estado real del sistema -->
                <!-- Se mantiene la lógica de mostrar mensajes de proceso como 'SISTEMA LISTO' o respuestas -->
                <!-- ESTADO DE PROCESO (TEXTO ABAJO) -->
                <!-- Ajustado: Margen negativo para subirlo y z-index alto -->
                <div class="relative z-50 text-center h-8 -mt-16 pointer-events-none">
                    <p
                        class="text-[18px] font-black tracking-[0.15em] text-cyan-400 uppercase drop-shadow-[0_0_15px_rgba(34,211,238,0.5)] font-sans">
                        {{ finaState.process }}
                    </p>
                    <!-- Indicador de Pensamiento (Subrayado sutil) -->
                    <p v-if="thoughtStream.length > 0"
                        class="text-[10px] font-mono text-cyan-300/80 uppercase tracking-[0.4em] mt-2 animate-pulse drop-shadow-[0_0_8px_rgba(103,232,249,0.3)]">
                        >> {{ thoughtStream[0] }}
                    </p>
                </div>
            </div>

            <!-- CONTENIDO INTERACTIVO (ABAJO) -->
            <div
                class="flex-1 w-full flex flex-col items-center justify-end overflow-hidden pb-12 relative z-10 pointer-events-none">
                <div class="w-full max-w-[95%] px-12 flex flex-col items-center pointer-events-auto">
                    <transition name="fade" mode="out-in">
                        <div v-if="activeTab === 'dashboard'" class="w-full grid grid-cols-2 gap-10 max-w-4xl">
                            <div @click="setTab('clima'); activeCasaView = 'aire'"
                                class="bg-slate-900/50 backdrop-blur-md p-6 rounded-[35px] border border-white/5 hover:border-orange-500/30 transition-all cursor-pointer group flex items-center justify-between gap-4 shadow-xl">
                                <i
                                    class="fa-solid fa-fan text-orange-400 text-xl w-12 h-12 flex items-center justify-center bg-orange-500/10 rounded-2xl shadow-lg"></i>
                                <div class="flex-1 flex flex-col px-4">
                                    <span
                                        class="text-xl font-black text-white tracking-tighter uppercase leading-none">{{ t('ui_ac', 'Aire Acond') }}</span>
                                    <span class="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">{{ t('ui_main_room', 'SALA PRINCIPAL') }}</span>
                                </div>
                                <div class="flex flex-col items-end gap-1">
                                    <span class="text-3xl font-black text-white leading-none">{{ acState.temp }}°</span>
                                    <div class="grid grid-cols-[45px_35px] gap-x-1 mt-2 items-center leading-none">
                                        <span class="text-right text-[15px] font-black text-cyan-500 uppercase">{{ t('ui_ext', 'EXT') }}:</span>
                                        <span class="text-left text-[15px] font-black text-cyan-400 ml-1 uppercase">{{ acState.outdoor }}°</span>

                                        <span
                                            class="text-right text-[15px] font-black text-orange-500 uppercase mt-1">{{ t('ui_int', 'INT') }}:</span>
                                        <span
                                            class="text-left text-[15px] font-black text-orange-400 ml-1 uppercase mt-1">{{ acState.indoor }}°</span>

                                        <span
                                            class="text-right text-[11.5px] font-bold text-green-500 uppercase mt-1">{{ t('ui_hum', 'HUM') }}:</span>
                                        <span
                                            class="text-left text-[11.5px] font-bold text-green-400 ml-1 uppercase mt-1">{{ weatherHumidity }}%</span>

                                        <span v-if="acState.watts !== undefined"
                                            class="text-right text-[12.5px] font-black text-yellow-500 uppercase mt-1">{{ t('ui_pwr', 'PWR') }}:</span>
                                        <span v-if="acState.watts !== undefined"
                                            class="text-left text-[12.5px] font-black text-yellow-400 ml-1 uppercase mt-1 text-[8px] ml-0.5">{{ acState.watts }}<span>W</span></span>

                                        <span v-if="acState.total_kwh !== undefined && acState.total_kwh !== null"
                                            class="text-right text-[12.5px] font-black text-purple-500 uppercase mt-1">{{ t('ui_tot', 'TOT') }}:</span>
                                        <span v-if="acState.total_kwh !== undefined && acState.total_kwh !== null"
                                            class="text-left text-[12.5px] font-black text-purple-400 ml-1 uppercase mt-1 text-[8px] ml-0.5">{{ acState.total_kwh }}<span>kWh</span></span>

                                        <span v-if="acState.monthly_kwh !== undefined"
                                            class="text-right text-[12.5px] font-black text-pink-500 uppercase mt-1">{{ t('ui_mes', 'MES') }}:</span>
                                        <span v-if="acState.monthly_kwh !== undefined"
                                            class="text-left text-[12.5px] font-black text-pink-400 ml-1 uppercase mt-1 text-[8px] ml-0.5">{{ acState.monthly_kwh }}<span>kWh</span></span>
                                    </div>
                                </div>
                            </div>

                            <div @click="testDoorbell"
                                class="bg-slate-900/50 backdrop-blur-md p-6 rounded-[35px] border border-white/5 hover:border-cyan-500/30 transition-all cursor-pointer group flex items-center justify-between gap-4 shadow-xl">
                                <i
                                    class="fa-solid fa-door-open text-cyan-400 text-xl w-12 h-12 flex items-center justify-center bg-cyan-500/10 rounded-2xl shadow-lg"></i>
                                <div class="flex-1 flex flex-col px-4">
                                    <span
                                        class="text-xl font-black text-white tracking-tighter uppercase leading-none">{{ t('ui_doorbell', 'Timbre Cam') }}</span>
                                    <span class="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1">{{ t('ui_outdoor_gate', 'PUERTA EXTERIOR') }}</span>
                                </div>
                                <div
                                    class="bg-slate-800/80 px-4 py-2 rounded-xl border border-white/5 shrink-0 flex items-center gap-2">
                                    <i class="fa-solid fa-battery-three-quarters"
                                        :class="parseInt(doorbellBattery) > 20 ? 'text-green-500' : 'text-red-500'"></i>
                                    <span class="text-[10px] font-black text-slate-300 uppercase leading-none">{{ doorbellBattery }}% {{ t('ui_battery', 'BATERÍA') }}</span>
                                </div>
                            </div>
                        </div>
                        <div v-else-if="activeTab === 'clima'" class="w-full flex flex-col items-center">
                            <div v-if="activeCasaView === 'main'"
                                class="grid grid-cols-4 gap-6 w-full max-w-4xl mx-auto">
                                <div @click="activeCasaView = 'aire'; syncAllDevices(true)"
                                    class="p-6 bg-slate-900/50 backdrop-blur-md border border-white/5 rounded-[30px] hover:border-orange-500/40 transition-all cursor-pointer flex flex-col items-center gap-3">
                                    <i class="fa-solid fa-fan text-2xl text-orange-400"></i>
                                    <span class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-200">{{ t('ui_ac_short', 'Aire') }}</span>
                                </div>
                                <div @click="activeCasaView = 'tv'; activeTvAppsView = false; activeTvSearch = ''; loadTvChannels()"
                                    class="p-6 bg-slate-900/50 backdrop-blur-md border border-white/5 rounded-[30px] hover:border-green-500/40 transition-all cursor-pointer flex flex-col items-center gap-3">
                                    <i class="fa-solid fa-tv text-2xl text-green-400"></i>
                                    <span class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-200">{{ t('ui_tv', 'TV') }}</span>
                                </div>
                            </div>

                            <!-- TV CONTROL PANEL -->
                            <div v-else-if="activeCasaView === 'tv'"
                                class="w-full max-w-4xl p-6 bg-slate-900/80 backdrop-blur-2xl rounded-[40px] border border-green-500/30">
                                <div class="flex items-center justify-between mb-6">
                                    <button
                                        @click="activeCasaView = 'main'; activeTvAppsView = false; activeTvSearch = ''"
                                        class="px-4 py-2 bg-white/5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-green-500 hover:text-black transition-all">←
                                        {{ t('ui_back', 'Volver') }}</button>
                                    <div class="flex items-center gap-3">
                                        <h3
                                            class="text-xl font-black text-white italic tracking-tighter uppercase flex items-center gap-3">
                                            TV: {{ activeTvRoom }}
                                            <!-- Connection Status Dot -->
                                            <span
                                                class="w-2.5 h-2.5 rounded-full shadow-[0_0_8px_rgba(0,0,0,0.5)] border border-black/50"
                                                :title="isTvConnected ? t('ui_connected', 'Conectado') : t('ui_disconnected', 'Desconectado')"
                                                :class="isTvConnected ? 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.6)]'"></span>
                                        </h3>
                                    </div>

                                    <div class="flex gap-2">
                                        <button v-for="room in roomList" :key="room"
                                            @click="!isScanningTv && (activeTvRoom = room, activeTvAppsView = false)"
                                            :disabled="isScanningTv"
                                            class="w-8 h-8 rounded-lg flex items-center justify-center text-[8px] font-black uppercase transition-all"
                                            :class="[
                                                activeTvRoom === room ? 'bg-green-500 text-black' : 'bg-white/5 text-slate-500 hover:text-white',
                                                isScanningTv ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'
                                            ]">
                                            {{ room.substring(0, 2) }}
                                        </button>
                                    </div>

                                    <div class="flex gap-2">
                                        <template v-if="!isScanningTv">
                                            <button v-if="!activeTvAppsView" @click="scanChannels"
                                                class="px-4 py-2 bg-green-500/10 border border-green-500/30 rounded-xl text-[10px] font-black text-green-400 uppercase tracking-widest hover:bg-green-500 hover:text-black transition-all">
                                                {{ t('ui_scan', 'Escanear') }}
                                            </button>
                                            <button @click="activeTvAppsView = !activeTvAppsView"
                                                class="px-4 py-2 bg-purple-500/10 border border-purple-500/30 rounded-xl text-[10px] font-black text-purple-400 uppercase tracking-widest hover:bg-purple-500 hover:text-white transition-all">
                                                {{ activeTvAppsView ? t('ui_channels', 'CANALES') : t('ui_apps', 'APPS') }}
                                            </button>
                                        </template>
                                        <button v-else @click="cancelTvScan"
                                            class="px-6 py-2 bg-red-500/20 border border-red-500/50 rounded-xl text-[10px] font-black text-red-500 uppercase tracking-[.2em] animate-pulse hover:bg-red-500 hover:text-white transition-all">
                                            <i class="fa-solid fa-stop mr-2"></i> {{ t('ui_cancel', 'Cancelar') }}
                                        </button>
                                    </div>
                                </div>

                                <!-- CHANNEL GRID -->
                                <div v-if="!activeTvAppsView" class="h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                                    <div v-if="isTvConnected">
                                        <div class="grid grid-cols-2 gap-4">
                                            <div v-for="(num, name) in tvChannels" :key="name" @click="tuneChannel(num)"
                                                class="p-4 bg-white/5 rounded-2xl border border-white/5 hover:border-green-500/40 hover:bg-green-500/5 transition-all cursor-pointer flex items-center justify-between group">
                                                <div class="flex flex-col">
                                                    <span
                                                        class="text-sm font-black text-white uppercase group-hover:text-green-400 transition-colors">{{ name }}</span>
                                                    <span
                                                        class="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-0.5">{{ t('ui_channel', 'CANAL') }}
                                                        {{ num }}</span>
                                                </div>
                                                <div
                                                    class="h-8 w-8 rounded-lg bg-white/5 flex items-center justify-center">
                                                    <i
                                                        class="fa-solid fa-play text-[10px] text-green-500/50 group-hover:text-green-500"></i>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div v-else
                                        class="flex flex-col items-center justify-center h-full text-slate-500 gap-4">
                                        <i class="fa-solid fa-tv-slash text-4xl opacity-50"></i>
                                        <span class="text-xs font-black uppercase tracking-widest">TV
                                            Desconectada</span>
                                    </div>
                                </div>

                                <!-- APPS GRID (MOCKUP STYLE) -->
                                <div v-else class="flex-1 flex flex-col gap-8 overflow-hidden">
                                    <div v-if="isTvConnected" class="flex-1 flex flex-col gap-8">
                                        <!-- MOCKUP HEADER -->
                                        <div class="flex items-start justify-between">
                                            <div class="flex flex-col">
                                                <div
                                                    class="px-8 py-3 bg-white/5 backdrop-blur-2xl rounded-3xl border border-white/10 shadow-2xl inline-block">
                                                    <h4
                                                        class="text-3xl font-black text-white tracking-tighter opacity-90 italic">
                                                        Fina Phoenix</h4>
                                                </div>
                                                <span
                                                    class="text-[10px] font-black text-slate-500 mt-3 ml-2 uppercase tracking-[0.3em] italic">TV
                                                    {{ activeTvRoom }}</span>

                                                <div class="flex gap-4 mt-6">
                                                    <button v-if="!isScanningTv" @click="activeTvAppsView = false"
                                                        class="px-6 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-white text-[9px] font-black uppercase tracking-widest transition-all w-fit flex items-center gap-2">
                                                        <i class="fa-solid fa-chevron-left"></i>
                                                        Canales
                                                    </button>
                                                    <button v-if="!isScanningTv" @click="scanTvApps"
                                                        class="px-6 py-2 bg-purple-500/10 hover:bg-purple-600 border border-purple-500/30 rounded-full text-white text-[9px] font-black uppercase tracking-widest transition-all w-fit flex items-center gap-2">
                                                        <i class="fa-solid fa-qrcode"></i>
                                                        Escanear Apps
                                                    </button>
                                                    <button v-if="isScanningTv" @click="cancelTvScan"
                                                        class="px-6 py-2 bg-red-500/20 hover:bg-red-500 border border-red-500/30 rounded-full text-white text-[9px] font-black uppercase tracking-widest transition-all w-fit flex items-center gap-2 animate-pulse">
                                                        <i class="fa-solid fa-stop"></i>
                                                        Cancelar Escaneo
                                                    </button>
                                                </div>
                                            </div>

                                            <div class="flex flex-col items-end pt-2">
                                                <div class="relative">
                                                    <div
                                                        class="w-5 h-5 rounded-full bg-emerald-500 shadow-[0_0_25px_rgba(16,185,129,0.8)] animate-pulse">
                                                    </div>
                                                    <div
                                                        class="absolute inset-0 rounded-full border-2 border-emerald-500/50 animate-ping">
                                                    </div>
                                                </div>
                                                <span
                                                    class="text-[9px] font-black text-emerald-500 uppercase tracking-[0.2em] mt-3 mr-1">{{ t('ui_online', 'Online') }}</span>
                                            </div>
                                        </div>

                                        <!-- SEARCH BAR -->
                                        <div class="relative group max-w-2xl mx-auto w-full">
                                            <div
                                                class="absolute left-6 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-purple-400 transition-colors pointer-events-none">
                                                <i class="fa-solid fa-magnifying-glass"></i>
                                            </div>
                                            <input v-model="activeTvSearch" type="text" placeholder="Search"
                                                class="w-full bg-white/5 border border-white/10 rounded-[25px] py-5 pl-16 pr-8 text-xs font-bold uppercase tracking-widest outline-none focus:border-purple-500/50 focus:bg-white/10 transition-all backdrop-blur-xl shadow-inner placeholder:text-slate-600">
                                        </div>

                                        <!-- APP CARDS SCROLLABLE -->
                                        <div
                                            class="flex-1 flex items-center gap-8 overflow-x-auto overflow-y-hidden pb-10 px-4 custom-scrollbar snap-x">
                                            <div v-for="(pkg, name) in filteredTvApps" :key="name"
                                                @click="launchTvApp(pkg)"
                                                class="min-w-[200px] aspect-square bg-white/5 backdrop-blur-[30px] rounded-[45px] border border-white/10 hover:border-white/30 hover:bg-white/10 transition-all cursor-pointer group flex flex-col items-center justify-center gap-5 relative overflow-hidden snap-center shadow-2xl">
                                                <!-- Dynamic Glow Background -->
                                                <div class="absolute inset-0 opacity-0 group-hover:opacity-25 transition-opacity duration-500"
                                                    :class="appMetadata[name.toLowerCase()]?.glow || 'shadow-white/20'">
                                                </div>

                                                <div
                                                    class="relative z-10 w-24 h-24 flex items-center justify-center transition-transform group-hover:scale-110 duration-500">
                                                    <i class="text-6xl drop-shadow-[0_0_15px_rgba(0,0,0,0.5)]"
                                                        :class="[appMetadata[name.toLowerCase()]?.icon || 'fa-solid fa-rocket', appMetadata[name.toLowerCase()]?.color || 'text-slate-400']"></i>
                                                </div>

                                                <span
                                                    class="relative z-10 text-[11px] font-black text-white/70 uppercase tracking-[0.2em] group-hover:text-white transition-colors">{{ name }}</span>
                                            </div>

                                            <!-- EMPTY STATE -->
                                            <div v-if="Object.keys(filteredTvApps).length === 0"
                                                class="w-full flex flex-col items-center justify-center text-slate-600 py-20">
                                                <i class="fa-solid fa-ghost text-4xl mb-4 opacity-20"></i>
                                                <span class="text-[10px] font-black uppercase tracking-[0.3em]">{{ t('ui_no_apps', 'No hay apps disponibles') }}</span>

                                            </div>
                                        </div>

                                        <!-- BOTTOM VOICE BUTTON -->
                                        <div class="flex justify-center -mt-4 pb-4">
                                            <button
                                                class="px-10 py-5 bg-white/5 backdrop-blur-3xl border border-white/10 rounded-[30px] hover:bg-white/10 transition-all flex items-center gap-6 group shadow-2xl hover:scale-105 active:scale-95">
                                                <div
                                                    class="w-12 h-12 rounded-2xl bg-slate-900/80 flex items-center justify-center border border-white/10 group-hover:bg-purple-500 group-hover:text-black transition-all">
                                                    <i
                                                        class="fa-solid fa-microphone text-slate-400 transition-colors"></i>
                                                </div>
                                                <span
                                                    class="text-[11px] font-black text-slate-300 uppercase tracking-[0.3em] group-hover:text-white transition-colors">Map
                                                    Voice Commands</span>
                                            </button>
                                        </div>
                                    </div>

                                    <!-- DISCONNECTED STATE -->
                                    <div v-else
                                        class="flex-1 flex flex-col items-center justify-center text-slate-500 gap-6">
                                        <div
                                            class="w-24 h-24 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                                            <i class="fa-solid fa-tv-slash text-5xl opacity-30"></i>
                                        </div>
                                        <span
                                            class="text-[11px] font-black uppercase tracking-[0.4em] text-red-500/50">{{ t('ui_tv_disconnected', 'TV Desconectada') }}</span>

                                    </div>
                                </div>

                                <div class="mt-6 flex flex-col gap-3">
                                    <div class="grid grid-cols-6 gap-3">
                                        <button @click="tvPower"
                                            class="h-12 rounded-xl bg-red-500/20 border border-red-500/30 text-red-500 font-black text-[10px] uppercase">{{ t('ui_power', 'Power') }}</button>
                                        <button @click="tvInput"
                                            class="h-12 rounded-xl bg-cyan-500/20 border border-cyan-500/30 text-cyan-400 font-black text-[10px] uppercase">{{ t('ui_input', 'TV/Aire') }}</button>
                                        <button @click="tvDeco"
                                            class="h-12 rounded-xl bg-blue-500/20 border border-blue-500/30 text-blue-400 font-black text-[10px] uppercase">{{ t('ui_hdmi', 'HDMI') }}</button>
                                        <button @mousedown="startVolDown" @mouseup="stopVol" @mouseleave="stopVol"
                                            class="h-12 rounded-xl bg-white/5 border border-white/5 text-white font-black text-[10px] uppercase">{{ t('ui_vol_down', 'Vol -') }}</button>
                                        <button @mousedown="startVolUp" @mouseup="stopVol" @mouseleave="stopVol"
                                            class="h-12 rounded-xl bg-white/5 border border-white/5 text-white font-black text-[10px] uppercase">{{ t('ui_vol_up', 'Vol +') }}</button>
                                        <button @click="tvMute"
                                            class="h-12 rounded-xl bg-white/5 border border-white/5 text-slate-400 font-black text-[10px] uppercase hover:text-white">{{ t('ui_mute', 'Mute') }}</button>
                                    </div>
                                    <div class="grid grid-cols-4 gap-3">
                                        <button @click="setTvVolume(10)"
                                            class="h-8 rounded-lg bg-white/5 border border-white/5 text-slate-500 hover:text-white font-black text-[9px] uppercase">Vol
                                            10</button>
                                        <button @click="setTvVolume(20)"
                                            class="h-8 rounded-lg bg-white/5 border border-white/5 text-slate-500 hover:text-white font-black text-[9px] uppercase">Vol
                                            20</button>
                                        <button @click="setTvVolume(30)"
                                            class="h-8 rounded-lg bg-white/5 border border-white/5 text-slate-500 hover:text-white font-black text-[9px] uppercase">Vol
                                            30</button>
                                        <button @click="setTvVolume(50)"
                                            class="h-8 rounded-lg bg-white/5 border border-white/5 text-slate-500 hover:text-white font-black text-[9px] uppercase">Vol
                                            50</button>
                                    </div>
                                </div>
                            </div>

                            <!-- AIRE ACONDICIONADO -->
                            <div v-if="activeCasaView === 'aire'"
                                class="w-full max-w-[1100px] animate-in fade-in slide-in-from-bottom-2 duration-300">
                                <div
                                    class="bg-slate-950/90 p-8 rounded-[40px] border border-orange-500/30 shadow-[0_0_50px_rgba(249,115,22,0.15)] relative flex flex-row items-center justify-between gap-10">
                                    <button @click="activeCasaView = 'main'"
                                        class="absolute -top-4 left-10 text-[10px] font-black text-white px-6 py-2 bg-slate-900 border-2 border-orange-500/40 rounded-full hover:bg-orange-500 hover:text-black transition-all uppercase tracking-widest z-50">
                                        <i class="fa-solid fa-chevron-left mr-2"></i>
                                        {{ t('ui_back_home', 'Volver a Casa') }}
                                    </button>

                                    <div
                                        class="flex flex-col items-center justify-center shrink-0 px-10 border-r border-white/5">
                                        <div
                                            class="text-[90px] font-black text-white tracking-tighter leading-none flex items-start">
                                            {{ acState.temp }}<span class="text-orange-500 text-4xl ml-1">°</span>
                                        </div>
                                        <div
                                            class="mt-4 px-4 py-1.5 bg-orange-500/10 border border-orange-500/30 rounded-full font-black text-orange-400 text-[10px] tracking-widest uppercase shadow-inner">
                                            {{ t('ui_main_room', 'SALA PRINCIPAL') }}</div>
                                    </div>

                                    <div class="flex-1 grid grid-cols-6 gap-3">
                                        <button @click="changeAcTemp(1)"
                                            class="h-12 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 flex items-center justify-center gap-2 font-black text-[9px] uppercase"><i
                                                class="fa-solid fa-plus text-[10px]"></i>
                                            TEMP</button>
                                        <button @click="changeAcTemp(-1)"
                                            class="h-12 rounded-xl bg-white/5 border border-white/5 hover:bg-white/10 flex items-center justify-center gap-2 font-black text-[9px] uppercase"><i
                                                class="fa-solid fa-minus text-[10px]"></i>
                                            TEMP</button>
                                        <button @click="toggleAcTurbo"
                                            class="h-12 rounded-xl border text-[9px] font-black uppercase transition-all"
                                            :class="acState.turbo ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400' : 'bg-white/5 border-white/5 text-slate-600'">{{ t('ui_turbo', 'TURBO') }}</button>
                                        <button @click="toggleAcSwing"
                                            class="h-12 rounded-xl border text-[9px] font-black uppercase transition-all"
                                            :class="acState.swing ? 'bg-purple-500/20 border-purple-500 text-purple-400' : 'bg-white/5 border-white/5 text-slate-600'">{{ t('ui_swing', 'SWING') }}</button>
                                        <button @click="acState.eco = !acState.eco"
                                            class="h-12 rounded-xl border text-[9px] font-black uppercase transition-all"
                                            :class="acState.eco ? 'bg-green-500/20 border-green-500 text-green-400' : 'bg-white/5 border-white/5 text-slate-600'">{{ t('ui_eco', 'ECO') }}</button>
                                        <button @click="acState.sleep = !acState.sleep"
                                            class="h-12 rounded-xl border text-[9px] font-black uppercase transition-all"
                                            :class="acState.sleep ? 'bg-indigo-500/20 border-indigo-500 text-indigo-400' : 'bg-white/5 border-white/5 text-slate-600'">{{ t('ui_sleep', 'SLEEP') }}</button>

                                        <button @click="setAcMode('cool')"
                                            class="h-10 rounded-lg border text-[8px] font-black uppercase transition-all"
                                            :class="acState.mode === 'cool' ? 'bg-blue-600/30 border-blue-500 text-white' : 'bg-white/5 border-white/5 text-slate-700'">{{ t('ui_cool', 'COOL') }}</button>
                                        <button @click="setAcMode('heat')"
                                            class="h-10 rounded-lg border text-[8px] font-black uppercase transition-all"
                                            :class="acState.mode === 'heat' ? 'bg-orange-600/30 border-orange-500 text-white' : 'bg-white/5 border-white/5 text-slate-700'">{{ t('ui_heat', 'HEAT') }}</button>
                                        <button @click="setAcMode('dry')"
                                            class="h-10 rounded-lg border text-[8px] font-black uppercase transition-all"
                                            :class="acState.mode === 'dry' ? 'bg-teal-600/30 border-teal-500 text-white' : 'bg-white/5 border-white/5 text-slate-700'">{{ t('ui_dry', 'DRY') }}</button>
                                        <button @click="setAcMode('fan')"
                                            class="h-10 rounded-lg border text-[8px] font-black uppercase transition-all"
                                            :class="acState.mode === 'fan' ? 'bg-slate-700 border-white/30 text-white' : 'bg-white/5 border-white/5 text-slate-700'">{{ t('ui_fan', 'FAN') }}</button>
                                        <button @click="toggleAcDisplay"
                                            class="h-10 rounded-lg border text-[8px] font-black uppercase transition-all"
                                            :class="acState.display ? 'bg-cyan-900/30 border-cyan-700 text-white' : 'bg-white/5 border-white/5 text-slate-700'">{{ t('ui_display', 'DISPLAY') }}</button>
                                        <button
                                            class="h-10 rounded-lg bg-white/5 border border-white/5 text-[8px] font-black text-slate-700 uppercase">{{ t('ui_timer', 'TIMER') }}</button>

                                        <button @click="toggleAcPower"
                                            class="col-span-6 h-14 rounded-2xl flex items-center justify-center gap-6 transition-all font-black text-xs uppercase tracking-[0.5em] shadow-xl border mt-2"
                                            :class="acState.power ? 'bg-red-600 text-white border-red-400' : 'bg-orange-600 text-white border-orange-400'">
                                            <i class="fa-solid fa-power-off text-sm"></i>
                                            {{ acBtnLabel }}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div v-else-if="activeTab === 'seguridad'"
                            class="w-full max-w-4xl grid grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <!-- ESTADO DEL SISTEMA -->
                            <div
                                class="bg-indigo-900/10 p-8 rounded-[35px] border border-indigo-500/20 shadow-[0_0_30px_rgba(79,70,229,0.1)] flex flex-col gap-6 relative overflow-hidden group">

                                <div
                                    class="absolute inset-0 bg-gradient-to-tr from-indigo-500/5 via-transparent to-transparent opacity-50">
                                </div>

                                <div class="flex items-center justify-between z-10 w-full">
                                    <div class="flex flex-col">
                                        <h3
                                            class="text-xl font-black text-white uppercase tracking-tighter flex items-center gap-3">
                                            {{ t('ui_sys_status', 'Estado Sistema') }}
                                            <span
                                                class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shadow-[0_0_8px_lime]"></span>
                                        </h3>
                                        <p class="text-[9px] font-black text-indigo-400 uppercase tracking-widest mt-1">
                                            {{ t('ui_uptime_label', 'Tiempo Activo:') }} {{ systemStats.uptime }}
                                        </p>
                                    </div>
                                    <i class="fa-solid fa-server text-3xl text-indigo-500/30"></i>
                                </div>

                                <div class="grid grid-cols-2 gap-4 z-10 mt-2">
                                    <!-- CPU Circle -->
                                    <div
                                        class="flex flex-col items-center justify-center p-4 bg-black/20 rounded-2xl border border-white/5">
                                        <div class="relative w-16 h-16 flex items-center justify-center">
                                            <svg class="w-full h-full transform -rotate-90">
                                                <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="4"
                                                    fill="transparent" class="text-slate-800" />
                                                <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="4"
                                                    fill="transparent"
                                                    class="text-cyan-500 transition-all duration-1000 ease-out"
                                                    :stroke-dasharray="2 * Math.PI * 28"
                                                    :stroke-dashoffset="2 * Math.PI * 28 * (1 - (systemStats.cpu?.percent || 0) / 100)" />
                                            </svg>
                                            <span class="absolute text-xs font-black text-white">{{ Math.round(systemStats.cpu?.percent || 0) }}%</span>
                                        </div>
                                        <span
                                            class="text-[9px] font-black text-slate-400 uppercase mt-2 tracking-widest">{{ t('ui_cpu_load', 'CARGA CPU') }}</span>
                                    </div>

                                    <!-- RAM Circle -->
                                    <div
                                        class="flex flex-col items-center justify-center p-4 bg-black/20 rounded-2xl border border-white/5">
                                        <div class="relative w-16 h-16 flex items-center justify-center">
                                            <svg class="w-full h-full transform -rotate-90">
                                                <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="4"
                                                    fill="transparent" class="text-slate-800" />
                                                <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="4"
                                                    fill="transparent"
                                                    class="text-purple-500 transition-all duration-1000 ease-out"
                                                    :stroke-dasharray="2 * Math.PI * 28"
                                                    :stroke-dashoffset="2 * Math.PI * 28 * (1 - systemStats.ram.percent / 100)" />
                                            </svg>
                                            <span class="absolute text-xs font-black text-white">{{ Math.round(systemStats.ram.percent) }}%</span>
                                        </div>
                                        <span
                                            class="text-[9px] font-black text-slate-400 uppercase mt-2 tracking-widest">{{ t('ui_ram_usage', 'USO RAM') }}</span>
                                    </div>
                                </div>

                                <div class="z-10 mt-auto pt-4 border-t border-white/5 w-full">
                                    <div class="flex justify-between items-center mb-1">
                                        <span class="text-[9px] font-bold text-slate-500 uppercase">{{ t('ui_storage', 'Almacenamiento (Root)') }}</span>
                                        <span class="text-[9px] font-bold text-white">{{ systemStats.disk.percent }}%</span>
                                    </div>
                                    <div class="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                        <div class="h-full bg-gradient-to-r from-cyan-600 to-blue-500 transition-all duration-1000"
                                            :style="{ width: systemStats.disk.percent + '%' }"></div>
                                    </div>
                                    <div class="flex justify-between items-center mt-1">
                                        <span class="text-[8px] font-mono text-slate-600 uppercase">{{ systemStats.disk.free }}{{ t('ui_free', 'GB Libres') }}</span>
                                    </div>
                                </div>
                            </div>

                            <div
                                class="bg-slate-900/50 p-8 rounded-[35px] border border-white/5 shadow-2xl flex flex-col items-center justify-between gap-6 overflow-hidden relative group">
                                <div
                                    class="absolute inset-0 bg-red-900/5 opacity-0 group-hover:opacity-100 transition-opacity">
                                </div>

                                <div class="relative z-10 flex flex-col items-center gap-4 text-center">
                                    <div
                                        class="h-20 w-20 rounded-full bg-red-500/10 border-2 border-red-500/30 flex items-center justify-center shadow-[0_0_20px_rgba(239,68,68,0.2)]">
                                        <i class="fa-solid fa-shield-halved text-3xl text-red-500"></i>
                                    </div>
                                    <div>
                                        <h3 class="text-xl font-black text-white uppercase tracking-tighter">{{ t('ui_firewall', 'Firewall') }}
                                        </h3>
                                        <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-1">
                                            {{ t('ui_real_time_protection', 'Protección en Tiempo Real') }}</p>
                                    </div>
                                    <div
                                        class="w-full flex items-center justify-between px-6 py-3 bg-white/5 rounded-2xl border border-white/5 mt-2">
                                        <span class="text-[9px] font-black text-slate-400 uppercase">{{ t('ui_status', 'Estado') }}</span>
                                        <span
                                            class="text-[9px] font-black text-emerald-500 uppercase flex items-center gap-2">
                                            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                            {{ t('ui_enabled', 'Activado') }}
                                        </span>
                                    </div>
                                </div>

                                <button @click="showSentinel = true"
                                    class="w-full py-4 bg-gradient-to-r from-red-900/80 to-red-800/80 border border-red-500/30 rounded-2xl flex items-center justify-center gap-3 group/btn hover:scale-105 transition-all shadow-lg shadow-red-900/40 relative z-10">
                                    <i class="fa-solid fa-radar text-red-400 text-lg group-hover/btn:animate-spin"></i>
                                    <div class="flex flex-col items-start leading-none">
                                        <span
                                            class="text-[9px] font-black text-red-300 uppercase tracking-[0.2em] mb-1">{{ t('ui_access', 'Acceder a') }}</span>
                                        <span class="text-sm font-black text-white uppercase tracking-wider">{{ t('ui_sentinel', 'CENTINELA') }}</span>
                                    </div>
                                </button>
                            </div>
                        </div>
                        <div v-else-if="activeTab === 'agenda'"
                            class="w-full flex-1 flex flex-col items-center p-8 animate-in fade-in zoom-in-95 duration-500 overflow-y-auto max-h-screen relative z-10 space-y-8">

                            <!-- TOP SECTION: HEADER & PANELS -->
                            <div class="w-full max-w-7xl flex flex-col items-center shrink-0">
                                <div class="w-full flex justify-between items-start mb-4">
                                    <div class="flex flex-col">
                                        <h3
                                            class="text-4xl font-black text-white italic tracking-tighter uppercase leading-none">
                                            Fina</h3>
                                        <span
                                            class="text-[10px] font-bold text-cyan-400 tracking-[0.4em] uppercase mt-2">{{ t('ui_personal_assistant', 'Personal Assistant') }}</span>
                                    </div>
                                    <div class="flex items-center gap-4">
                                        <i class="fa-solid fa-bell text-slate-500 relative cursor-pointer">
                                            <span
                                                class="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>
                                        </i>
                                        <div
                                            class="w-10 h-10 rounded-full bg-gradient-to-tr from-purple-600 to-pink-500 border border-white/20">
                                        </div>
                                    </div>
                                </div>

                                <div class="w-full grid grid-cols-1 lg:grid-cols-3 gap-8 items-center">
                                    <!-- LEFT: RECORDATORIOS -->
                                    <div
                                        class="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-[35px] p-6 shadow-2xl space-y-4">
                                        <h4 class="text-sm font-black text-white uppercase flex items-center gap-2">
                                            <i class="fa-solid fa-bell text-cyan-400"></i>
                                            {{ t('ui_reminders', 'Recordatorios') }}
                                        </h4>
                                        <div class="space-y-4">
                                            <div v-for="(reminder, index) in userData.reminders" :key="index"
                                                class="flex flex-col border-l-2 pl-4 py-1 hover:bg-white/5 rounded-r-lg transition-colors cursor-pointer"
                                                :class="{
                                                    'border-cyan-500/50': index % 3 === 0,
                                                    'border-purple-500/50': index % 3 === 1,
                                                    'border-pink-500/50': index % 3 === 2
                                                }">
                                                <span class="text-[11px] font-bold text-white">{{ reminder.task }}</span>
                                                <span
                                                    class="text-[9px] text-slate-500 uppercase font-black tracking-widest mt-0.5">{{ reminder.time }}</span>
                                            </div>
                                            <div v-if="!userData.reminders || userData.reminders.length === 0"
                                                class="text-[10px] text-slate-600 font-bold uppercase py-4">
                                                {{ t('ui_no_reminders', 'Sin recordatorios pendientes') }}
                                            </div>
                                        </div>
                                    </div>

                                    <!-- CENTER: SILUETA FINA -->
                                    <div class="flex justify-center relative">
                                        <div class="absolute inset-0 bg-cyan-500/20 blur-[100px] rounded-full"></div>
                                        <img src="/assets/fina_avatar.png"
                                            class="w-full max-w-[320px] relative z-10 drop-shadow-[0_0_50px_rgba(6,182,212,0.4)] animate-pulse brightness-110" />
                                    </div>

                                    <!-- RIGHT: CORREOS -->
                                    <div
                                        class="bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-[35px] p-6 shadow-2xl space-y-4">
                                        <div class="flex items-center justify-between">
                                            <h4 class="text-sm font-black text-white uppercase flex items-center gap-2">
                                                <i class="fa-solid fa-envelope text-red-500"></i>
                                                {{ t('ui_emails', 'Correos') }}
                                            </h4>
                                            <div @click="fetchRecentEmails"
                                                class="cursor-pointer transition-all duration-500"
                                                :class="{ 'rotate-180 opacity-50': isFetchingMails }">
                                                <i class="fa-solid fa-arrows-rotate text-[10px]"
                                                    :class="isFetchingMails ? 'text-cyan-500 animate-spin' : 'text-slate-600'"></i>
                                            </div>
                                        </div>
                                        <div class="space-y-4">
                                            <div v-for="mail in recentEmails.slice(0, 3)" :key="mail.subject"
                                                class="flex flex-col border-r-2 border-blue-500/50 pr-4 py-1 items-end text-right hover:bg-white/5 rounded-l-lg transition-colors cursor-pointer">
                                                <span class="text-[11px] font-bold text-white">{{ mail.subject }}</span>
                                                <span
                                                    class="text-[9px] text-slate-500 uppercase font-black tracking-widest mt-0.5">{{ mail.from }}</span>
                                            </div>
                                            <div v-if="mailError"
                                                class="flex flex-col border-r-2 border-red-500/50 pr-4 py-1 items-end text-right">
                                                <span class="text-[10px] font-bold text-red-400 leading-tight">{{ mailError }}</span>
                                                <span
                                                    class="text-[8px] text-slate-600 uppercase font-black tracking-widest mt-1">CONFIGURACIÓN
                                                    REQUERIDA</span>
                                            </div>
                                            <div v-else-if="recentEmails.length === 0"
                                                class="flex flex-col border-r-2 border-slate-500/50 pr-4 py-1 items-end text-right">
                                                <span class="text-[11px] font-bold text-slate-400">{{ isFetchingMails ? t('ui_fetching', 'Actualizando...') : t('ui_no_subjects', 'Sin asuntos') }}</span>
                                                <span
                                                    class="text-[9px] text-slate-600 uppercase font-black tracking-widest mt-0.5">FINA
                                                    AL DÍA</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- MIDDLE SECTION: MI DÍA (HORIZONTAL TIMELINE) -->
                            <div
                                class="w-full max-w-7xl bg-black/40 backdrop-blur-xl border border-white/10 rounded-[40px] p-10 flex flex-col relative overflow-hidden group shadow-2xl shrink-0">
                                <div class="flex items-center justify-between mb-12 z-10">
                                    <div class="flex flex-col gap-1">
                                        <h3
                                            class="text-2xl font-black text-white uppercase tracking-tighter flex items-center gap-3">
                                            {{ t('ui_my_day', 'Mi Día') }}
                                        </h3>
                                        <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">{{ currentDate }}</span>
                                    </div>
                                    <div class="flex items-center gap-4">
                                        <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">{{ t('ui_today_events', '3 Eventos Hoy') }}</span>

                                        <i class="fa-solid fa-calendar-day text-slate-500"></i>
                                    </div>
                                </div>

                                <div class="relative py-12 z-10">
                                    <!-- Background line -->
                                    <div class="absolute top-[80px] left-8 right-8 h-[4px] bg-white/5 rounded-full">
                                    </div>
                                    <!-- Progress line -->
                                    <div
                                        class="absolute top-[80px] left-8 w-[65%] h-[4px] bg-gradient-to-r from-cyan-500 via-purple-500 to-pink-500 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.5)]">
                                    </div>

                                    <div class="flex justify-between items-start relative px-8">
                                        <!-- Point 1 -->
                                        <div class="flex flex-col items-center gap-6 w-1/4 group/item cursor-pointer">
                                            <div
                                                class="w-14 h-14 rounded-2xl bg-slate-900 border border-cyan-500/50 flex items-center justify-center text-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.2)] group-hover/item:scale-110 transition-transform">
                                                <i class="fa-solid fa-laptop-code text-xl"></i>
                                            </div>
                                            <div
                                                class="w-5 h-5 rounded-full bg-cyan-500 border-4 border-slate-950 z-10 shadow-[0_0_15px_cyan]">
                                            </div>
                                            <div
                                                class="text-center group-hover/item:-translate-y-1 transition-transform">
                                                <span
                                                    class="text-[12px] font-black text-white uppercase tracking-widest">9:00
                                                    AM</span>
                                                <p
                                                    class="text-[10px] text-cyan-200 mt-2 font-bold uppercase tracking-tight">
                                                    {{ t('ui_dev_fina', 'Desarrollo Fina V3') }}
                                                </p>
                                                <span class="text-[9px] text-slate-500 font-bold uppercase">{{ t('ui_sprint_coding', 'Sprint Coding') }}</span>

                                            </div>
                                        </div>

                                        <!-- Point 2 -->
                                        <div class="flex flex-col items-center gap-6 w-1/4 group/item cursor-pointer">
                                            <div
                                                class="w-14 h-14 rounded-2xl bg-slate-900 border border-purple-500/50 flex items-center justify-center text-purple-400 shadow-[0_0_20px_rgba(168,85,247,0.2)] group-hover/item:scale-110 transition-transform">
                                                <i class="fa-solid fa-server text-xl"></i>
                                            </div>
                                            <div
                                                class="w-5 h-5 rounded-full bg-purple-500 border-4 border-slate-950 z-10 shadow-[0_0_15px_purple]">
                                            </div>
                                            <div
                                                class="text-center group-hover/item:-translate-y-1 transition-transform">
                                                <div class="flex items-center justify-center">
                                                    <span
                                                        class="text-[12px] font-black text-white uppercase tracking-widest">13:30
                                                        PM</span>
                                                    <i
                                                        class="fa-solid fa-bell text-[8px] text-orange-400 ml-2 animate-bounce"></i>
                                                </div>
                                                <p
                                                    class="text-[10px] text-purple-200 mt-2 font-bold uppercase tracking-tight">
                                                    {{ t('ui_server_maint', 'Mantenimiento Server') }}
                                                </p>
                                                <span class="text-[9px] text-slate-500 font-bold uppercase">{{ t('ui_update_logs', 'Update Logs') }}</span>

                                            </div>
                                        </div>

                                        <!-- Point 3 -->
                                        <div class="flex flex-col items-center gap-6 w-1/4 group/item cursor-pointer">
                                            <div
                                                class="w-14 h-14 rounded-2xl bg-slate-900 border border-pink-500/50 flex items-center justify-center text-pink-400 shadow-[0_0_20px_rgba(236,72,153,0.2)] group-hover/item:scale-110 transition-transform">
                                                <i class="fa-solid fa-rocket text-xl"></i>
                                            </div>
                                            <div
                                                class="w-5 h-5 rounded-full bg-pink-500/20 border-4 border-white/5 z-10">
                                            </div>
                                            <div
                                                class="text-center group-hover/item:-translate-y-1 transition-transform">
                                                <div class="flex items-center justify-center">
                                                    <span
                                                        class="text-[12px] font-black text-white uppercase tracking-widest">18:00
                                                        PM</span>
                                                    <i class="fa-solid fa-bell text-[8px] text-slate-600 ml-2"></i>
                                                </div>
                                                <p
                                                    class="text-[10px] text-pink-200 mt-2 font-bold uppercase tracking-tight">
                                                    {{ t('ui_prod_deploy', 'Deploy Producción') }}
                                                </p>
                                                <span class="text-[9px] text-slate-500 font-bold uppercase">{{ t('ui_release', 'Release') }}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <!-- BOTTOM SECTION: COMUNICACIÓN -->
                            <div
                                class="w-full max-w-7xl bg-slate-900/40 backdrop-blur-xl border border-white/10 rounded-[40px] p-8 shadow-2xl shrink-0">
                                <div class="flex items-center justify-between mb-6">
                                    <h4 class="text-sm font-black text-white uppercase tracking-[0.2em]">{{ t('ui_communication', 'Comunicación') }}
                                    </h4>
                                    <div class="flex items-center gap-2">
                                        <span class="text-[9px] font-black text-slate-500">{{ t('ui_sync', 'SÍNC.') }}</span>
                                        <i class="fa-solid fa-arrows-rotate text-[10px] text-emerald-400"></i>
                                    </div>
                                </div>
                                <div class="grid grid-cols-2 gap-8">
                                    <div @click="handleMessagingClick"
                                        class="p-6 bg-white/5 border border-white/5 rounded-3xl flex items-center justify-center gap-6 hover:bg-green-500/10 hover:border-green-500/30 transition-all cursor-pointer group/wa">
                                        <div
                                            class="w-14 h-14 rounded-full bg-green-500/20 flex items-center justify-center text-green-500 group-hover/wa:scale-110 transition-transform">
                                            <i class="fa-solid fa-comment-dots text-3xl"></i>
                                        </div>
                                        <div class="flex flex-col">
                                            <span class="text-sm font-black text-white uppercase">{{ t('ui_messaging', 'Mensajería') }}</span>
                                            <span
                                                class="text-[9px] font-bold text-slate-500 uppercase tracking-widest truncate max-w-[120px]">{{ linkedMobileDevice ? linkedMobileDevice.name : t('ui_link_app', 'Vincular App') }}</span>
                                        </div>
                                    </div>
                                    <div @click="handleCallClick"
                                        class="p-6 bg-white/5 border border-white/5 rounded-3xl flex items-center justify-center gap-6 hover:bg-blue-500/10 hover:border-blue-500/30 transition-all cursor-pointer group/phone">
                                        <div
                                            class="w-14 h-14 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-500 group-hover/phone:scale-110 transition-transform">
                                            <i class="fa-solid fa-phone-flip text-2xl"></i>
                                        </div>
                                        <div class="flex flex-col">
                                            <span class="text-sm font-black text-white uppercase">{{ t('ui_call', 'Llamada') }}</span>
                                            <span
                                                class="text-[9px] font-bold text-slate-500 uppercase tracking-widest truncate max-w-[120px]">{{ linkedMobileDevice ? linkedMobileDevice.name : t('ui_link', 'Vincular') }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                        </div>
                        <div v-else-if="activeTab === 'ajustes'"
                            class="w-full max-w-6xl h-[75vh] flex relative animate-in zoom-in-95 duration-500">

                            <!-- HUB DE DOMINIOS -->
                            <div v-if="!activeSettingsDomain"
                                class="w-full h-full flex flex-col items-center justify-center p-12 gap-12 bg-slate-950/90 rounded-[50px] border border-white/10 shadow-3xl z-50">
                                <h2 class="text-3xl font-black text-white uppercase tracking-tighter mb-4">
                                    Panel de
                                    Control
                                    Maestro</h2>

                                <div class="grid grid-cols-2 lg:grid-cols-4 gap-8 w-full max-w-5xl">
                                    <!-- DOMINIO INTELIGENCIA -->
                                    <button
                                        @click="activeSettingsDomain = 'inteligencia'; activeSettingsTab = 'general'"
                                        class="group relative h-64 bg-gradient-to-br from-indigo-900/40 to-slate-900/40 rounded-[35px] border border-white/10 hover:border-cyan-500/50 hover:shadow-[0_0_30px_rgba(6,182,212,0.15)] transition-all flex flex-col items-center justify-center gap-6 overflow-hidden">
                                        <div
                                            class="absolute inset-0 bg-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity">
                                        </div>
                                        <div
                                            class="w-20 h-20 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
                                            <i class="fa-solid fa-brain text-4xl text-indigo-400"></i>
                                        </div>
                                        <span
                                            class="text-xs font-black text-slate-200 uppercase tracking-widest z-10 text-indigo-400 text-lg">{{ t('ui_domain', 'Dominio') }}<br><span>{{ t('ui_dom_intel', 'Inteligencia') }}</span></span>
                                    </button>

                                    <!-- DOMINIO VISUAL (TV, Timbre, Iluminación) -->
                                    <button @click="activeSettingsDomain = 'visual'; activeSettingsTab = 'tv'"
                                        class="group relative h-64 bg-gradient-to-br from-purple-900/40 to-slate-900/40 rounded-[35px] border border-white/10 hover:border-purple-500/50 hover:shadow-[0_0_30px_rgba(168,85,247,0.15)] transition-all flex flex-col items-center justify-center gap-6 overflow-hidden">
                                        <div
                                            class="absolute inset-0 bg-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity">
                                        </div>
                                        <div
                                            class="w-20 h-20 rounded-2xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
                                            <i class="fa-solid fa-eye text-4xl text-purple-400"></i>
                                        </div>
                                        <span
                                            class="text-xs font-black text-slate-200 uppercase tracking-widest z-10 text-purple-400 text-lg">{{ t('ui_domain', 'Dominio') }}<br><span>{{ t('ui_dom_visual', 'Visual') }}</span></span>
                                    </button>

                                    <!-- DOMINIO HABITAT (Aire, Ventanas, Riego, etc) -->
                                    <button @click="activeSettingsDomain = 'habitat'; activeSettingsTab = 'aire'"
                                        class="group relative h-64 bg-gradient-to-br from-emerald-900/40 to-slate-900/40 rounded-[35px] border border-white/10 hover:border-emerald-500/50 hover:shadow-[0_0_30px_rgba(16,185,129,0.15)] transition-all flex flex-col items-center justify-center gap-6 overflow-hidden">
                                        <div
                                            class="absolute inset-0 bg-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity">
                                        </div>
                                        <div
                                            class="w-20 h-20 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
                                            <i class="fa-solid fa-leaf text-4xl text-emerald-400"></i>
                                        </div>
                                        <span
                                            class="text-xs font-black text-slate-200 uppercase tracking-widest z-10 text-emerald-400 text-lg">{{ t('ui_domain', 'Dominio') }}<br><span>{{ t('ui_dom_habitat', 'Habitat') }}</span></span>
                                    </button>

                                    <!-- DOMINIO SEGURIDAD (Biometría, Cámaras, Puertas) -->
                                    <button @click="activeSettingsDomain = 'seguridad'; activeSettingsTab = 'biometria'"
                                        class="group relative h-64 bg-gradient-to-br from-red-900/40 to-slate-900/40 rounded-[35px] border border-white/10 hover:border-red-500/50 hover:shadow-[0_0_30px_rgba(239,68,68,0.15)] transition-all flex flex-col items-center justify-center gap-6 overflow-hidden">
                                        <div
                                            class="absolute inset-0 bg-red-500/5 opacity-0 group-hover:opacity-100 transition-opacity">
                                        </div>
                                        <div
                                            class="w-20 h-20 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
                                            <i class="fa-solid fa-shield-halved text-4xl text-red-400"></i>
                                        </div>
                                        <span
                                            class="text-xs font-black text-slate-200 uppercase tracking-widest z-10 text-red-400 text-lg">{{ t('ui_domain', 'Dominio') }}<br><span>{{ t('ui_dom_security', 'Seguridad') }}</span></span>
                                    </button>
                                </div>
                            </div>

                            <!-- LAYOUT INTERNO DEL DOMINIO -->
                            <div v-else
                                class="w-full h-full bg-slate-950/90 rounded-[50px] border border-white/10 shadow-3xl flex overflow-hidden animate-in slide-in-from-right-8 duration-500">

                                <!-- Sidebar de Ajustes Dinámico -->
                                <div class="w-72 bg-white/5 border-r border-white/5 p-8 flex flex-col gap-2 relative">

                                    <button @click="activeSettingsDomain = null"
                                        class="absolute top-4 left-4 h-8 w-8 rounded-full bg-white/5 hover:bg-white/20 flex items-center justify-center text-slate-400 hover:text-white transition-all">
                                        <i class="fa-solid fa-arrow-left text-xs"></i>
                                    </button>

                                    <div class="mt-8 mb-10 px-4">
                                        <h2 class="text-xl font-black text-white uppercase tracking-tighter">
                                            {{ activeSettingsDomain }}</h2>
                                        <p class="text-[9px] font-black text-cyan-500 uppercase tracking-widest mt-1">
                                            {{ t('ui_config', 'Configuración') }} </p>
                                    </div>

                                    <nav class="flex flex-col gap-2">
                                        <!-- INTELIGENCIA -->
                                        <template v-if="activeSettingsDomain === 'inteligencia'">
                                            <button @click="activeSettingsTab = 'general'"
                                                :class="activeSettingsTab === 'general' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-brain w-5"></i>
                                                Núcleo Ergen
                                            </button>
                                            <button @click="activeSettingsTab = 'plugins'"
                                                :class="activeSettingsTab === 'plugins' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-microchip w-5"></i>
                                                Nódulos
                                            </button>
                                            <button @click="activeSettingsTab = 'herramientas'"
                                                :class="activeSettingsTab === 'herramientas' ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-key w-5"></i>
                                                Servicios & APIs
                                            </button>
                                        </template>

                                        <!-- VISUAL -->
                                        <template v-if="activeSettingsDomain === 'visual'">
                                            <button @click="activeSettingsTab = 'tv'"
                                                :class="activeSettingsTab === 'tv' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-tv w-5"></i>
                                                Televisión
                                            </button>
                                            <button @click="activeSettingsTab = 'timbre'"
                                                :class="activeSettingsTab === 'timbre' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-bell w-5"></i>
                                                Timbre
                                            </button>
                                            <button @click="activeSettingsTab = 'iluminacion'"
                                                :class="activeSettingsTab === 'iluminacion' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-lightbulb w-5"></i>
                                                Iluminación
                                            </button>
                                        </template>

                                        <!-- HABITAT -->
                                        <template v-if="activeSettingsDomain === 'habitat'">
                                            <button @click="activeSettingsTab = 'aire'"
                                                :class="activeSettingsTab === 'aire' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-wind w-5"></i>
                                                Aire Ac.
                                            </button>
                                            <button @click="activeSettingsTab = 'ventanas'"
                                                :class="activeSettingsTab === 'ventanas' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-table-cells w-5"></i>
                                                Ventanas
                                            </button>
                                            <button @click="activeSettingsTab = 'riego'"
                                                :class="activeSettingsTab === 'riego' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-droplet w-5"></i>
                                                Riego
                                            </button>
                                            <button @click="activeSettingsTab = 'limpieza'"
                                                :class="activeSettingsTab === 'limpieza' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-broom w-5"></i>
                                                Limpieza
                                            </button>
                                            <button @click="activeSettingsTab = 'heladera'"
                                                :class="activeSettingsTab === 'heladera' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-temperature-empty w-5"></i>
                                                Heladera
                                            </button>
                                        </template>

                                        <!-- SEGURIDAD -->
                                        <template v-if="activeSettingsDomain === 'seguridad'">
                                            <button @click="activeSettingsTab = 'biometria'"
                                                :class="activeSettingsTab === 'biometria' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-fingerprint w-5"></i>
                                                Biometría
                                            </button>
                                            <button @click="activeSettingsTab = 'camaras'"
                                                :class="activeSettingsTab === 'camaras' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-video w-5"></i>
                                                Cámaras
                                            </button>
                                            <button @click="activeSettingsTab = 'puertas'"
                                                :class="activeSettingsTab === 'puertas' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'text-slate-500 hover:text-slate-300 border-transparent'"
                                                class="flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all text-xs font-black uppercase tracking-widest text-left">
                                                <i class="fa-solid fa-door-closed w-5"></i>
                                                Puertas
                                            </button>
                                        </template>
                                    </nav>

                                    <!-- Botón de Manual (Persistente en Sidebar de Ajustes) -->
                                    <div class="mt-auto pt-6 border-t border-white/5 px-2 mb-4">
                                        <button @click="openConfigManual"
                                            class="w-full flex items-center gap-3 px-5 py-4 rounded-2xl bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 hover:text-indigo-300 border border-indigo-500/20 transition-all text-[8px] font-black uppercase tracking-[0.2em] text-left">
                                            <i class="fa-solid fa-book-open text-xs"></i>
                                            Documentación
                                        </button>
                                    </div>
                                </div>

                                <!-- Contenido de Ajustes -->
                                <div
                                    class="flex-1 p-12 overflow-y-auto custom-scrollbar bg-gradient-to-br from-transparent to-cyan-500/5 relative">

                                    <!-- TAB: NÚCLEO ERGEN (DASHBOARD) -->
                                    <div v-if="activeSettingsTab === 'general'"
                                        class="animate-in fade-in zoom-in-95 duration-700 h-full flex flex-col">

                                        <div class="flex items-center justify-between mb-8">
                                            <div class="flex flex-col">
                                                <h3
                                                    class="text-3xl font-black text-white uppercase tracking-tighter italic">
                                                    NÚCLEO ERGEN</h3>
                                                <p
                                                    class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.4em] mt-2">
                                                    Central Intelligence
                                                    Matrix</p>
                                            </div>
                                            <div class="flex items-center gap-4">
                                                <div
                                                    class="px-4 py-2 bg-indigo-500/10 border border-indigo-500/30 rounded-xl">
                                                    <span
                                                        class="text-[9px] font-black text-indigo-400 uppercase tracking-widest">Estado
                                                        Core: </span>
                                                    <span
                                                        class="text-[10px] font-black text-white uppercase tracking-widest">{{ t('ui_local_infra', 'Infraestructura Local') }}</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div class="flex-1 grid grid-cols-12 gap-8 min-h-0">
                                            <!-- LEFT: NEURAL VISUALIZATION -->
                                            <div
                                                class="col-span-12 lg:col-span-7 bg-white/5 rounded-[40px] border border-white/10 p-10 flex flex-col items-center justify-center relative overflow-hidden group">
                                                <div
                                                    class="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-indigo-500/5 via-transparent to-transparent">
                                                </div>

                                                <!-- Neural Grid Simulation -->
                                                <div
                                                    class="relative w-full aspect-square max-h-[400px] flex items-center justify-center">
                                                    <!-- Animated Background Orbs -->
                                                    <div
                                                        class="absolute w-64 h-64 bg-indigo-500/20 rounded-full blur-[100px] animate-pulse">
                                                    </div>

                                                    <!-- Central Brain Icon -->
                                                    <div
                                                        class="relative z-10 w-48 h-48 rounded-full border border-indigo-500/30 flex items-center justify-center bg-black/40 backdrop-blur-xl shadow-[0_0_50px_rgba(99,102,241,0.2)] group-hover:scale-105 transition-transform duration-700">
                                                        <i
                                                            class="fa-solid fa-brain text-8xl text-indigo-500 drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]"></i>

                                                        <!-- Orbital Rings -->
                                                        <div
                                                            class="absolute inset-x-[-20px] inset-y-[-20px] border border-indigo-500/10 rounded-full animate-[spin_10s_linear_infinite]">
                                                        </div>
                                                        <div
                                                            class="absolute inset-x-[-40px] inset-y-[-40px] border border-indigo-500/5 rounded-full animate-[spin_15s_linear_infinite_reverse] border-dashed">
                                                        </div>
                                                    </div>

                                                    <!-- Activity Nodes -->
                                                    <div class="absolute inset-0 z-0">
                                                        <div v-for="i in 5" :key="i"
                                                            class="absolute w-2 h-2 bg-indigo-400 rounded-full blur-[2px] animate-ping"
                                                            :style="{
                                                                top: Math.random() * 80 + 10 + '%',
                                                                left: Math.random() * 80 + 10 + '%',
                                                                animationDelay: (i * 0.5) + 's'
                                                            }"></div>
                                                    </div>
                                                </div>

                                                <div class="mt-8 text-center z-10">
                                                    <div class="flex items-center gap-6 justify-center">
                                                        <div class="flex flex-col items-center">
                                                            <span class="text-4xl font-black text-white leading-none">{{ neuralActivity }}%</span>
                                                            <span
                                                                class="text-[9px] font-black text-indigo-400 uppercase tracking-widest mt-2">{{ t('ui_neural_activity', 'Actividad Neural') }}</span>
                                                        </div>
                                                        <div class="w-px h-10 bg-white/10"></div>
                                                        <div class="flex flex-col items-center">
                                                            <span
                                                                class="text-4xl font-black text-white leading-none">V3.2</span>
                                                            <span
                                                                class="text-[9px] font-black text-indigo-400 uppercase tracking-widest mt-2">{{ t('ui_revision', 'Revisión') }}
                                                                Matrix</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <!-- RIGHT: THOUGHTS & CONTROLS -->
                                            <div class="col-span-12 lg:col-span-5 flex flex-col gap-6">
                                                <!-- THOUGHT STREAM -->
                                                <div
                                                    class="flex-1 bg-black/40 rounded-[40px] border border-white/5 flex flex-col overflow-hidden">
                                                    <div
                                                        class="p-6 border-b border-white/5 flex items-center justify-between bg-white/5">
                                                        <span
                                                            class="text-[10px] font-black text-slate-400 uppercase tracking-widest">{{ t('ui_thought_stream', 'Flujo de') }}
                                                            {{ t('ui_migrated_core', 'Migración Core') }}</span>
                                                        <div class="flex gap-1">
                                                            <div
                                                                class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse">
                                                            </div>
                                                            <div
                                                                class="w-1.5 h-1.5 rounded-full bg-indigo-500/50 animate-pulse delay-75">
                                                            </div>
                                                            <div
                                                                class="w-1.5 h-1.5 rounded-full bg-indigo-500/20 animate-pulse delay-150">
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div
                                                        class="flex-1 p-6 space-y-4 overflow-y-auto custom-scrollbar font-mono text-[10px] text-indigo-300">
                                                        <div v-for="(thought, i) in thoughtStream" :key="i"
                                                            class="flex gap-2 animate-in slide-in-from-left-2 transition-all">
                                                            <span class="text-indigo-500 opacity-50 italic">>></span>
                                                            <span>{{ thought }}</span>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- ACTIVE MODEL CARD -->
                                                <div
                                                    class="bg-gradient-to-br from-indigo-900/40 to-slate-900/60 p-8 rounded-[40px] border border-indigo-500/20 relative group overflow-hidden">
                                                    <div class="flex flex-col gap-4 relative z-10">
                                                        <span
                                                            class="text-[9px] font-black text-indigo-400 uppercase tracking-widest">{{ t('ui_active_base_model', 'Modelo Base Activo') }}</span>
                                                        <h4
                                                            class="text-2xl font-black text-white italic tracking-tighter">
                                                            {{ activeModel }}</h4>
                                                        <div class="flex items-center gap-2 mt-2">
                                                            <span
                                                                class="px-2 py-0.5 bg-indigo-600 text-[8px] font-black text-white rounded uppercase">{{ t('ui_ultra_low_latency', 'Ultra-Low Latency') }}</span>
                                                            <span
                                                                class="px-2 py-0.5 bg-white/10 text-[8px] font-black text-indigo-300 rounded uppercase">{{ t('ui_self_optimizing', 'Self-Optimizing') }}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- TAB: SERVICIOS & APIS -->
                                    <div v-if="activeSettingsTab === 'herramientas'"
                                        class="animate-in fade-in slide-in-from-right-4 duration-500 h-full overflow-y-auto custom-scrollbar pr-4">
                                        <h3
                                            class="text-2xl font-black text-white uppercase tracking-tighter mb-10 flex items-center gap-4 italic text-indigo-400">
                                            <span class="w-12 h-1 bg-indigo-500 rounded-full"></span>
                                            Configuración de Servicios & APIs
                                        </h3>

                                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
                                            <div class="space-y-10">
                                                <!-- BLOQUE AI -->
                                                <div
                                                    class="p-10 bg-white/5 rounded-[40px] border border-white/10 space-y-8">
                                                    <span
                                                        class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] block border-b border-white/5 pb-4 italic underline decoration-indigo-500/30">{{ t('ui_intelligence_level', 'Nivel de Inteligencia') }}</span>
                                                    <div v-for="(label, key) in { GITHUB_TOKEN: 'Mistral (GH Token)', OPENAI_API_KEY: 'OpenAI API Key', ELEVENLABS_API_KEY: 'ElevenLabs SDK', FINA_VOICE_ID: 'ElevenLabs Voice ID' }"
                                                        :key="key" class="space-y-2">
                                                        <label
                                                            class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-2">{{ label }}</label>
                                                        <div class="relative">
                                                            <input
                                                                :type="showPass[key.toLowerCase().split('_')[0]] ? 'text' : 'password'"
                                                                v-model="userSettings.apis[key]"
                                                                class="w-full bg-black/40 border border-white/10 rounded-2xl pl-6 pr-12 py-4 text-xs font-mono focus:border-indigo-500 outline-none transition-all" />
                                                            <button
                                                                @click="showPass[key.toLowerCase().split('_')[0]] = !showPass[key.toLowerCase().split('_')[0]]"
                                                                class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-600 hover:text-indigo-400"><i
                                                                    class="fa-solid"
                                                                    :class="showPass[key.toLowerCase().split('_')[0]] ? 'fa-eye-slash' : 'fa-eye'"></i></button>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- BLOQUE CORREO -->
                                                <div
                                                    class="p-10 bg-white/5 rounded-[40px] border border-white/10 space-y-8">
                                                    <span
                                                        class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] block border-b border-white/5 pb-4 italic underline decoration-indigo-500/30">{{ t('ui_messaging_service', 'Servicio de Mensajería') }}</span>
                                                    <div class="space-y-6">
                                                        <div class="space-y-2">
                                                            <label
                                                                class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-2">{{ t('ui_email_user', 'Email Usuario') }}</label>
                                                            <input type="text" v-model="userSettings.apis.EMAIL_USER"
                                                                class="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-xs font-mono focus:border-indigo-500 outline-none transition-all" />
                                                        </div>
                                                        <div class="space-y-2">
                                                            <label
                                                                class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-2">{{ t('ui_app_password', 'Password Aplicación') }}</label>
                                                            <div class="relative">
                                                                <input :type="showPass.email ? 'text' : 'password'"
                                                                    v-model="userSettings.apis.EMAIL_PASSWORD"
                                                                    class="w-full bg-black/40 border border-white/10 rounded-2xl pl-6 pr-12 py-4 text-xs font-mono focus:border-indigo-500 outline-none transition-all" />
                                                                <button @click="showPass.email = !showPass.email"
                                                                    class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-600 hover:text-indigo-400">
                                                                    <i class="fa-solid"
                                                                        :class="showPass.email ? 'fa-eye-slash' : 'fa-eye'"></i>
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <!-- BLOQUE MODELOS (Agregado para Novatos) -->
                                                <div
                                                    class="p-10 bg-white/5 rounded-[40px] border border-white/10 space-y-8">
                                                    <span
                                                        class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] block border-b border-white/5 pb-4 italic underline decoration-indigo-500/30">{{ t('ui_models_heuristics', 'Modelos & Heurísticas') }}</span>

                                                    <div class="space-y-2">
                                                        <label
                                                            class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-2">{{ t('ui_universal_language', `Idioma Universal (Voz y Escucha)`) }}</label>

                                                        <select v-model="userSettings.apis.FINA_LANGUAGE"
                                                            @change="() => notifyFina(t('ui_restart_for_lang', 'REQUIERE REINICIO PARA APLICAR IDIOMA'))"
                                                            class="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-xs font-black text-indigo-300 focus:border-indigo-500 outline-none transition-all appearance-none cursor-pointer">
                                                            <option value="" disabled>{{ t('ui_select_language', 'Seleccione un idioma...') }}
                                                            </option>
                                                            <option value="es">Español (Recomendado)</option>
                                                            <option value="en">Inglés (English)</option>
                                                            <option value="fr">Francés (Français)</option>
                                                            <option value="de">Alemán (Deutsch)</option>
                                                            <option value="ja">Japonés (日本語)</option>
                                                            <option value="zh">Chino (中文)</option>
                                                        </select>
                                                        <p class="text-[9px] text-slate-500 italic px-2">{{ t('ui_language_download_hint', `Fina descargará automáticamente los modelos en el próximo inicio.`) }}</p>
                                                    </div>

                                                    <div v-for="(label, key) in { VOICE_MODELS_PATH: t('ui_custom_voices_folder_opt', 'Carpeta de Voces Custom (Opcional)'), VOSK_MODEL_PATH: t('ui_custom_vosk_model_opt', 'Modelo Vosk Custom (Opcional)') }"
                                                        :key="key" class="space-y-2">
                                                        <label
                                                            class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-2">{{ label }}</label>
                                                        <div class="flex gap-2">
                                                            <input type="text" v-model="userSettings.apis[key]"
                                                                placeholder="Ej: /home/usuario/voces/"
                                                                class="flex-1 bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-xs font-mono focus:border-indigo-500 outline-none transition-all" />
                                                            <button @click="selectFolder(key)"
                                                                class="px-5 py-4 bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 rounded-2xl border border-indigo-500/30 transition-all font-black">
                                                                <i class="fa-solid fa-folder-open"></i>
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- BLOQUE EXTERNOS -->
                                                <div
                                                    class="p-10 bg-white/5 rounded-[40px] border border-white/10 space-y-8">
                                                    <span
                                                        class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] block border-b border-white/5 pb-4 italic underline decoration-indigo-500/30">{{ t('ui_external_sensors', 'Sensores Externos') }}</span>
                                                    <div v-for="(label, key) in { WEATHER_API_KEY: 'OpenWeather Map', WEATHER_CITY_ID: 'Ciudad ID (Weather)', NEWS_API_KEY: 'NewsAPI.org' }"
                                                        :key="key" class="space-y-2">
                                                        <label
                                                            class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-2">{{ label }}</label>
                                                        <div class="relative">
                                                            <input
                                                                :type="key.includes('KEY') && !showPass[key.toLowerCase().split('_')[0]] ? 'password' : 'text'"
                                                                v-model="userSettings.apis[key]"
                                                                class="w-full bg-black/40 border border-white/10 rounded-2xl pl-6 pr-12 py-4 text-xs font-mono focus:border-indigo-500 outline-none transition-all" />
                                                            <button v-if="key.includes('KEY')"
                                                                @click="showPass[key.toLowerCase().split('_')[0]] = !showPass[key.toLowerCase().split('_')[0]]"
                                                                class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-600 hover:text-indigo-400"><i
                                                                    class="fa-solid"
                                                                    :class="showPass[key.toLowerCase().split('_')[0]] ? 'fa-eye-slash' : 'fa-eye'"></i></button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <div class="space-y-10">
                                                <!-- BLOQUE RUTAS -->
                                                <div
                                                    class="p-10 bg-indigo-500/5 rounded-[40px] border border-indigo-500/10 space-y-8">
                                                    <span
                                                        class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] block border-b border-indigo-500/10 pb-4 italic">{{ t('ui_system_heuristics', 'Heurísticas de Sistema') }}</span>
                                                    <div v-for="(label, key) in { VOICE_MODELS_PATH: t('ui_voice_models_path_label', 'Ruta Modelos Voz'), VOSK_MODEL_PATH: t('ui_vosk_path_label', 'Ruta Vosk (Local)') }"
                                                        :key="key" class="space-y-2">
                                                        <label
                                                            class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-2">{{ label }}</label>
                                                        <div class="flex gap-2">
                                                            <input type="text" v-model="userSettings.apis[key]"
                                                                class="flex-1 bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-[10px] font-mono focus:border-indigo-500 outline-none transition-all" />
                                                            <button @click="selectFolder(key)"
                                                                class="px-6 py-4 bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 rounded-2xl border border-indigo-500/30 transition-all font-black text-xs">
                                                                <i class="fa-solid fa-folder-open"></i>
                                                            </button>
                                                        </div>
                                                    </div>

                                                </div>

                                                <!-- BLOQUE MULTIMEDIA -->
                                                <div
                                                    class="p-10 bg-white/5 rounded-[40px] border border-white/10 space-y-8">
                                                    <span
                                                        class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] block border-b border-white/5 pb-4 italic underline decoration-indigo-500/30">{{ t('ui_generative_generators', 'Generadores Generativos') }}</span>
                                                    <div v-for="(label, key) in { UNSPLASH_ACCESS_KEY: 'Unsplash Access Key', UNSPLASH_SECRET_KEY: 'Unsplash Secret Key', RUNAWAY_API_KEY: 'Runway Gen-2 API' }"
                                                        :key="key" class="space-y-2">
                                                        <label
                                                            class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-2">{{ label }}</label>
                                                        <div class="relative">
                                                            <input
                                                                :type="showPass[key.toLowerCase().split('_')[0]] ? 'text' : 'password'"
                                                                v-model="userSettings.apis[key]"
                                                                class="w-full bg-black/40 border border-white/10 rounded-2xl pl-6 pr-12 py-4 text-xs font-mono focus:border-indigo-500 outline-none transition-all" />
                                                            <button
                                                                @click="showPass[key.toLowerCase().split('_')[0]] = !showPass[key.toLowerCase().split('_')[0]]"
                                                                class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-600 hover:text-indigo-400"><i
                                                                    class="fa-solid"
                                                                    :class="showPass[key.toLowerCase().split('_')[0]] ? 'fa-eye-slash' : 'fa-eye'"></i></button>
                                                        </div>
                                                    </div>
                                                </div>

                                                <!-- BLOQUE CLIMATIZACIÓN -->
                                                <div
                                                    class="p-10 bg-white/5 rounded-[40px] border border-white/10 space-y-8">
                                                    <span
                                                        class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] block border-b border-white/5 pb-4 italic underline decoration-indigo-500/30">Infraestructura
                                                        IoT</span>
                                                    <div class="space-y-2">
                                                        <label
                                                            class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-2">IP
                                                            Aire
                                                            Acondicionado</label>
                                                        <input type="text" v-model="userSettings.apis.AC_IP"
                                                            class="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-xs font-mono focus:border-indigo-500 outline-none transition-all" />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- BOTÓN GUARDAR -->
                                        <div class="mt-12 pt-10 border-t border-white/5 flex justify-end">
                                            <button @click="saveSettings"
                                                class="px-16 h-16 bg-gradient-to-r from-indigo-600 to-blue-700 rounded-full font-black text-xs uppercase tracking-[0.3em] shadow-2xl shadow-indigo-900/40 hover:scale-105 active:scale-95 transition-all text-white">
                                                {{ t('ui_save_core', 'GUARDAR CONFIGURACIÓN CORE') }}
                                            </button>
                                        </div>
                                    </div>

                                    <!-- TAB: PLUGINS / NÓDULOS -->
                                    <div v-if="activeSettingsTab === 'plugins'"
                                        class="animate-in fade-in slide-in-from-right-4 duration-500 h-full overflow-y-auto custom-scrollbar pr-4">
                                        <div class="flex items-center justify-between mb-10">
                                            <h3
                                                class="text-2xl font-black text-white uppercase tracking-tighter flex items-center gap-4 italic text-indigo-400">
                                                <span class="w-12 h-1 bg-indigo-500 rounded-full"></span>
                                                {{ t('ui_connectivity_nodes', 'Nódulos de Conectividad') }}
                                            </h3>
                                            <div class="flex items-center gap-4">
                                                <!-- BOTÓN MARKET (MOVIDO DESDE AGENDA) -->
                                                <button @click="openPluginStore"
                                                    class="px-6 py-2 bg-gradient-to-r from-indigo-600/20 to-blue-600/20 hover:from-indigo-600 hover:to-blue-600 border border-indigo-500/30 rounded-full text-white text-[10px] font-black uppercase tracking-widest transition-all group/market">
                                                    <i
                                                        class="fa-solid fa-puzzle-piece mr-2 group-hover/market:rotate-45 transition-transform duration-500"></i>
                                                    {{ t('ui_plugin_market', 'Market de Plugins') }}
                                                </button>

                                                <button @click="scanNetwork" :disabled="isScanningNetwork"
                                                    class="px-6 py-2 bg-indigo-500/10 hover:bg-indigo-500 border border-indigo-500/30 rounded-full text-white text-[10px] font-black uppercase tracking-widest transition-all">
                                                    <i class="fa-solid mr-2 shadow-sm"
                                                        :class="isScanningNetwork ? 'fa-spinner fa-spin' : 'fa-arrows-rotate'"></i>
                                                    {{ isScanningNetwork ? t('ui_scanning', 'Escaneando...') : t('ui_scan_network', 'Escanear Red') }}

                                                </button>
                                            </div>
                                        </div>

                                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                            <!-- Panel de Dispositivos Detectados -->
                                            <div class="bg-white/5 rounded-[40px] border border-white/10 p-8">
                                                <span
                                                    class="text-[10px] font-black text-indigo-400 uppercase tracking-widest block mb-6 italic">{{ t('ui_local_infra', 'Infraestructura Local') }}</span>
                                                <div
                                                    class="space-y-3 max-h-[500px] overflow-y-auto custom-scrollbar pr-2">
                                                    <div v-for="(dev, index) in scannedDevices" :key="index"
                                                        class="flex flex-col p-5 bg-black/40 rounded-3xl border border-white/5 hover:border-indigo-500/30 transition-all group/node">
                                                        <div class="flex items-center justify-between w-full">
                                                            <div class="flex items-center gap-4">
                                                                <div
                                                                    class="w-10 h-10 rounded-full flex items-center justify-center bg-indigo-500/10 text-indigo-400 group-hover/node:bg-indigo-500 group-hover/node:text-white transition-colors">
                                                                    <i class="fa-solid"
                                                                        :class="dev.assignedType ? (deviceTypesList.find(t => t.id === dev.assignedType)?.icon || 'fa-check') : 'fa-network-wired'"></i>
                                                                </div>
                                                                <div class="flex flex-col">
                                                                    <span class="text-xs font-black text-slate-200">{{ dev.assignedName || dev.vendor || 'Nodo Desconocido' }}</span>
                                                                    <span
                                                                        class="text-[9px] font-mono text-slate-500 uppercase tracking-widest">{{ dev.ip }}</span>
                                                                </div>
                                                            </div>
                                                            <button v-if="!dev.assignedType"
                                                                @click="assigningDeviceIp = assigningDeviceIp === dev.ip ? null : dev.ip; customDeviceName = dev.vendor || ''; customDeviceRoom = 'Living'"
                                                                class="px-4 py-2 rounded-xl bg-indigo-500/10 hover:bg-indigo-500 text-white text-[9px] font-black uppercase transition-all">{{ t('ui_assign', 'Asignar') }}</button>
                                                            <div v-else class="flex items-center gap-3">
                                                                <span
                                                                    class="px-3 py-1 rounded-lg bg-green-500/10 text-green-400 text-[10px] font-black uppercase border border-green-500/20 italic">{{ dev.assignedType }}</span>

                                                                <!-- Button to toggle Primary Status for Mobile Phones -->
                                                                <button v-if="dev.assignedType === 'Celular'"
                                                                    @click="setPrimaryMobile(dev)"
                                                                    class="w-6 h-6 rounded flex items-center justify-center transition-colors"
                                                                    :class="dev.isPrimary ? 'text-yellow-400 hover:text-yellow-300' : 'text-slate-600 hover:text-yellow-400'">
                                                                    <i
                                                                        :class="dev.isPrimary ? 'fa-solid fa-star' : 'fa-regular fa-star'"></i>
                                                                </button>

                                                                <button @click="dev.assignedType = null"
                                                                    class="text-slate-600 hover:text-red-400 transition-colors"><i
                                                                        class="fa-solid fa-trash-can"></i></button>
                                                            </div>
                                                        </div>

                                                        <transition name="fade">
                                                            <div v-if="assigningDeviceIp === dev.ip"
                                                                class="mt-4 pt-4 border-t border-white/5 space-y-4">
                                                                <div class="grid grid-cols-2 gap-4">
                                                                    <div class="space-y-1">
                                                                        <label
                                                                            class="text-[8px] font-black text-slate-500 uppercase ml-2">{{ t('ui_custom_name', 'Nombre Personalizado') }}</label>
                                                                        <input type="text" v-model="customDeviceName"
                                                                            placeholder="Ej: Celular Principal"
                                                                            class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-[10px] font-bold text-white outline-none focus:border-indigo-500 placeholder-slate-600" />
                                                                    </div>
                                                                    <div class="space-y-1">
                                                                        <label
                                                                            class="text-[8px] font-black text-slate-500 uppercase ml-2">{{ t('ui_room_solo_tv', 'Habitáculo (Solo TV)') }}</label>
                                                                        <select v-model="customDeviceRoom"
                                                                            class="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-[10px] font-bold text-white outline-none focus:border-indigo-500 appearance-none">
                                                                            <option v-for="room in roomList" :key="room"
                                                                                :value="room">{{ room }}
                                                                            </option>
                                                                        </select>
                                                                    </div>
                                                                </div>

                                                                <div class="grid grid-cols-4 gap-2">
                                                                    <button v-for="type in deviceTypesList"
                                                                        :key="type.id"
                                                                        @click="assignDeviceType(dev, type.id, customDeviceName)"
                                                                        class="flex flex-col items-center p-3 rounded-2xl bg-white/5 hover:bg-indigo-600 transition-all border border-transparent hover:border-indigo-400/50 group">
                                                                        <i class="fa-solid text-sm mb-2 group-hover:scale-110"
                                                                            :class="type.icon"></i>
                                                                        <span
                                                                            class="text-[7px] font-black uppercase text-center leading-tight">{{ type.label }}</span>
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        </transition>
                                                    </div>
                                                </div>
                                            </div>

                                            <div class="space-y-6">
                                                <!-- Instalación Manual -->
                                                <div
                                                    class="p-8 bg-gradient-to-br from-indigo-900/20 to-slate-900/40 rounded-[40px] border border-white/10 relative overflow-hidden group">
                                                    <i
                                                        class="fa-solid fa-cloud-arrow-down absolute -right-4 -top-4 text-8xl text-indigo-500/10 group-hover:scale-110 transition-transform"></i>
                                                    <h4
                                                        class="text-sm font-black text-white uppercase tracking-widest mb-4">
                                                        {{ t('ui_manual_install', 'Instalar Nuevos Plugins') }}
                                                    </h4>
                                                    <div class="relative">
                                                        <input type="text"
                                                            :placeholder="t('ui_repo_url_placeholder', 'URL del repositorio o .zip...')"
                                                            class="w-full bg-black/40 border border-white/10 rounded-2xl px-6 py-4 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-all font-mono">
                                                        <button
                                                            class="absolute right-3 top-3 w-10 h-10 bg-indigo-500 rounded-xl text-white hover:scale-105 transition-transform"><i
                                                                class="fa-solid fa-download"></i></button>
                                                    </div>
                                                </div>

                                                <!-- Migración -->
                                                <div
                                                    class="p-8 bg-white/5 rounded-[40px] border border-white/10 flex items-center justify-between">
                                                    <div class="flex flex-col">
                                                        <span
                                                            class="text-sm font-black text-white uppercase tracking-widest">{{ t('ui_migrated_core', 'Migración Core') }}</span>
                                                        <span
                                                            class="text-[10px] text-slate-500 uppercase font-black mt-1">{{ t('ui_sync_root_config', 'Sincronizar config raíz') }}</span>
                                                    </div>
                                                    <button @click="importFromCore"
                                                        class="px-8 py-3 bg-indigo-500/10 border border-indigo-500/30 rounded-2xl text-indigo-400 text-[10px] font-black uppercase hover:bg-indigo-500 hover:text-white transition-all text-white">{{ t('ui_import', 'Importar') }}</button>
                                                </div>

                                                <!-- ADB -->
                                                <div
                                                    class="p-8 bg-white/5 rounded-[40px] border border-white/10 flex items-center justify-between">
                                                    <div class="flex flex-col">
                                                        <span
                                                            class="text-sm font-black text-white uppercase tracking-widest">{{ t('ui_adb_debugging', 'Depuración ADB') }}</span>
                                                        <span
                                                            class="text-[10px] text-slate-500 uppercase font-black mt-1">{{ t('ui_restart_tv_server', 'Reiniciar servidor TV') }}</span>
                                                    </div>
                                                    <button
                                                        class="px-8 py-3 bg-red-500/10 border border-red-500/30 rounded-2xl text-red-400 text-[10px] font-black uppercase hover:bg-red-500 hover:text-white transition-all text-white">ADB
                                                        Kill</button>
                                                </div>
                                            </div>
                                            <div v-if="mobileHubError"
                                                class="p-4 mb-6 bg-red-500/10 border border-red-500/30 rounded-2xl flex items-center gap-4 animate-in slide-in-from-top-2">
                                                <i class="fa-solid fa-circle-exclamation text-red-500 text-xl"></i>
                                                <span class="text-xs font-bold text-red-200 uppercase">{{ mobileHubError }}</span>
                                            </div>
                                        </div>
                                    </div>


                                    <!-- SUB-TAB: TV (VISUAL) -->
                                    <div v-if="activeSettingsTab === 'tv'"
                                        class="animate-in fade-in slide-in-from-right-4 duration-500 flex flex-col h-full">
                                        <h3
                                            class="text-2xl font-black text-white uppercase tracking-tighter mb-6 flex items-center gap-4">
                                            <span class="w-12 h-1 bg-purple-500 rounded-full"></span>
                                            {{ t('ui_visual_config_tv', 'Configuración Visual: TV') }}
                                        </h3>

                                        <!-- Room Selector -->
                                        <div class="flex gap-4 mb-8 overflow-x-auto pb-2 scrollbar-hide">
                                            <button v-for="room in roomList" :key="room" @click="activeTvRoom = room"
                                                :class="activeTvRoom === room ? 'bg-purple-500 text-white shadow-[0_0_20px_rgba(168,85,247,0.4)]' : 'bg-white/5 text-slate-400 hover:text-white'"
                                                class="px-8 py-3 rounded-full font-black text-xs uppercase tracking-widest transition-all whitespace-nowrap border border-transparent hover:border-white/10">
                                                {{ room }}
                                            </button>
                                        </div>

                                        <div
                                            class="grid grid-cols-2 gap-10 flex-1 overflow-y-auto custom-scrollbar pr-4">
                                            <div class="space-y-6">
                                                <div
                                                    class="flex items-center justify-between p-6 bg-purple-500/10 rounded-3xl border border-purple-500/20">
                                                    <div class="flex flex-col">
                                                        <span class="text-xs font-black text-white uppercase">TV
                                                            {{ activeTvRoom }}</span>
                                                        <span
                                                            class="text-[10px] font-black text-purple-400 mt-1 uppercase tracking-widest leading-relaxed">{{ t('ui_primary_device', 'Dispositivo Principal') }}</span>
                                                        <span v-if="activeTvIp"
                                                            class="text-[9px] font-mono text-emerald-400 mt-1 font-bold">IPV4:
                                                            {{ activeTvIp }}</span>
                                                        <span v-if="activeTvIp"
                                                            class="text-[9px] font-bold text-emerald-400 mt-1 uppercase">{{ t('ui_synced', 'Sincronizado') }}</span>
                                                        <span v-else
                                                            class="text-[9px] font-bold text-red-500 mt-1 uppercase">{{ t('ui_no_connection', 'Sin Conexión') }}</span>
                                                    </div>
                                                    <div class="w-3 h-3 rounded-full shadow-[0_0_10px_lime] animate-pulse"
                                                        :class="activeTvIp ? 'bg-green-500' : 'bg-red-500'">
                                                    </div>
                                                </div>

                                                <div v-if="activeTvIp && tvStatuses[activeTvIp]" class="space-y-4">
                                                    <span
                                                        class="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-4">{{ t('ui_apps_config', 'Configuración de Apps') }}</span>
                                                    <div class="grid grid-cols-2 gap-4">
                                                        <div v-for="(pkg, app) in userSettings.tv_apps" :key="app"
                                                            class="p-4 bg-white/5 rounded-2xl border border-white/5">
                                                            <span
                                                                class="text-[9px] font-black text-purple-400 uppercase block mb-1">{{ app }}</span>
                                                            <span
                                                                class="text-[8px] font-mono text-slate-400 truncate block">{{ pkg }}</span>
                                                        </div>
                                                    </div>
                                                    <button @click="scanTvApps"
                                                        class="w-full mt-4 py-3 bg-purple-500/10 border border-purple-500/30 rounded-2xl text-[10px] font-black text-purple-400 uppercase tracking-widest hover:bg-purple-500 hover:text-white transition-all">
                                                        <i class="fa-solid fa-magnifying-glass mr-2"></i>
                                                        {{ t('ui_scan_installed_apps', 'Escanear Apps Instaladas') }}
                                                    </button>
                                                </div>
                                                <div v-else
                                                    class="p-8 bg-white/5 rounded-3xl border border-white/5 flex flex-col items-center justify-center text-center gap-4 opacity-50">
                                                    <i
                                                        class="fa-solid fa-plug-circle-xmark text-3xl text-slate-600"></i>
                                                    <span
                                                        class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">{{ t('ui_connect_device_for_apps', `Conecte el dispositivo para ver apps`) }}</span>

                                                </div>
                                            </div>

                                            <div v-if="activeTvIp && tvStatuses[activeTvIp]" class="space-y-6">
                                                <div class="flex items-center justify-between mb-4">
                                                    <span
                                                        class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Gestion
                                                        de
                                                        Canales</span>
                                                    <button
                                                        class="text-[9px] font-black text-purple-400 hover:text-white uppercase transition-colors"><i
                                                            class="fa-solid fa-plus"></i></button>
                                                </div>

                                                <div class="max-h-[50vh] overflow-y-auto custom-scrollbar space-y-2">
                                                    <div v-for="(num, name) in tvChannels" :key="name"
                                                        class="flex items-center justify-between p-4 bg-white/5 rounded-2xl border transition-all cursor-pointer hover:bg-white/10"
                                                        :class="isChannelEnabled(name) ? 'border-white/5' : 'border-red-500/20 opacity-50'"
                                                        @click="toggleChannel(name)">
                                                        <div class="flex items-center gap-3">
                                                            <div class="w-2 h-2 rounded-full"
                                                                :class="isChannelEnabled(name) ? 'bg-emerald-500' : 'bg-red-500'">
                                                            </div>
                                                            <span class="text-xs font-black"
                                                                :class="isChannelEnabled(name) ? 'text-white' : 'text-slate-500'">{{ name }}</span>
                                                        </div>
                                                        <span class="text-[9px] font-mono"
                                                            :class="isChannelEnabled(name) ? 'text-purple-400' : 'text-slate-600'">{{ num }}</span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div v-else
                                                class="flex flex-col items-center justify-center p-12 bg-white/5 rounded-[40px] border border-white/5 gap-6 opacity-40">
                                                <div class="relative">
                                                    <i class="fa-solid fa-tv text-6xl text-slate-700"></i>
                                                    <i
                                                        class="fa-solid fa-slash text-4xl text-red-500/50 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"></i>
                                                </div>
                                                <span
                                                    class="text-xs font-black text-slate-500 uppercase tracking-[0.3em]">Sin
                                                    Conexión con {{ activeTvRoom }}</span>
                                            </div>
                                        </div>

                                        <!-- BOTÓN GENERAL DE GUARDADO -->
                                        <div class="mt-6 pt-6 border-t border-white/5 flex justify-end">
                                            <button @click="saveSettings"
                                                class="px-12 h-12 bg-gradient-to-r from-purple-600 to-indigo-700 rounded-full font-black text-xs uppercase tracking-[0.2em] shadow-2xl shadow-purple-900/40 active:scale-95 transition-all text-white">
                                                {{ t('ui_save_tv_settings', 'GUARDAR AJUSTES TV') }} </button>
                                        </div>
                                    </div>

                                    <!-- SUB-TAB: TIMBRE (VISUAL) -->
                                    <div v-if="activeSettingsTab === 'timbre'"
                                        class="animate-in fade-in slide-in-from-right-4 duration-500">
                                        <h3
                                            class="text-2xl font-black text-white uppercase tracking-tighter mb-10 flex items-center gap-4">
                                            <span class="w-12 h-1 bg-purple-500 rounded-full"></span> {{ t('ui_timbre_title', 'Visual: Timbre Cam') }}
                                        </h3>
                                        <div class="space-y-6">
                                            <div class="flex flex-col gap-2">
                                                <label
                                                    class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-1">IP
                                                    del Timbre</label>
                                                <input type="text" v-model="userSettings.apis.TIMBRE_IP"
                                                    class="bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-xs font-mono focus:border-purple-500 outline-none transition-all" />
                                            </div>
                                            <div class="flex flex-col gap-2">
                                                <label
                                                    class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-1">Interfaz
                                                    de Red</label>
                                                <input type="text" v-model="userSettings.apis.TIMBRE_NET_INTERFACE"
                                                    class="bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-xs font-mono focus:border-purple-500 outline-none transition-all" />
                                            </div>
                                            <div
                                                class="p-6 bg-yellow-500/10 border border-yellow-500/20 rounded-2xl mt-4">
                                                <p
                                                    class="text-[10px] text-yellow-500 font-bold uppercase tracking-widest flex items-center gap-2">
                                                    <i class="fa-solid fa-triangle-exclamation"></i>
                                                    Requiere
                                                    Waydroid
                                                </p>
                                                <p class="text-[9px] text-slate-400 mt-2 leading-relaxed">
                                                    El timbre utiliza la app
                                                    Tuya Smart corriendo en
                                                    Waydroid.
                                                    Asegúrese
                                                    de que el contenedor esté
                                                    iniciado y la app
                                                    configurada.
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- SUB-TAB: ILUMINACIÓN (VISUAL) -->
                                    <div v-if="activeSettingsTab === 'iluminacion'"
                                        class="animate-in fade-in slide-in-from-right-4 duration-500">
                                        <h3
                                            class="text-2xl font-black text-white uppercase tracking-tighter mb-10 flex items-center gap-4">
                                            <span class="w-12 h-1 bg-purple-500 rounded-full"></span> {{ t('ui_lighting_title', 'Visual: Iluminación') }}
                                        </h3>
                                        <div class="grid grid-cols-3 gap-6">
                                            <div v-for="luz in ['Living Principal', 'Cocina', 'Dormitorio', 'Pasillo']"
                                                :key="luz"
                                                class="aspect-square rounded-[30px] bg-white/5 border border-white/5 flex flex-col items-center justify-center gap-4 hover:bg-white/10 transition-all cursor-pointer group">
                                                <i
                                                    class="fa-solid fa-lightbulb text-4xl text-slate-700 group-hover:text-yellow-400 transition-colors shadow-2xl"></i>
                                                <span
                                                    class="text-[10px] font-black text-slate-400 uppercase tracking-widest">{{ luz }}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- SUB-TAB: SEGURIDAD (SEGURIDAD) -->
                                    <div v-if="activeSettingsDomain === 'seguridad'"
                                        class="animate-in fade-in slide-in-from-right-4 duration-500 flex flex-col h-full">
                                        <h3
                                            class="text-2xl font-black text-white uppercase tracking-tighter mb-6 flex items-center gap-4">
                                            <span class="w-12 h-1 bg-red-500 rounded-full"></span> {{ t('ui_security_title', 'Seguridad Avanzada Fina') }}
                                        </h3>

                                        <!-- TABLA SUPERIOR (Bio, Camaras, Puertas) -->
                                        <div v-if="activeSettingsTab === 'biometria'" class="space-y-6">
                                            <div class="flex gap-4 mb-6">
                                                <button
                                                    v-for="bio in [{ id: 'huella', icon: 'fingerprint', key: 'ui_bio_finger' }, { id: 'facial', icon: 'face-smile-beam', key: 'ui_bio_facial' }, { id: 'voz', icon: 'microphone-lines', key: 'ui_bio_voice' }]"
                                                    :key="bio.id" @click="activeBioTab = bio.id"
                                                    :class="activeBioTab === bio.id ? 'bg-red-500 text-white shadow-[0_0_20px_rgba(239,68,68,0.4)]' : 'bg-white/5 text-slate-400 hover:text-white'"
                                                    class="px-8 py-3 rounded-full font-black text-xs uppercase tracking-widest transition-all border border-transparent hover:border-white/10">
                                                    {{ t(bio.key, bio.id) }}
                                                </button>

                                            </div>

                                            <!-- CONTENIDO BIOMETRIA -->
                                            <div
                                                class="p-8 bg-white/5 rounded-[40px] border border-white/10 min-h-[400px]">
                                                <div v-if="activeBioTab === 'huella'"
                                                    class="flex flex-col items-center justify-center h-full gap-6 text-center animate-in zoom-in-95">
                                                    <div
                                                        class="h-24 w-24 rounded-full bg-red-500/10 flex items-center justify-center border-2 border-red-500/20">
                                                        <i class="fa-solid fa-fingerprint text-5xl text-red-500"></i>
                                                    </div>
                                                    <div>
                                                        <h4 class="text-xl font-black text-white uppercase">{{ t('ui_bio_finger_title', 'Escáner Dactilar') }}</h4>
                                                        <p class="text-[10px] text-slate-400 mt-2 max-w-sm mx-auto">{{ t('ui_bio_finger_desc', 'Gestión de huellas mediante fprintd. Utilice el sensor físico para registrar o eliminar accesos.') }}</p>
                                                    </div>
                                                    <button @click="enrollFinger"
                                                        class="px-10 py-4 bg-red-600 hover:bg-red-500 text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all">
                                                        <i class="fa-solid fa-plus mr-2"></i> {{ t('ui_bio_finger_btn', 'Registrar Nueva Huella') }}
                                                    </button>
                                                </div>

                                                <div v-if="activeBioTab === 'facial'"
                                                    class="flex flex-col items-center justify-center h-full gap-6 text-center animate-in zoom-in-95">
                                                    <div
                                                        class="h-24 w-24 rounded-full bg-blue-500/10 flex items-center justify-center border-2 border-blue-500/20">
                                                        <i
                                                            class="fa-solid fa-face-smile-beam text-5xl text-blue-500"></i>
                                                    </div>
                                                    <div>
                                                        <h4 class="text-xl font-black text-white uppercase">{{ t('ui_bio_facial_title', 'Reconocimiento Facial') }}</h4>
                                                        <p class="text-[10px] text-slate-400 mt-2 max-w-sm mx-auto">{{ t('ui_bio_facial_desc', 'Sistema de autenticación mediante cámara web y modelos de visión computarizada local.') }}</p>
                                                    </div>
                                                    <div class="flex gap-4">
                                                        <button @click="enrollFace"
                                                            class="px-8 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all">
                                                            {{ t('ui_bio_facial_btn', 'Entrenar Modelo') }}
                                                        </button>
                                                    </div>
                                                </div>

                                                <div v-if="activeBioTab === 'voz'"
                                                    class="flex flex-col items-center justify-center h-full gap-6 text-center animate-in zoom-in-95">
                                                    <div
                                                        class="h-24 w-24 rounded-full bg-purple-500/10 flex items-center justify-center border-2 border-purple-500/20">
                                                        <i
                                                            class="fa-solid fa-microphone-lines text-5xl text-purple-500"></i>
                                                    </div>
                                                    <div>
                                                        <h4 class="text-xl font-black text-white uppercase">{{ t('ui_bio_voice_title', 'Biometría de Voz') }}</h4>
                                                        <p class="text-[10px] text-slate-400 mt-2 max-w-sm mx-auto">{{ t('ui_bio_voice_desc', 'Fina aprende de tu voz para validar comandos críticos de seguridad.') }}</p>
                                                    </div>
                                                    <button @click="enrollVoice"
                                                        class="px-10 py-4 bg-purple-600 hover:bg-purple-500 text-white rounded-2xl font-black text-xs uppercase tracking-widest transition-all">
                                                        <i class="fa-solid fa-microphone mr-2"></i> {{ t('ui_bio_voice_btn', 'Iniciar Entrenamiento') }}
                                                    </button>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- CAMARAS GRID -->
                                        <div v-if="activeSettingsTab === 'camaras'" class="h-full flex flex-col">
                                            <div class="flex items-center justify-between mb-6">
                                                <h4 class="text-sm font-black text-slate-300 uppercase tracking-widest">
                                                    Sistema CCTV (8 Canales)
                                                </h4>
                                                <div class="flex gap-2">
                                                    <button
                                                        class="px-4 py-2 bg-white/5 rounded-lg text-[10px] font-bold text-slate-400">Grid
                                                        2x4</button>
                                                    <button
                                                        class="px-4 py-2 bg-white/5 rounded-lg text-[10px] font-bold text-slate-400">{{ t('ui_btn_list', 'Listado') }}</button>
                                                </div>
                                            </div>
                                            <div class="grid grid-cols-4 gap-4 flex-1">
                                                <div v-for="cam in 8" :key="cam"
                                                    class="bg-black/40 rounded-xl border border-white/5 relative group overflow-hidden">
                                                    <div class="absolute inset-0 flex items-center justify-center">
                                                        <i class="fa-solid fa-video-slash text-slate-700 text-2xl"></i>
                                                    </div>
                                                    <span
                                                        class="absolute top-3 left-3 text-[9px] font-black text-slate-500 bg-black/60 px-2 py-1 rounded">CAM
                                                        {{ cam }}</span>
                                                    <div
                                                        class="absolute inset-0 bg-red-500/5 opacity-0 group-hover:opacity-100 transition-opacity flex items-end justify-center pb-4">
                                                        <button
                                                            class="text-[10px] font-bold text-red-400 bg-red-900/80 px-4 py-2 rounded-full">CONFIGURAR</button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- PUERTAS -->
                                        <div v-if="activeSettingsTab === 'puertas'"
                                            class="h-full flex flex-col justify-center">
                                            <div class="grid grid-cols-2 gap-8">
                                                <!-- Garaje -->
                                                <div
                                                    class="p-10 bg-white/5 rounded-[40px] border border-white/10 flex flex-col items-center gap-6 group hover:border-red-500/40 transition-all">
                                                    <i
                                                        class="fa-solid fa-warehouse text-6xl text-slate-600 group-hover:text-red-500 transition-colors"></i>
                                                    <h4
                                                        class="text-2xl font-black text-white uppercase tracking-tighter">
                                                        Garaje</h4>
                                                    <div class="flex gap-2">
                                                        <span
                                                            class="px-4 py-1.5 rounded-full bg-red-500/20 text-red-500 text-[10px] font-black uppercase">{{ t('ui_closed', 'Cerrado') }}</span>
                                                        <span
                                                            class="px-4 py-1.5 rounded-full bg-slate-800 text-slate-500 text-[10px] font-black uppercase">Wifi</span>
                                                    </div>
                                                    <button
                                                        class="w-full py-4 bg-white/5 rounded-2xl text-[10px] font-black text-slate-300 uppercase tracking-widest hover:bg-white/10">Gestionar
                                                        Acceso</button>
                                                </div>
                                                <!-- Entrada Principal -->
                                                <div
                                                    class="p-10 bg-white/5 rounded-[40px] border border-white/10 flex flex-col items-center gap-6 group hover:border-red-500/40 transition-all">
                                                    <i
                                                        class="fa-solid fa-door-closed text-6xl text-slate-600 group-hover:text-red-500 transition-colors"></i>
                                                    <h4
                                                        class="text-2xl font-black text-white uppercase tracking-tighter">
                                                        Entrada Principal</h4>
                                                    <div class="flex gap-2">
                                                        <span
                                                            class="px-4 py-1.5 rounded-full bg-green-500/20 text-green-500 text-[10px] font-black uppercase">Seguro
                                                            Activo</span>
                                                        <span
                                                            class="px-4 py-1.5 rounded-full bg-slate-800 text-slate-500 text-[10px] font-black uppercase">Zigbee</span>
                                                    </div>
                                                    <button
                                                        class="w-full py-4 bg-white/5 rounded-2xl text-[10px] font-black text-slate-300 uppercase tracking-widest hover:bg-white/10">Gestionar
                                                        Acceso</button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- SUB-TAB: AIRE & HABITAT (HABITAT) -->
                                    <div v-if="activeSettingsDomain === 'habitat'"
                                        class="animate-in fade-in slide-in-from-right-4 duration-500">
                                        <h3
                                            class="text-2xl font-black text-white uppercase tracking-tighter mb-10 flex items-center gap-4">
                                            <span class="w-12 h-1 bg-emerald-500 rounded-full"></span>
                                            Habitat & Confort
                                        </h3>

                                        <!-- AIRE AC (Original Content Refined) -->
                                        <div v-if="activeSettingsTab === 'aire'" class="grid grid-cols-2 gap-10">
                                            <div class="space-y-6">
                                                <div class="flex flex-col gap-2">
                                                    <label
                                                        class="text-[9px] font-black text-slate-500 uppercase tracking-widest px-1">IP
                                                        del Equipo
                                                        AC</label>
                                                    <input type="text" :value="userSettings.apis.AC_IP"
                                                        @input="e => userSettings.apis.AC_IP = e.target.value"
                                                        class="bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-xs font-mono focus:border-emerald-500 outline-none transition-all" />
                                                </div>

                                                <div
                                                    class="flex flex-col p-8 bg-white/5 rounded-[40px] border border-white/10 shadow-2xl gap-8">
                                                    <div
                                                        class="flex flex-col items-center border-b border-white/5 pb-4">
                                                        <span
                                                            class="text-[11px] font-black text-emerald-500 uppercase tracking-[0.2em] leading-none">Consumo
                                                            Energético</span>
                                                    </div>
                                                    <div class="flex items-center justify-center gap-12">
                                                        <div class="flex flex-col items-center">
                                                            <div class="flex items-baseline">
                                                                <span
                                                                    class="text-2xl font-mono text-white tracking-tighter leading-none">{{ acState.watts !== undefined ? acState.watts : '---' }}</span>
                                                                <span
                                                                    class="text-xs font-black text-emerald-400/40 ml-2">W</span>
                                                            </div>
                                                            <span
                                                                class="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-3">{{ t('ui_power', 'Potencia') }}</span>
                                                        </div>
                                                        <div class="w-px h-12 bg-white/10">
                                                        </div>
                                                        <div v-if="acState.total_kwh !== undefined && acState.total_kwh !== null"
                                                            class="flex flex-col items-center">
                                                            <div class="flex items-baseline">
                                                                <span
                                                                    class="text-2xl font-black text-red-400/70 tracking-tighter leading-none">{{ acState.total_kwh }}</span>
                                                                <span
                                                                    class="text-xs font-black text-purple-400/40 ml-1">kWh</span>
                                                            </div>
                                                            <span
                                                                class="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-3">{{ t('ui_accumulated', 'Acumulado') }}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>

                                            <div
                                                class="p-8 bg-emerald-500/5 border border-emerald-500/20 rounded-[40px]">
                                                <h4
                                                    class="text-[10px] font-black text-emerald-400 uppercase tracking-widest mb-6">
                                                    Estado Actual</h4>
                                                <div class="space-y-4">
                                                    <div
                                                        class="flex justify-between items-center border-b border-emerald-500/10 pb-2">
                                                        <span
                                                            class="text-[9px] font-black text-slate-500 uppercase tracking-widest">Energía</span>
                                                        <span class="text-xs font-black"
                                                            :class="acState.power ? 'text-emerald-500' : 'text-red-500'">{{ acState.power ? 'ENCENDIDO' : 'APAGADO' }}</span>
                                                    </div>
                                                    <div
                                                        class="flex justify-between items-center border-b border-emerald-500/10 pb-2">
                                                        <span
                                                            class="text-[9px] font-black text-slate-500 uppercase tracking-widest">{{ t('ui_temperature', 'Temperatura') }}</span>
                                                        <span class="text-xs font-mono font-bold text-white">{{ acState.temp }}°C</span>
                                                    </div>
                                                    <div class="flex justify-between items-center">
                                                        <span
                                                            class="text-[9px] font-black text-slate-500 uppercase tracking-widest">{{ t('ui_mode', 'Modo') }}</span>
                                                        <span class="text-xs font-black text-white uppercase">{{ acState.mode }}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <!-- Placeholder Tabs for Habitat -->
                                        <div v-else
                                            class="flex flex-col items-center justify-center h-[400px] text-center opacity-50">
                                            <i class="fa-solid fa-hammer text-6xl text-emerald-500 mb-6"></i>
                                            <h4 class="text-2xl font-black text-white uppercase">
                                                En Construcción
                                            </h4>
                                            <p class="text-xs font-bold text-slate-500 mt-2 uppercase tracking-widest">
                                                Módulo {{ activeSettingsTab }}
                                                en
                                                desarrollo</p>
                                        </div>

                                        <!-- BOTÓN GENERAL DE GUARDADO HABITAT -->
                                        <div v-if="activeSettingsTab === 'aire'"
                                            class="mt-12 pt-8 border-t border-white/5 flex justify-end">
                                            <button @click="saveSettings"
                                                class="px-12 h-14 bg-gradient-to-r from-emerald-600 to-teal-700 rounded-full font-black text-xs uppercase tracking-[0.2em] shadow-2xl shadow-emerald-900/40 active:scale-95 transition-all text-white">
                                                GUARDAR CONFIGURACIÓN
                                            </button>
                                        </div>
                                    </div>
                                </div> <!-- Cierre del Content (3264) -->
                            </div> <!-- Cierre del Layout (3141) -->
                        </div> <!-- Cierre del Tab Ajustes (3065) -->
                    </transition>
                </div> <!-- Cierre del Container Inner (2054) -->
            </div> <!-- Cierre del Container Outer (2053) -->

            <!-- MODAL ACERCA DE (RESTAURADO) [ESTRICTO] -->
            <transition name="fade">
                <div v-if="showCredits"
                    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/85 backdrop-blur-xl p-8"
                    @click.self="showCredits = false">
                    <div
                        class="bg-[#0f172a] w-full max-w-lg rounded-[40px] border border-white/10 shadow-[0_0_80px_rgba(34,211,238,0.15)] overflow-hidden animate-in zoom-in-95 duration-500">
                        <div
                            class="bg-gradient-to-br from-cyan-600/20 to-purple-600/20 p-10 border-b border-white/5 flex flex-col items-center text-center relative">
                            <!-- Boton Cerrar Modal -->
                            <button @click="showCredits = false"
                                class="absolute top-6 right-6 text-slate-500 hover:text-white transition-colors text-xl"><i
                                    class="fa-solid fa-xmark"></i></button>

                            <img src="/assets/avatar.png"
                                class="h-28 w-28 rounded-full border-4 border-[#020617] shadow-2xl mb-6" />
                            <h3 class="text-3xl font-black text-white tracking-tighter mb-1 uppercase">
                                Fina AI Ergen
                            </h3>
                            <div
                                class="flex items-center gap-2 bg-cyan-400/10 px-3 py-1 rounded-full border border-cyan-400/20">
                                <span class="text-[10px] font-mono text-cyan-400 font-bold tracking-widest uppercase">{{ version }}</span>
                            </div>
                        </div>
                        <div class="p-10 space-y-8">
                            <div class="grid grid-cols-2 gap-6 w-full text-center">
                                <div class="p-5 bg-white/5 rounded-3xl border border-white/5">
                                    <span class="text-[9px] font-black text-slate-500 uppercase block mb-1">{{ t('ui_author', 'Autor') }}</span>
                                    <span class="text-sm font-bold text-slate-200">Dankopetro</span>
                                </div>
                                <div class="p-5 bg-white/5 rounded-3xl border border-white/5">
                                    <span class="text-[9px] font-black text-slate-500 uppercase block mb-1">{{ t('ui_created', 'Creado') }}</span>
                                    <span class="text-sm font-bold text-slate-200 uppercase">{{ buildDate }}</span>
                                </div>
                            </div>
                            {{ t('ui_fina_description', '"Sistema avanzado de asistencia por voz e integración domótica diseñado para Linux(Mac y Windows también)"') }}

                            <button @click="showCredits = false"
                                class="w-full h-14 rounded-3xl bg-cyan-500 text-[#020617] font-black text-xs uppercase tracking-widest shadow-xl shadow-cyan-900/30">{{ t('ui_close', 'Cerrar') }}</button>
                        </div>
                    </div>
                </div>
            </transition>

            <!-- VENTANA FLOTANTE DEL TIMBRE [ESTRICTO - CORRECCIÓN TOTAL] -->
            <transition name="fade">
                <div v-if="showDoorbell"
                    class="fixed inset-0 z-[200] flex items-center justify-center bg-black/90 backdrop-blur-2xl p-4">
                    <div class="flex flex-col items-center max-h-screen">

                        <!-- HEADER POR FUERA (ARRIBA DEL VIDEO) -->
                        <div
                            class="w-full max-w-[420px] flex items-center justify-between mb-5 px-4 animate-in fade-in slide-in-from-top-4 duration-500">
                            <div
                                class="flex items-center gap-3 bg-slate-900/90 px-5 py-2.5 rounded-2xl border border-white/10 shadow-[0_0_20px_rgba(0,0,0,0.5)]">
                                <div
                                    class="w-3 h-3 rounded-full bg-red-500 animate-pulse shadow-[0_0_10px_rgba(239,68,68,0.8)]">
                                </div>
                                <span
                                    class="text-[11px] font-black text-white uppercase tracking-[0.2em] leading-none">CÁMARA
                                    EN VIVO - TIMBRE</span>
                            </div>
                            <button @click="hangUp"
                                class="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-2xl text-[11px] font-black uppercase transition-all shadow-xl border border-white/5 active:scale-95 leading-none">
                                COLGAR / CERRAR
                            </button>
                        </div>

                        <!-- VIDEO ENTERO (SIN ESPACIOS VACÍOS - FULL FILL) -->
                        <div
                            class="w-[450px] h-[720px] bg-black rounded-[50px] border-2 border-cyan-500/50 shadow-[0_0_80px_rgba(34,211,238,0.25)] overflow-hidden relative animate-in zoom-in-95 duration-500">
                            <img v-if="streamUrl" :src="'http://127.0.0.1:8555/stream.mjpg?t=' + streamKey"
                                class="w-full h-full object-cover" />
                            <div v-else
                                class="w-full h-full flex flex-col items-center justify-center gap-6 bg-slate-950">
                                <i class="fa-solid fa-spinner fa-spin text-5xl text-cyan-500"></i>
                                <span
                                    class="text-[12px] font-black text-slate-500 uppercase tracking-widest animate-pulse">Iniciando
                                    Enlace...</span>
                            </div>
                        </div>

                        <div class="mt-4 opacity-30">
                            <span class="text-[10px] font-black text-cyan-400 uppercase tracking-[0.6em]">FINA
                                ADVANCED
                                SECURITY</span>
                        </div>
                    </div>
                </div>
            </transition>

            <!-- SENTINEL OVERLAY (MODAL) -->
            <transition name="fade">
                <div v-if="showSentinel"
                    class="fixed inset-0 z-[100] bg-[#050510] flex flex-col animate-in fade-in duration-300">
                    <!-- HEADER -->
                    <div
                        class="h-24 border-b border-red-900/30 bg-gradient-to-r from-black via-red-950/20 to-black flex items-center justify-between px-12 shrink-0 backdrop-blur-md">
                        <div class="flex items-center gap-6">
                            <div class="relative">
                                <i class="fa-solid fa-shield-cat text-4xl text-red-500 animate-pulse relative z-10"></i>
                                <div class="absolute inset-0 bg-red-500 blur-xl opacity-20 animate-pulse"></div>
                            </div>
                            <div class="flex flex-col">
                                <h1 class="text-3xl font-black text-white uppercase tracking-tighter italic">
                                    Fina Centinela</h1>
                                <div class="flex items-center gap-3">
                                    <span class="text-xs font-mono text-red-400 uppercase tracking-[0.4em]">Sistema
                                        de Protección Activa</span>
                                    <span
                                        class="px-2 py-0.5 bg-red-500/20 border border-red-500/30 rounded text-[10px] text-red-400 font-bold">V
                                        2.1.0</span>
                                </div>
                            </div>
                        </div>
                        <button @click="showSentinel = false"
                            class="w-12 h-12 rounded-full hover:bg-white/10 flex items-center justify-center transition-all group">
                            <i
                                class="fa-solid fa-xmark text-2xl text-slate-500 group-hover:text-white group-hover:rotate-90 transition-transform duration-300"></i>
                        </button>
                    </div>

                    <!-- MAIN CONTENT -->
                    <div class="flex-1 flex overflow-hidden">
                        <!-- LEFT PANEL: RADAR -->
                        <div
                            class="w-[40%] border-r border-white/5 p-8 flex flex-col items-center justify-center relative bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-red-900/10 via-transparent to-transparent">
                            <!-- Scanlines Effect -->
                            <div
                                class="absolute inset-0 pointer-events-none opacity-10 bg-[url('https://media.giphy.com/media/26tn33aiTi1jkl6H6/giphy.gif')] bg-cover mix-blend-overlay">
                            </div>

                            <!-- CSS RADAR -->
                            <div class="relative w-80 h-80 flex items-center justify-center mb-12">
                                <div
                                    class="absolute inset-0 rounded-full border border-red-500/20 shadow-[0_0_50px_rgba(239,68,68,0.1)]">
                                </div>
                                <div
                                    class="absolute inset-0 rounded-full border-t border-red-500/40 animate-[spin_8s_linear_infinite]">
                                </div>
                                <div
                                    class="absolute inset-8 rounded-full border border-red-500/10 border-dashed animate-[spin_12s_linear_infinite_reverse]">
                                </div>
                                <div class="absolute inset-20 rounded-full border border-red-500/5"></div>

                                <!-- Axis -->
                                <div class="absolute w-full h-px bg-red-500/20 top-1/2 -translate-y-1/2"></div>
                                <div class="absolute h-full w-px bg-red-500/20 left-1/2 -translate-x-1/2"></div>

                                <!-- Scanning Beam -->
                                <div
                                    class="absolute w-1/2 h-1/2 top-0 left-0 origin-bottom-right bg-gradient-to-tl from-transparent to-red-500/30 animate-[spin_3s_linear_infinite] rounded-tl-full z-10 box-decoration-clone filter blur-[1px]">
                                </div>

                                <!-- Blips -->
                                <div
                                    class="absolute top-16 left-24 w-1.5 h-1.5 bg-red-400 rounded-full animate-ping items-center flex justify-center">
                                    <div class="w-1 h-1 bg-white rounded-full"></div>
                                </div>
                                <div
                                    class="absolute bottom-20 right-28 w-1.5 h-1.5 bg-red-400 rounded-full animate-ping delay-700 items-center flex justify-center">
                                    <div class="w-1 h-1 bg-white rounded-full"></div>
                                </div>

                                <!-- Central Core -->
                                <div
                                    class="absolute w-4 h-4 rounded-full bg-red-500 shadow-[0_0_20px_red] animate-pulse z-20">
                                </div>
                            </div>

                            <div class="text-center z-20">
                                <div
                                    class="inline-flex items-center gap-3 px-6 py-2 bg-red-500/10 border border-red-500/20 rounded-full mb-4">
                                    <div class="w-2 h-2 bg-red-500 rounded-full animate-blink"></div>
                                    <span class="text-xs font-black text-red-500 uppercase tracking-widest">{{ t('ui_scanning_network', 'Escaneando Red...') }}</span>
                                </div>
                                <h3 class="text-6xl font-black text-white tracking-tighter drop-shadow-2xl">
                                    NIVEL 4</h3>
                                <p
                                    class="text-xs font-mono text-emerald-400 mt-2 uppercase tracking-[0.3em] opacity-70">
                                    Nivel Privilegio: ALMIRANTE</p>
                            </div>
                        </div>

                        <!-- CENTER PANEL: METRICS -->
                        <div
                            class="w-[30%] border-r border-white/5 p-10 flex flex-col gap-8 bg-black/20 overflow-y-auto custom-scrollbar">
                            <div class="flex items-center justify-between shrink-0">
                                <h4
                                    class="text-xs font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
                                    <i class="fa-solid fa-chart-pie"></i>
                                    {{ t('ui_threat_analysis_label', 'Análisis de Amenazas') }}
                                </h4>
                                <span class="text-[11px] font-mono text-slate-600">INT: 500ms</span>
                            </div>

                            <!-- Histogram -->
                            <div
                                class="h-40 shrink-0 bg-black/40 rounded-2xl border border-white/5 p-6 flex items-end justify-between gap-1.5 shadow-inner">
                                <div v-for="(h, i) in sentinelHistogram" :key="i"
                                    class="w-full bg-gradient-to-t from-red-900/60 to-red-500/60 hover:to-red-400 transition-all duration-1000 rounded-sm"
                                    :style="{ height: h + '%' }"></div>
                            </div>

                            <div class="grid grid-cols-2 gap-4 shrink-0">
                                <div
                                    class="p-4 bg-white/5 rounded-2xl border border-white/5 flex flex-col items-center justify-center">
                                    <span class="text-xs font-black text-slate-500 uppercase mb-1">{{ t('ui_cpu_load', 'CPU') }}</span>
                                    <span class="text-xl font-black text-white">{{ Math.round(systemStats.cpu?.percent || 0) }}%</span>
                                    <span class="text-[11px] text-slate-600 font-mono">{{ systemStats.cpu?.freq }}
                                        MHz</span>
                                </div>
                                <div
                                    class="p-4 bg-white/5 rounded-2xl border border-white/5 flex flex-col items-center justify-center">
                                    <span class="text-xs font-black text-slate-500 uppercase mb-1">{{ t('ui_ram_usage', 'RAM') }}</span>
                                    <span class="text-xl font-black text-white">{{ systemStats.ram?.percent }}%</span>
                                    <span class="text-[11px] text-slate-600 font-mono">{{ systemStats.ram?.used }} / {{ systemStats.ram?.total }} GB</span>
                                </div>
                                <div
                                    class="p-4 bg-white/5 rounded-2xl border border-white/5 flex flex-col items-center justify-center">
                                    <span class="text-xs font-black text-slate-500 uppercase mb-1">{{ t('ui_disk_free', 'DISCO') }}</span>
                                    <span class="text-xl font-black text-white">{{ systemStats.disk?.percent }}%</span>
                                    <span class="text-[11px] text-slate-600 font-mono">{{ systemStats.disk?.free }} GB
                                        Libres</span>
                                </div>
                                <div
                                    class="p-4 bg-white/5 rounded-2xl border border-white/5 flex flex-col items-center justify-center">
                                    <span class="text-xs font-black text-slate-500 uppercase mb-1">{{ t('ui_network_m', 'RED (M)') }}</span>
                                    <div class="flex flex-col items-center leading-none">
                                        <span class="text-[11px] text-emerald-400 font-bold">↑ {{ systemStats.net?.sent }} MB</span>
                                        <span class="text-[11px] text-cyan-400 font-bold">↓ {{ systemStats.net?.recv }}
                                            MB</span>
                                    </div>
                                </div>
                            </div>

                            <div class="grid grid-cols-1 gap-4 shrink-0">
                                <div
                                    class="p-6 bg-white/5 rounded-2xl border border-white/5 flex items-center justify-between group hover:bg-white/10 transition-colors cursor-pointer">
                                    <div class="flex flex-col">
                                        <span
                                            class="text-3xl font-black text-white group-hover:text-red-400 transition-colors">24</span>
                                        <span class="text-xs font-bold text-slate-500 uppercase tracking-wider">{{ t('ui_ips_blocked_label', 'IPs Bloqueadas') }}</span>
                                    </div>
                                    <i
                                        class="fa-solid fa-ban text-2xl text-slate-700 group-hover:text-red-500/50 transition-colors"></i>
                                </div>
                                <div
                                    class="p-6 bg-white/5 rounded-2xl border border-white/5 flex items-center justify-between group hover:bg-white/10 transition-colors cursor-pointer">
                                    <div class="flex flex-col">
                                        <span class="text-3xl font-black text-emerald-400">0</span>
                                        <span
                                            class="text-xs font-bold text-slate-500 uppercase tracking-wider">Intrusiones
                                            Activas</span>
                                    </div>
                                    <i
                                        class="fa-solid fa-check-circle text-2xl text-slate-700 group-hover:text-emerald-500/50 transition-colors"></i>
                                </div>
                            </div>

                            <div class="mt-auto p-6 bg-yellow-500/5 border border-yellow-500/10 rounded-2xl shrink-0">
                                <div class="flex items-center justify-between mb-3">
                                    <span
                                        class="text-xs font-bold text-yellow-500 uppercase tracking-widest flex items-center gap-2">
                                        <i class="fa-solid fa-triangle-exclamation"></i> {{ t('ui_global_threat_level', 'Nivel de Amenaza Global') }}
                                    </span>
                                    <span class="text-xs font-black text-white bg-yellow-500/20 px-2 py-0.5 rounded">{{ t('ui_threat_level_elevated', 'ELEVADO') }}</span>
                                </div>
                                <div class="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                                    <div
                                        class="h-full w-[35%] bg-gradient-to-r from-yellow-600 to-yellow-400 opacity-80">
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- RIGHT PANEL: LOGS -->
                        <div class="w-[30%] bg-[#020205] flex flex-col font-mono text-xs border-l border-white/5">
                            <div class="h-14 flex items-center px-6 border-b border-white/5 bg-white/5 justify-between">
                                <h4 class="text-[#00ff00] font-bold tracking-wider text-xs">>>
                                    TERMINAL_CENTINELA</h4>
                                <div class="flex gap-1.5">
                                    <div class="w-2.5 h-2.5 rounded-full bg-red-500/20"></div>
                                    <div class="w-2.5 h-2.5 rounded-full bg-yellow-500/20"></div>
                                    <div class="w-2.5 h-2.5 rounded-full bg-green-500/20"></div>
                                </div>
                            </div>
                            <div class="flex-1 overflow-y-auto p-6 space-y-1.5 custom-scrollbar font-medium">
                                <div v-for="(log, i) in sentinelLogs" :key="i"
                                    class="flex gap-3 text-opacity-80 hover:bg-white/5 p-1 rounded -mx-1 px-1 transition-colors">
                                    <span class="text-slate-600 shrink-0 select-none">[{{ log.time }}]</span>
                                    <span
                                        :class="log.msg.includes('BLOCK') || log.msg.includes('FAIL') ? 'text-red-400' : 'text-slate-300'"
                                        class="truncate tracking-tight">{{ log.msg }}</span>
                                </div>
                                <div class="h-4 w-2 bg-[#00ff00] animate-blink mt-2"></div>
                            </div>
                            <div class="p-4 border-t border-white/10 bg-white/5">
                                <div class="flex gap-3 items-center">
                                    <span class="text-emerald-500 font-bold">></span>
                                    <input v-model="sentinelInput" @keyup.enter="handleSentinelCommand" type="text"
                                        :placeholder="t('ui_execute_countermeasure_placeholder', 'Ejecutar contramedida...')"
                                        class="bg-transparent text-white outline-none w-full placeholder-slate-700 text-xs font-bold" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </transition>
            <transition name="fade">
                <div v-if="showCommModal"
                    class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-8"
                    @click.self="showCommModal = false">
                    <div class="relative w-full max-w-lg bg-slate-900 border border-white/10 rounded-[30px] p-8 shadow-2xl flex flex-col gap-6"
                        @click.stop>

                        <!-- Header -->
                        <div class="flex items-center gap-4 border-b border-white/5 pb-4">
                            <div class="w-12 h-12 rounded-full flex items-center justify-center"
                                :class="commMode === 'sms' ? 'bg-green-500/10 text-green-400' : 'bg-blue-500/10 text-blue-400'">
                                <i class="fa-solid"
                                    :class="commMode === 'sms' ? 'fa-comment-dots text-2xl' : 'fa-phone text-2xl'"></i>
                            </div>
                            <div>
                                <h3 class="text-xl font-black text-white uppercase tracking-wider">
                                    {{ commMode === 'sms' ? 'Enviar SMS' : 'Iniciar Llamada' }}
                                </h3>
                                <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                                    Vía {{ linkedMobileDevice ? linkedMobileDevice.name : 'Dispositivo' }}
                                </span>
                            </div>
                        </div>

                        <!-- Warning: No Connection -->
                        <div v-if="!isMessagingAvailable"
                            class="bg-red-500/10 border border-red-500/30 rounded-2xl p-4 flex flex-col items-center text-center gap-2 animate-pulse">
                            <i class="fa-solid fa-triangle-exclamation text-red-400 text-xl"></i>
                            <span class="text-[10px] font-black text-red-300 uppercase tracking-widest leading-tight">
                                {{ t('ui_no_comm_avail', 'No hay servicios de comunicación disponibles.') }}<br>
                                {{ t('ui_connect_phone_hint', 'Conecta un celular o abre el centro web.') }}
                            </span>
                        </div>

                        <!-- Open Unified Center Button (NUEVO) -->
                        <button @click="openMessagingCenter"
                            class="w-full py-4 bg-indigo-500/10 border border-indigo-500/30 rounded-2xl flex items-center justify-center gap-3 hover:bg-indigo-500 transition-all group/center">
                            <i class="fa-solid fa-window-restore text-indigo-400 group-hover:text-white"></i>
                            <span class="text-[10px] font-black text-white uppercase tracking-widest">{{ t('ui_open_unified_center', 'Abrir Centro de Mensajería Unificado') }}</span>
                        </button>

                        <!-- Inputs -->
                        <div class="space-y-4"
                            :class="!isMessagingAvailable ? 'opacity-30 pointer-events-none grayscale' : ''">

                            <!-- App Selector -->
                            <div v-if="commMode === 'sms' && installedMessagingApps.length > 1" class="space-y-2">
                                <label
                                    class="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Enviar
                                    vía</label>
                                <div class="flex gap-2 p-1 bg-black/40 rounded-2xl border border-white/10">
                                    <button v-for="appId in installedMessagingApps" :key="appId"
                                        @click="selectedMessagingApp = appId"
                                        class="flex-1 py-2 rounded-xl border flex items-center justify-center gap-2 transition-all"
                                        :class="selectedMessagingApp === appId
                                            ? 'bg-white/10 border-white/10 text-white shadow-lg'
                                            : 'border-transparent text-slate-600 hover:text-slate-400'">
                                        <i
                                            :class="[SUPPORTED_MESSAGING_APPS[appId].icon, selectedMessagingApp === appId ? SUPPORTED_MESSAGING_APPS[appId].color : '']"></i>
                                        <span class="text-[10px] font-bold uppercase tracking-wider">{{ SUPPORTED_MESSAGING_APPS[appId].name }}</span>
                                    </button>
                                </div>
                            </div>

                            <div class="space-y-2">
                                <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">{{ t('ui_recipient', 'Destinatario') }}</label>
                                <div class="relative">
                                    <i
                                        class="fa-solid fa-address-book absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-xs"></i>
                                    <input type="text" v-model="commTarget" placeholder="Número o Contacto"
                                        class="w-full bg-black/40 border border-white/10 rounded-2xl pl-10 pr-4 py-4 text-sm font-bold text-white outline-none focus:border-cyan-500/50 transition-all placeholder-slate-700 font-mono" />
                                </div>
                            </div>

                            <div v-if="commMode === 'sms'" class="space-y-2">
                                <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">{{ t('ui_message', 'Mensaje') }}</label>
                                <textarea v-model="commBody" rows="4" placeholder="Escribe tu mensaje aquí..."
                                    class="w-full bg-black/40 border border-white/10 rounded-2xl px-5 py-4 text-sm font-medium text-slate-300 outline-none focus:border-cyan-500/50 transition-all placeholder-slate-700 resize-none"></textarea>
                            </div>
                        </div>

                        <!-- Actions -->
                        <div class="grid grid-cols-2 gap-4 mt-2">
                            <button @click="showCommModal = false"
                                class="py-4 rounded-2xl border border-white/10 text-slate-400 text-xs font-black uppercase hover:bg-white/5 transition-all tracking-widest">
                                {{ t('ui_cancel', 'Cancelar') }}
                            </button>
                            <button @click="sendCommAction" :disabled="!isMessagingAvailable"
                                class="py-4 rounded-2xl text-black text-xs font-black uppercase transition-all tracking-widest shadow-lg flex items-center justify-center gap-2 disabled:opacity-20 disabled:grayscale disabled:cursor-not-allowed"
                                :class="commMode === 'sms'
                                    ? 'bg-gradient-to-r from-green-400 to-emerald-500 hover:scale-[1.02] shadow-green-500/20'
                                    : 'bg-gradient-to-r from-blue-400 to-indigo-500 hover:scale-[1.02] shadow-blue-500/20'">
                                <i class="fa-solid" :class="commMode === 'sms' ? 'fa-paper-plane' : 'fa-phone'"></i>
                                {{ commMode === 'sms' ? t('ui_send_message_btn', 'Enviar Mensaje') : t('ui_call_btn', 'Llamar') }}
                            </button>
                        </div>

                    </div>
                </div>
            </transition>

            <!-- ANDROID 14+ PAIRING MODAL -->
            <transition name="fade">
                <div v-if="showPairingModal"
                    class="fixed inset-0 z-[70] flex items-center justify-center bg-black/90 backdrop-blur-md p-8"
                    @click.self="showPairingModal = false">
                    <div class="w-full max-w-md bg-[#0a0a15] border border-purple-500/30 rounded-[40px] p-10 shadow-[0_0_50px_rgba(168,85,247,0.2)] flex flex-col gap-6 relative overflow-hidden"
                        @click.stop>

                        <!-- Background Glow -->
                        <div class="absolute -top-24 -right-24 w-48 h-48 bg-purple-500/10 blur-[80px] rounded-full">
                        </div>
                        <div class="absolute -bottom-24 -left-24 w-48 h-48 bg-pink-500/10 blur-[80px] rounded-full">
                        </div>

                        <!-- Header -->
                        <div class="flex flex-col items-center text-center gap-4 relative z-10">
                            <div
                                class="w-20 h-20 bg-purple-500/10 border border-purple-500/20 rounded-full flex items-center justify-center shadow-inner">
                                <i class="fa-solid fa-qrcode text-4xl text-purple-400 animate-pulse"></i>
                            </div>
                            <h2 class="text-2xl font-black text-white uppercase tracking-tighter">
                                {{ t('ui_pair_android', 'Emparejar Android') }} {{ detectedAndroidVersion }}+
                            </h2>
                            <p class="text-slate-400 text-xs font-medium px-4">
                                {{ t('ui_android_pairing_desc', 'En tu celular, ve a Ajutes > Opciones de desarrollador...') }}
                            </p>
                        </div>

                        <!-- QR Code Display -->
                        <div class="flex flex-col items-center gap-4 relative z-10">
                            <div v-if="qrCodeDataURL" class="bg-white p-4 rounded-3xl shadow-2xl">
                                <img :src="qrCodeDataURL" alt="QR Code" class="w-64 h-64">
                            </div>
                            <div v-else
                                class="w-64 h-64 bg-white/5 rounded-3xl flex items-center justify-center border border-white/10">
                                <i class="fa-solid fa-spinner fa-spin text-4xl text-purple-400"></i>
                            </div>

                            <!-- Connection Info -->
                            <div class="bg-white/5 rounded-2xl p-4 w-full border border-white/10">
                                <div class="text-center space-y-1">
                                    <p class="text-xs text-slate-500 uppercase tracking-wider font-bold">Información de
                                        Conexión</p>
                                    <p class="text-sm text-white font-mono">{{ pairingIP }}:{{ pairingPort }}</p>
                                    <p class="text-2xl text-cyan-400 font-black tracking-widest">{{ pairingCode }}</p>
                                </div>
                            </div>
                        </div>

                        <!-- Actions -->
                        <div class="flex flex-col gap-3 relative z-10">
                            <button @click="showPairingModal = false; retryMobileConnection()"
                                class="w-full py-4 bg-purple-500 text-white font-black rounded-2xl hover:bg-purple-400 transition-all uppercase tracking-widest text-xs">
                                YA ESCANEÉ EL QR - CONECTAR
                            </button>
                            <button @click="showPairingModal = false"
                                class="w-full py-3 bg-white/5 text-slate-400 font-bold rounded-2xl hover:bg-white/10 transition-all uppercase tracking-widest text-xs border border-white/10">
                                {{ t('ui_cancel', 'Cancelar') }}
                            </button>
                        </div>
                    </div>
                </div>
            </transition>

            <!-- MOBILE HELP MODAL (INSTRUCCIONES CLARAS) -->
            <transition name="fade">
                <div v-if="showMobileHelpModal"
                    class="fixed inset-0 z-[60] flex items-center justify-center bg-black/90 backdrop-blur-md p-8"
                    @click.self="showMobileHelpModal = false">
                    <div class="w-full max-w-lg bg-[#0a0a15] border border-cyan-500/30 rounded-[40px] p-10 shadow-[0_0_50px_rgba(6,182,212,0.2)] flex flex-col gap-8 relative overflow-hidden"
                        @click.stop>

                        <!-- Background Glow -->
                        <div class="absolute -top-24 -right-24 w-48 h-48 bg-cyan-500/10 blur-[80px] rounded-full"></div>
                        <div class="absolute -bottom-24 -left-24 w-48 h-48 bg-blue-500/10 blur-[80px] rounded-full">
                        </div>

                        <!-- Header -->
                        <div class="flex flex-col items-center text-center gap-4 relative z-10">
                            <div
                                class="w-20 h-20 bg-cyan-500/10 border border-cyan-500/20 rounded-full flex items-center justify-center shadow-inner">
                                <i class="fa-solid fa-mobile-screen-button text-4xl text-cyan-400 animate-pulse"></i>
                            </div>
                            <h2 class="text-2xl font-black text-white uppercase tracking-tighter">
                                {{ mobileHelpTitle }}
                            </h2>
                            <p class="text-slate-400 text-sm font-medium px-4">
                                {{ mobileHelpDescription }}
                            </p>
                        </div>

                        <!-- Step by Step (Easy) -->
                        <div class="space-y-4 relative z-10">
                            <div v-if="mobileHelpContext === 'offline'"
                                class="flex gap-4 items-start bg-white/5 p-4 rounded-3xl border border-white/5">
                                <span
                                    class="w-8 h-8 shrink-0 bg-cyan-500 text-black font-black flex items-center justify-center rounded-xl text-xs">1</span>
                                <div class="flex flex-col">
                                    <span class="text-sm font-bold text-white">{{ t('ui_physical_connection', 'Conexión Física') }}</span>
                                    <span class="text-xs text-slate-500">{{ t('ui_usb_conn_desc', 'Conecta tu celular a la PC usando un cable USB de buena calidad.') }}</span>
                                </div>
                            </div>
                            <div v-if="mobileHelpContext === 'offline'"
                                class="flex gap-4 items-start bg-white/5 p-4 rounded-3xl border border-white/5">
                                <span
                                    class="w-8 h-8 shrink-0 bg-cyan-500 text-black font-black flex items-center justify-center rounded-xl text-xs">2</span>
                                <div class="flex flex-col">
                                    <span class="text-sm font-bold text-white">{{ t('ui_unlock_auth', 'Desbloquear y Autorizar') }}</span>
                                    <span class="text-xs text-slate-500">{{ t('ui_usb_auth_desc', 'Mira la pantalla de tu celular. Si aparece "Permitir depuración USB", selecciona "Permitir siempre" y dale a Aceptar.') }}</span>
                                </div>
                            </div>
                            <div v-if="mobileHelpContext === 'missing'"
                                class="flex gap-4 items-start bg-white/5 p-4 rounded-3xl border border-white/5">
                                <span
                                    class="w-8 h-8 shrink-0 bg-blue-500 text-white font-black flex items-center justify-center rounded-xl text-xs">A</span>
                                <div class="flex flex-col">
                                    <span class="text-sm font-bold text-white">{{ t('ui_config', 'Configuración') }}</span>
                                    <span class="text-xs text-slate-500">{{ t('ui_mobile_config_desc', 'Ve a Ajustes > Plugins y busca el ícono de Celular para añadir un nuevo dispositivo.') }}</span>
                                </div>
                            </div>
                        </div>

                        <!-- Actions -->
                        <div class="flex flex-col gap-3 relative z-10">
                            <button
                                @click="showMobileHelpModal = false; mobileHelpContext === 'offline' && retryMobileConnection()"
                                class="w-full py-4 bg-cyan-500 text-black font-black rounded-2xl hover:bg-cyan-400 transition-all uppercase tracking-widest text-xs">
                                {{ mobileHelpContext === 'offline' ? t('ui_understood_v_conn', 'ENTENDIDO - VERIFICAR CONEXIÓN') : t('ui_understood', 'ENTENDIDO') }}
                            </button>
                            <button v-if="mobileHelpContext === 'missing'"
                                @click="activeTab = 'ajustes'; activeSettingsDomain = 'inteligencia'; activeSettingsTab = 'plugins'; showMobileHelpModal = false; showCommModal = false"
                                class="w-full py-4 bg-white/5 text-white font-bold rounded-2xl hover:bg-white/10 transition-all uppercase tracking-widest text-xs border border-white/10">
                                {{ t('ui_go_to_settings', 'IR A CONFIGURACIÓN') }}
                            </button>
                        </div>
                    </div>
                </div>
            </transition>

            <!-- OPT-IN MODAL FOR NEW APPS -->
            <transition name="fade">
                <div v-if="showOptInModal"
                    class="fixed inset-0 z-[70] flex items-center justify-center bg-black/90 backdrop-blur-md p-8">
                    <div class="w-full max-w-lg bg-[#0a0f1e] border border-cyan-500/30 rounded-[40px] p-10 shadow-2xl relative overflow-hidden flex flex-col gap-6"
                        @click.stop>

                        <!-- Background Glow -->
                        <div class="absolute -top-20 -right-20 w-40 h-40 bg-purple-500/10 blur-[60px] rounded-full">
                        </div>
                        <div class="absolute -bottom-20 -left-20 w-40 h-40 bg-cyan-500/10 blur-[60px] rounded-full">
                        </div>

                        <!-- Header -->
                        <div class="flex items-center gap-4 z-10">
                            <div
                                class="w-12 h-12 bg-cyan-500/10 border border-cyan-500/20 rounded-full flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.2)]">
                                <i class="fa-solid fa-link text-xl"></i>
                            </div>
                            <div>
                                <h2 class="text-xl font-black text-white uppercase tracking-wider">{{ t('ui_link_apps_title', 'Vincular Apps') }}</h2>
                                <p class="text-[10px] text-slate-400 font-bold uppercase tracking-widest mt-1">
                                    {{ t('ui_apps_query', '¿Qué apps quieres usar con Fina?') }}
                                </p>
                            </div>
                        </div>

                        <!-- App List -->
                        <div class="flex flex-col gap-3 z-10">
                            <div v-for="appId in newDetectedApps" :key="appId"
                                class="flex items-center justify-between p-4 rounded-2xl border transition-all cursor-pointer group"
                                :class="selectedAppsToLink.includes(appId) ? 'bg-cyan-900/20 border-cyan-500/50' : 'bg-white/5 border-white/5 hover:bg-white/10'"
                                @click="toggleAppSelection(appId)">
                                <div class="flex items-center gap-3">
                                    <div
                                        class="w-10 h-10 rounded-xl bg-black/30 flex items-center justify-center border border-white/5">
                                        <i :class="SUPPORTED_MESSAGING_APPS[appId].icon + ' ' + SUPPORTED_MESSAGING_APPS[appId].color"
                                            class="text-xl"></i>
                                    </div>
                                    <span class="text-sm font-black text-white uppercase tracking-wide">{{ SUPPORTED_MESSAGING_APPS[appId].name }}</span>
                                </div>
                                <span
                                    class="text-[9px] font-black px-2 py-1 rounded border uppercase tracking-widest transition-colors"
                                    :class="selectedAppsToLink.includes(appId) ? 'text-cyan-400 bg-cyan-500/20 border-cyan-500/30' : 'text-slate-400 bg-white/5 border-white/10 group-hover:text-cyan-200'">
                                    {{ selectedAppsToLink.includes(appId) ? t('ui_app_selected', 'SELECCIONADA') : t('ui_app_link', 'VINCULAR') }}
                                </span>
                            </div>
                        </div>

                        <!-- Info Text -->
                        <div class="p-4 bg-cyan-900/10 border border-cyan-500/20 rounded-2xl z-10">
                            <p class="text-[10px] text-cyan-200 font-medium leading-relaxed">
                                {{ t('ui_apps_link_desc', 'Al vincular estas aplicaciones, permitirás que Fina te ayude a leer y redactar mensajes. Tienes el control total.') }}
                            </p>
                        </div>

                        <!-- Buttons -->
                        <div class="flex gap-3 z-10 mt-2">
                            <button @click="showOptInModal = false"
                                class="flex-1 py-3 rounded-xl border border-white/10 text-slate-400 font-bold uppercase tracking-wider hover:bg-white/5 hover:text-white transition-colors text-[10px]">
                                {{ t('ui_no_ignore_btn', 'NO, IGNORAR') }}
                            </button>
                            <button @click="confirmLinkApps"
                                class="flex-1 py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-black uppercase tracking-wider hover:from-cyan-500 hover:to-blue-500 shadow-lg shadow-cyan-900/20 transition-all text-[10px]">
                                {{ t('ui_yes_link_btn', 'SÍ, VINCULAR') }}
                            </button>
                        </div>
                    </div>
                </div>
            </transition>

            <!-- FINA MARKET MODAL (INNER SYSTEM) -->
            <transition name="fade">
                <div v-if="showMarket"
                    class="fixed inset-0 z-[80] flex items-center justify-center bg-black/95 backdrop-blur-xl p-6"
                    @click.self="showMarket = false">
                    <div class="w-full max-w-6xl h-[85vh] bg-[#050a14] border border-cyan-500/20 rounded-[50px] shadow-3xl relative overflow-hidden flex flex-col"
                        @click.stop>

                        <!-- Header -->
                        <div class="p-10 border-b border-white/5 flex items-center justify-between shrink-0">
                            <div class="flex items-center gap-6">
                                <div
                                    class="w-16 h-16 bg-cyan-500/10 rounded-full flex items-center justify-center border border-cyan-500/20">
                                    <i class="fa-solid fa-puzzle-piece text-3xl text-cyan-400"></i>
                                </div>
                                <div>
                                    <h1 class="text-3xl font-black text-white uppercase tracking-tighter">Fina Market
                                    </h1>
                                    <p class="text-xs text-slate-500 font-bold uppercase tracking-[0.3em] mt-1">
                                        {{ t('ui_modular_addons_ecosystem', 'Ecosistema de Complementos Modulares') }}
                                    </p>
                                </div>
                            </div>
                            <button @click="showMarket = false"
                                class="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center hover:bg-red-500/20 hover:text-red-400 transition-all">
                                <i class="fa-solid fa-xmark text-xl"></i>
                            </button>
                        </div>

                        <!-- Content wrapper -->
                        <div class="flex-1 overflow-y-auto p-10 custom-scrollbar">

                            <!-- Loading State -->
                            <div v-if="isMarketLoading"
                                class="w-full h-full flex flex-col items-center justify-center gap-6">
                                <div class="relative w-24 h-24">
                                    <div class="absolute inset-0 border-4 border-cyan-500/20 rounded-full"></div>
                                    <div
                                        class="absolute inset-0 border-4 border-cyan-400 rounded-full border-t-transparent animate-spin">
                                    </div>
                                </div>
                                <p class="text-cyan-400 font-black uppercase tracking-widest animate-pulse">
                                    {{ t('ui_syncing_market', 'Sincronizando con Repositorio Central...') }}</p>
                            </div>

                            <!-- Plugin Grid -->
                            <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                <div v-for="plugin in marketPlugins" :key="plugin.path"
                                    class="bg-white/5 border border-white/10 rounded-[35px] p-8 flex flex-col gap-6 hover:border-cyan-500/40 hover:bg-white/[0.07] transition-all group">

                                    <div class="flex items-start justify-between">
                                        <div
                                            class="w-14 h-14 bg-black/40 rounded-2xl flex items-center justify-center border border-white/5">
                                            <i class="fa-solid text-2xl text-cyan-400" :class="{
                                                'fa-tv': plugin.category === 'TVs',
                                                'fa-box': plugin.category === 'Decos',
                                                'fa-bell': plugin.category === 'Doorbells',
                                                'fa-wind': plugin.category === 'AirConditioning'
                                            }"></i>
                                        </div>
                                        <span
                                            class="px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-[10px] font-black text-cyan-400 uppercase tracking-widest">{{ plugin.category }}</span>
                                    </div>

                                    <div>
                                        <h3 class="text-xl font-black text-white uppercase tracking-tight">{{ plugin.name }}</h3>
                                        <p class="text-xs text-slate-500 font-bold mt-1">{{ plugin.brand }}</p>
                                    </div>

                                    <div class="mt-auto pt-4 flex gap-3">
                                        <button @click="installMarketPlugin(plugin)"
                                            class="flex-1 py-4 bg-cyan-500 text-black font-black rounded-2xl hover:bg-cyan-400 transition-all uppercase tracking-widest text-[10px] flex items-center justify-center gap-2">
                                            <i class="fa-solid fa-download"></i>
                                            {{ t('ui_install_plugin', 'INSTALAR PODER') }}
                                        </button>
                                        <a :href="'https://github.com/dankopetro/Fina-Plugins-Market/tree/main/' + plugin.category + '/' + plugin.path"
                                            target="_blank"
                                            class="w-14 py-4 bg-white/5 border border-white/10 text-white rounded-2xl hover:bg-white/10 transition-all flex items-center justify-center">
                                            <i class="fa-brands fa-github"></i>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Footer Info -->
                        <div class="p-6 bg-black/40 border-t border-white/5 text-center shrink-0">
                            <p class="text-[10px] text-slate-600 font-bold uppercase tracking-[0.2em]">{{ t('ui_plugin_install_hint', 'Los plugins se instalan automáticamente en la carpeta de ejecución local.') }}</p>
                        </div>
                    </div>
                </div>
            </transition>
            <!-- UNIVERSAL PIN MODAL -->
            <transition name="fade">
                <div v-if="showUniversalPinModal"
                    class="fixed inset-0 z-[100] flex items-center justify-center bg-black/95 backdrop-blur-xl p-6"
                    @click.self="showUniversalPinModal = false">
                    <div class="w-full max-w-md bg-[#070a14] border border-cyan-500/30 rounded-[40px] p-10 shadow-3xl text-center flex flex-col gap-8 relative overflow-hidden"
                        @click.stop>
                        <div class="absolute -top-20 -left-20 w-40 h-40 bg-cyan-500/10 blur-[60px] rounded-full"></div>
                        <div class="z-10 flex flex-col items-center gap-6">
                            <div class="w-20 h-20 bg-cyan-500/10 border border-cyan-500/20 rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(6,182,212,0.2)]">
                                <i class="fa-solid fa-key-skeleton text-4xl text-cyan-400"></i>
                            </div>
                            <div>
                                <h3 class="text-2xl font-black text-white uppercase tracking-tighter">{{ universalPinData.title }}</h3>
                                <p class="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">{{ universalPinData.device }}</p>
                            </div>
                            <div class="w-full space-y-4">
                                <label class="text-[10px] font-black text-cyan-400/50 uppercase tracking-[0.3em]">Ingresa los 6 dígitos</label>
                                <input v-model="universalPinInput" type="text" maxlength="6"
                                    placeholder="000000"
                                    @keyup.enter="submitUniversalPin"
                                    class="w-full bg-white/5 border border-white/10 rounded-3xl px-6 py-6 text-4xl font-black text-white text-center tracking-[0.5em] focus:border-cyan-500 transition-all placeholder:opacity-20 outline-none" />
                            </div>
                            <p class="text-[9px] text-slate-600 font-bold leading-relaxed uppercase tracking-wider">
                                Este código aparece en la pantalla de tu dispositivo para asegurar una conexión privada y segura.
                            </p>
                        </div>
                        <div class="z-10 flex gap-3">
                            <button @click="showUniversalPinModal = false"
                                class="flex-1 py-4 border border-white/10 rounded-2xl text-slate-400 font-bold text-[10px] hover:bg-white/5 hover:text-white transition-all uppercase tracking-widest">
                                Cancelar
                            </button>
                            <button @click="submitUniversalPin" :disabled="universalPinInput.length !== 6"
                                class="flex-2 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 text-white font-black rounded-2xl text-[10px] uppercase tracking-widest hover:scale-[1.02] active:scale-95 transition-all shadow-lg shadow-cyan-900/40 disabled:opacity-20">
                                Confirmar y Conectar
                            </button>
                        </div>
                    </div>
                </div>
            </transition>
        </main>
    </div>
</template>

<style scoped>
.no-drag {
    -webkit-app-region: no-drag;
}

[data-tauri-drag-region] {
    -webkit-app-region: drag;
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

@keyframes halo-anim {
    0% {
        transform: scale(0.92);
        opacity: 0.3;
    }

    50% {
        transform: scale(1.08);
        opacity: 0.6;
    }

    100% {
        transform: scale(0.92);
        opacity: 0.3;
    }
}

.animate-halo-1 {
    animation: halo-anim 4s ease-in-out infinite;
}

.animate-halo-2 {
    animation: halo-anim 4s ease-in-out infinite 0.7s;
}

.animate-halo-3 {
    animation: halo-anim 4s ease-in-out infinite 1.4s;
}

@keyframes bar-scale-anim {
    0% {
        transform: scaleY(0.15);
        opacity: 0.5;
    }

    100% {
        transform: scaleY(1.0);
        opacity: 1;
        box-shadow: 0 0 12px cyan;
    }
}

.bar-anim-1 {
    animation: bar-scale-anim 0.2s ease-in-out infinite alternate;
}

.bar-anim-2 {
    animation: bar-scale-anim 0.25s ease-in-out infinite alternate-reverse;
}

.bar-anim-3 {
    animation: bar-scale-anim 0.3s ease-in-out infinite alternate 0.1s;
}

.bar-anim-4 {
    animation: bar-scale-anim 0.22s ease-in-out infinite alternate-reverse 0.05s;
}

/* Chat History List Transition */
.list-enter-active,
.list-leave-active {
    transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.list-enter-from,
.list-leave-to {
    opacity: 0;
    transform: translateX(50px) scale(0.9);
}

.list-move {
    transition: transform 0.4s ease;
}
</style>