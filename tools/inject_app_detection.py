
import re

file_path = './src/App.vue'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Definir la función detectMessagingApps
detect_func_code = """
// --- APP DETECTION ---
const detectMessagingApps = async () => {
    try {
        console.log("🕵️ Escaneando apps de mensajería...");
        const output = await invoke("execute_shell_command", { command: "timeout 5 adb shell pm list packages" });
        
        const detected = [];
        // Revisar cada app soportada
        Object.values(SUPPORTED_MESSAGING_APPS).forEach(app => {
            if (app.id === 'sms') { // SMS siempre está
                detected.push('sms');
                return;
            }
            if (output.includes(`package:${app.package}`)) {
                detected.push(app.id);
            }
        });
        
        installedMessagingApps.value = detected;
        console.log("✅ Apps detectadas:", detected);
    } catch (e) {
        console.warn("Error detectando apps:", e);
        installedMessagingApps.value = ['sms'];
    }
};

"""

# 2. Insertar antes de retryMobileConnection si no existe ya
if "const detectMessagingApps" not in content:
    content = content.replace("const retryMobileConnection", detect_func_code + "const retryMobileConnection")

# 3. Agregar llamada a detectMessagingApps() en retryMobileConnection (versión inteligente actual)
# Buscamos el punto de éxito: "finaState.value.process = `${dev.name.toUpperCase()} CONECTADO`;"
# Ojo, en la versión "smart" tenemos "RECONECTADO" y "CONECTADO".

success_patterns = [
    'finaState.value.process = `${dev.name.toUpperCase()} CONECTADO`;',
    'finaState.value.process = `${dev.name.toUpperCase()} RECONECTADO`;'
]

for pattern in success_patterns:
    if pattern in content:
        # Insertar la llamada después de la línea de éxito
        replacement = pattern + "\n            detectMessagingApps(); // Detectar apps al conectar"
        content = content.replace(pattern, replacement)

# 4. También agregar en onMounted cuando se hace la reconexión automática
# Buscamos: finaState.value.process = "MÓVIL ONLINE";
# Y agregamos la llamada.
if 'finaState.value.process = "MÓVIL ONLINE";' in content:
    content = content.replace('finaState.value.process = "MÓVIL ONLINE";', 'finaState.value.process = "MÓVIL ONLINE";\n                    detectMessagingApps();')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Función detectMessagingApps insertada y conectada.")
