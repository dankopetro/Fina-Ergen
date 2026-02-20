import frida
import sys
import subprocess

PACKAGE_NAME = "com.tuya.smart"

def on_message(message, data):
    if message['type'] == 'send':
        print(f"[*] {message['payload']}")
    else:
        print(message)

jscode = """
Java.perform(function () {
    console.log("🚀 Inyectado en: " + Java.androidVersion);
    
    // Buscar clases interesantes de Tuya
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.includes("Tuya") || className.includes("Encrypt")) {
                console.log("🔎 Clase detectada: " + className);
            }
        },
        onComplete: function() {
            console.log("✅ Escaneo de clases completado.");
        }
    });

    // Intentar hookear SSL (donde viajan las llaves)
    var SSLContext = Java.use("javax.net.ssl.SSLContext");
    SSLContext.init.overload("[Ljavax.net.ssl.KeyManager;", "[Ljavax.net.ssl.TrustManager;", "java.security.SecureRandom").implementation = function(a, b, c) {
        console.log("🔐 SSLContext.init() llamado! Posible handshake.");
        return this.init(a, b, c);
    };
});
"""

print(f"👻 Esperando al proceso {PACKAGE_NAME}...")

try:
    # Volvemos a USB (Versiones sincronizadas)
    print("🔌 Conectando via USB (ADB)...")
    device = frida.get_usb_device()
    
    print(f"🔍 Buscando PID real via ADB...")
    
    # Obtener PID crudo desde Android
    out = subprocess.check_output(["adb", "shell", "ps -A | grep com.tuya.smart"], text=True)
    target_pid = None
        
    for line in out.strip().split('\n'):
        parts = line.split()
        if len(parts) > 8:
            proc_name = parts[-1]
            pid = int(parts[1])
            # Queremos el exacto "com.tuya.smart"
            if proc_name == "com.tuya.smart":
                target_pid = pid
                print(f"✅ PID Detectado (ADB): {target_pid} ({proc_name})")
                break
        
    if not target_pid:
        print("❌ No encontré el proceso principal com.tuya.smart en ps.")
        sys.exit(1)
            
    session = device.attach(target_pid)
    
    script = session.create_script(jscode)
    script.on("message", on_message)
    script.load()
    
    print("⚡ Inyectado exitosamente. ¡Hacé tu magia (Tocá el timbre)!")
    sys.stdin.read()
    
except Exception as e:
    print(f"❌ Error: {e}")
    # print("Tip: Aseguralo que Frida Server corre en Waydroid y ADB conecta.")
