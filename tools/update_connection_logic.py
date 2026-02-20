
import re

file_path = './src/App.vue'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Patrón para encontrar la función retryMobileConnection completa
# Buscamos desde la declaración hasta antes de la siguiente función (const playAudio = ... o lo que siga)
# O simplemente, buscamos el bloque y lo reemplazamos con cuidado.

# Mejor estrategia: Encontrar la función y reemplazar su cuerpo.
start_marker = "const retryMobileConnection = async () => {"
end_marker = "};" # Esto es arriesgado porque hay muchos };

# Vamos a buscar el inicio y contar llaves para encontrar el final
start_idx = content.find(start_marker)
if start_idx == -1:
    print("Error: No se encontró la función")
    exit(1)

# Encontrar el final balanceando llaves
brace_count = 0
i = start_idx + len(start_marker)
found_start = False
end_idx = -1

# Ajustar i para empezar después del { de la declaración
# Ya sumamos len(start_marker) que incluye el { final
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

# Nuevo contenido de la función
new_function_body = """const retryMobileConnection = async () => {
    const dev = linkedMobileDevice.value;
    if (!dev || !dev.ip) {
        finaState.value.process = "NO HAY DISPOSITIVO CONFIGURADO";
        return;
    }

    finaState.value.process = `REINTENTANDO CONEXIÓN ${dev.name.toUpperCase()}...`;

    try {
        // 1. Verificar si hay algún dispositivo conectado por USB
        const devicesOut = await invoke("execute_shell_command", { command: "timeout 3 adb devices" });
        console.log("📱 Dispositivos ADB:", devicesOut);
        
        // Buscar dispositivos USB (excluir la línea de encabezado y dispositivos IP)
        let usbDeviceId = null;
        let deviceStatus = null;
        
        const lines = devicesOut.split('\\n');
        for (const line of lines) {
            // Saltar líneas vacías y el encabezado
            if (!line.trim() || line.includes('List of devices')) continue;
            
            // Excluir IPs (contiene . o :)
            if (line.includes('.') || line.includes(':')) continue;
            
            // Regex relajado para capturar cualquier ID de dispositivo que no sea espacio en blanco
            const match = line.match(/^([^\\s]+)\\s+(device|unauthorized)/);
            if (match) {
                usbDeviceId = match[1];
                deviceStatus = match[2];
                break;
            }
        }
        
        if (!usbDeviceId) {
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
            
            // Esperar hasta 15 segundos a que autorice
            let authorized = false;
            for (let i = 0; i < 15; i++) {
                await new Promise(resolve => setTimeout(resolve, 1000));
                const checkDevices = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
                if (checkDevices.includes(`${usbDeviceId}\\tdevice`) || checkDevices.includes(`${usbDeviceId} device`)) {
                    authorized = true;
                    break;
                }
            }
            
            if (!authorized) {
                throw new Error("No se autorizó la depuración USB");
            }
        }
        
        // 3. Detectar versión (informativo y para QR si falla tcpip)
        const androidVersion = await detectAndroidVersion();
        
        // 4. HABILITAR TCPIP 5555 PARA TODOS (Android 13 y 14)
        // Esto asegura que podemos conectar a la IP en el puerto 5555 estándar
        finaState.value.process = "CONFIGURANDO MODO INALÁMBRICO...";
        await invoke("execute_shell_command", { command: `timeout 4 adb -s ${usbDeviceId} tcpip 5555` }).catch(() => { });
        await new Promise(resolve => setTimeout(resolve, 2000)); // Esperar reinicio de adbd
        
        // 5. Intentar conectar (a la IP configurada en Fina)
        finaState.value.process = `CONECTANDO A ${dev.ip}...`;
        await invoke("execute_shell_command", { command: `timeout 4 adb connect ${dev.ip}:5555` }).catch(() => { });
        
        // 6. Verificar estado final
        const finalDevicesCheck = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
        const isListed = finalDevicesCheck.includes(dev.ip);
        const isOffline = finalDevicesCheck.includes("offline") || finalDevicesCheck.includes("unauthorized");
        
        if (isListed && !isOffline) {
            // ÉXITO - Conectado
            finaState.value.process = `${dev.name.toUpperCase()} CONECTADO`;
            const hint = `Perfecto, ${dev.name} está conectado y listo. Puedes desconectar el cable USB ahora.`;
            invoke("execute_shell_command", {
                command: `python3 ./utils.py speak "${hint}"`
            }).catch(() => { });

            addChatMessage(`${dev.name} conectado correctamente. Ya puedes desconectar el cable USB.`);
            
            // Cerrar modales y volver
            showPairingModal.value = false;
            showMobileHelpModal.value = false;
            
            setTimeout(() => {
                showCommModal.value = true;
                if (finaState.value.process.includes("CONECTADO")) finaState.value.process = 'SISTEMA LISTO';
            }, 2000);
            return; // Salir, éxito total
        }

        // Si llegamos aquí, adb tcpip falló o no conectó.
        // Solo para Android 14+: Intentar flujo QR como último recurso
        if (androidVersion >= 14) {
             const wirelessCheck = await invoke("execute_shell_command", { command: "timeout 2 adb devices" });
             if (!wirelessCheck.includes(dev.ip)) {
                // Necesita emparejamiento - Generar QR automáticamente
                await generatePairingQR();
                showPairingModal.value = true;
                const hint = `${dev.name} usa Android ${androidVersion}. La conexión automática falló. Escanea el código QR para intentar el método alternativo.`;
                invoke("execute_shell_command", {
                    command: `python3 ./utils.py speak "${hint}"`
                }).catch(() => { });
                return;
            }
        }
        
        throw new Error("No se pudo establecer conexión inalámbrica");

    } catch (e) {
        console.error("Error conexión:", e);
        finaState.value.process = `${dev.name.toUpperCase()} AÚN DESCONECTADO`;
        const hint = `Todavía no puedo detectar ${dev.name}. Asegúrate de haber aceptado la autorización en la pantalla del celular.`;
        invoke("execute_shell_command", {
            command: `python3 ./utils.py speak "${hint}"`
        }).catch(() => { });

        setTimeout(() => {
            if (finaState.value.process.includes("DESCONECTADO")) finaState.value.process = 'SISTEMA LISTO';
        }, 5000);
    }
};"""

# Reemplazar el bloque antiguo con el nuevo
final_content = content[:start_idx] + new_function_body + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

print("✅ Función retryMobileConnection actualizada correctamente.")
