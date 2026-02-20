
import re

file_path = './src/App.vue'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón para encontrar la función retryMobileConnection completa
start_marker = "const retryMobileConnection = async () => {"

start_idx = content.find(start_marker)
if start_idx == -1:
    print("Error: No se encontró la función")
    exit(1)

# Encontrar el final balanceando llaves
brace_count = 0
i = start_idx + len(start_marker)
found_start = False
end_idx = -1

brace_count = 1 

while i < len(content):
    if content[i] == '{':
        brace_count += 1
    elif content[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            end_idx = i + 1
            break
    i += 1

if end_idx == -1:
    print("Error: No se pudo determinar el final de la función")
    exit(1)

# Nuevo contenido de la función MEJORADO
new_function_body = """const retryMobileConnection = async () => {
    const dev = linkedMobileDevice.value;
    if (!dev || !dev.ip) {
        finaState.value.process = "NO HAY DISPOSITIVO CONFIGURADO";
        return;
    }

    finaState.value.process = `BUSCANDO ${dev.name.toUpperCase()}...`;

    // 0. INTENTO DE RECONEXIÓN INALÁMBRICA RÁPIDA (ANTES DE PEDIR CABLE)
    try {
        console.log(`Intentando reconexión inalámbrica a ${dev.ip}...`);
        await invoke("execute_shell_command", { command: `timeout 3 adb connect ${dev.ip}:5555` }).catch(() => {});
        
        // Verificar si revivió
        const quickCheck = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
        if (quickCheck.includes(dev.ip) && !quickCheck.includes("offline")) {
            finaState.value.process = `${dev.name.toUpperCase()} RECONECTADO`;
            addChatMessage(`${dev.name} reconectado inalámbricamente con éxito.`);
            
            showPairingModal.value = false;
            showMobileHelpModal.value = false;
            
            setTimeout(() => {
                showCommModal.value = true;
                if (finaState.value.process.includes("CONECTADO") || finaState.value.process.includes("RECONECTADO")) 
                    finaState.value.process = 'SISTEMA LISTO';
            }, 1500);
            return; // ¡ÉXITO SIN CABLE!
        }
    } catch (e) {
        console.log("Reconexión rápida falló, procediendo a flujo USB/QR...");
    }

    // SI LLEGAMOS ACÁ, FALLÓ LA RECONEXIÓN AUTOMÁTICA -> PEDIMOS CABLE
    finaState.value.process = "SOLICITANDO CONEXIÓN USB...";
    
    try {
        // 1. Verificar si hay algún dispositivo conectado por USB
        const devicesOut = await invoke("execute_shell_command", { command: "timeout 3 adb devices" });
        console.log("📱 Dispositivos ADB:", devicesOut);
        
        let usbDeviceId = null;
        let deviceStatus = null;
        
        const lines = devicesOut.split('\\n');
        for (const line of lines) {
            if (!line.trim() || line.includes('List of devices')) continue;
            if (line.includes('.') || line.includes(':')) continue; // Excluir IPs
            
            const match = line.match(/^([^\\s]+)\\s+(device|unauthorized)/);
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
            finaState.value.process = "ESPERANDO AUTORIZACIÓN EN EL CELULAR...";
            const hint = "Por favor, acepta la autorización de depuración USB en la pantalla de tu celular.";
            invoke("execute_shell_command", { 
                command: `python3 ./utils.py speak "${hint}"` 
            }).catch(() => { });
            
            let authorized = false;
            for (let i = 0; i < 15; i++) {
                await new Promise(resolve => setTimeout(resolve, 1000));
                const checkDevices = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
                if (checkDevices.includes(`${usbDeviceId}\\tdevice`) || checkDevices.includes(`${usbDeviceId} device`)) {
                    authorized = true;
                    break;
                }
            }
            if (!authorized) throw new Error("No se autorizó la depuración USB");
        }
        
        // 3. Detectar versión (informativo)
        const androidVersion = await detectAndroidVersion();
        
        // 4. MODO ROBUSTO: Activar tcpip 5555
        finaState.value.process = "CONFIGURANDO MODO INALÁMBRICO...";
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
            const hint = `Conexión restablecida. Ya puedes desconectar el cable USB.`;
            invoke("execute_shell_command", {
                command: `python3 ./utils.py speak "${hint}"`
            }).catch(() => { });

            addChatMessage(`Conexión con ${dev.name} restablecida. Puedes quitar el cable.`);
            
            showPairingModal.value = false;
            showMobileHelpModal.value = false;
            
            setTimeout(() => {
                showCommModal.value = true;
                if (finaState.value.process.includes("CONECTADO")) finaState.value.process = 'SISTEMA LISTO';
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
                    command: `python3 ./utils.py speak "${hint}"`
                }).catch(() => { });
                return;
            }
        }
        
        throw new Error("No se pudo establecer conexión inalámbrica");

    } catch (e) {
        console.error("Error conexión:", e);
        // Solo mostrar error si falló también la conexión USB
        if (e.message.includes("No hay dispositivo USB conectado")) {
             finaState.value.process = "ESPERANDO CONEXIÓN USB...";
             // No hacemos nada, el usuario verá el modal pidiendo el cable
        } else {
             finaState.value.process = "ERROR DE CONEXIÓN";
        }
    }
};"""

final_content = content[:start_idx] + new_function_body + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("✅ Función retryMobileConnection actualizada con reconexión inteligente.")
