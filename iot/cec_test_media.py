
import subprocess
import sys

def send_cec_command(target_logical_addr, opcode, params=""):
    """
    Envia comando HDMI-CEC real usando 'cmd hdmi_control'
    Esto obliga a la TV a mandar el mensaje al deco, no simular tecla.
    
    Target: 4 (Playback Device / Deco)
    Opcode: 
      0x44 (User Control Pressed)
      0x45 (User Control Released)
    Params: Hex del botón (ej: 04 = Left, 01 = Up, 02 = Down, 03 = Right, 00 = Select)
    """
    # Formato: cmd hdmi_control cec_client <dst> <opcode> <params>
    # En TCL/Android 11+, a veces es: cmd hdmi_control send -d <dst> -t <type> ...
    # Pero probaremos el formato standard de shell service primero.
    
    # Intento 1: Inyectar mensaje directo al bus CEC
    # User Control Pressed (0x44) -> Down (0x02)
    hex_cmd = f"10:44:{params}" 
    # 1 -> TV (src), 4 -> Playback (dst), :44: -> Opcode
    # Espera, '1' suele ser Recorder 1. TV es '0'.
    # Entonces: "04:44:02" (TV le dice a Deco: Se presionó ABAJO)
    
    print(f"Enviando CEC RAW: {hex_cmd}")
    
    # Desafortunadamente 'dumpsys' es solo lectura. 'cmd hdmi_control' a veces permite envío.
    # En muchos Android TV comerciales, NO dejan inyectar raw CEC por seguridad.
    
    # Intento 2: Usar input keyevent con flag de "INJECT_INPUT_EVENT" que a veces rutea a CEC? No.
    
    pass

def try_key_injection(ip):
    # Probamos simular teclas de MEDIOS que suelen viajar por CEC
    # KEYCODE_MEDIA_PLAY_PAUSE = 85
    # KEYCODE_MEDIA_NEXT = 87
    print("Probando Play/Pause (85)...")
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', '85'])

if __name__ == "__main__":
    try_key_injection("192.168.0.10")
