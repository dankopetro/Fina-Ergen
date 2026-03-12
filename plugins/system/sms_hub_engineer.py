import subprocess
import sys
import time

# --- MOTOR DE INGENIERÍA FINAL (VERIFICADO) ---
# Transacción Confirmada: 6
# SubID Confirmado: 0
# Estado: Funciona con pantalla apagada

def send_sms_final(number, message, ip="127.0.0.1"):
    target = f"{ip}:5555"
    pkg = "com.android.shell"
    
    # Firma de 8 parámetros confirmada por diag_sms
    params = [
        "i32 0",               # subId (0 funcionó)
        f"s16 \"{pkg}\"",      # callingPkg
        "s16 \"null\"",        # attributionTag
        f"s16 \"{number}\"",   # destAddr
        "s16 \"null\"",        # scAddr
        f"s16 \"{message}\"",  # text (EL MENSAJE)
        "s16 \"null\"",        # sentIntent
        "s16 \"null\""         # deliveryIntent
    ]

    print(f"[SMS_FINAL] Disparando Transacción 6 a {number}...")
    
    # Usamos una lista para evitar problemas de comillas en el shell
    adb_cmd = ["adb", "-s", target, "shell", "service", "call", "isms", "6"] + params
    
    try:
        res = subprocess.run(adb_cmd, capture_output=True, text=True, timeout=10)
        if "00000000" in res.stdout:
            print("✅ KERNEL: Mensaje entregado a la radiofrecuencia.")
            return True
        else:
            print(f"❌ KERNEL: Error en la respuesta -> {res.stdout}")
            return False
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {e}")
        return False

if __name__ == "__main__":
    # Prueba final con el mensaje solicitado
    TARGET_IP = "127.0.0.1"
    DESTINO = "2213999606"
    MENSAJE = "Como estas?" # <--- El mensaje que querías probar
    
    if send_sms_final(DESTINO, MENSAJE, TARGET_IP):
        print("\n🚀 PRUEBA DE INGENIERÍA COMPLETADA CON ÉXITO")
    else:
        print("\n⚠️ FALLO EN EL ÚLTIMO PASO")
