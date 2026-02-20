import subprocess
import json
import os
import sys

# --- FINA ERGEN: MOTOR DE INYECCIÓN UNIFICADO ---

class UniversalMobileHub:
    def __init__(self, ip="192.168.0.6", silent=False):
        self.ip = ip
        self.silent = silent
        self.target = f"{ip}:5555" if "." in ip and ":" not in ip else ip
        self.config = {"sms_code": 6, "sub_id": 1, "pkg": "com.android.shell"}

    def send_sms(self, number, message):
        code = self.config["sms_code"]
        sub_id = self.config["sub_id"]
        pkg = self.config["pkg"]

        # ESTRATEGIA DE INGENIERÍA: 
        # Enviamos el comando completo como una sola cadena para que las comillas internas (\") 
        # lleguen vivas al kernel de Android y protejan los espacios del mensaje.
        adb_call = f'service call isms {code} i32 {sub_id} s16 {pkg} s16 null s16 {number} s16 null s16 \"{message}\" s16 null s16 null'
        
        adb_cmd = ["adb", "-s", self.target, "shell", adb_call]
        
        try:
            res = subprocess.run(adb_cmd, capture_output=True, text=True, timeout=10)
            # El kernel devuelve Parcel( 00000000... o Parcel( 00000001...
            success = "00000000" in res.stdout or "0x00000001" in res.stdout or "Parcel(" in res.stdout
            return success
        except Exception:
            return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("pos_num", nargs="?", default=None)
    parser.add_argument("pos_msg", nargs="*", default=None)
    parser.add_argument("--ip", default="192.168.0.6")
    parser.add_argument("--number")
    parser.add_argument("--msg")
    parser.add_argument("command", nargs="?", default=None)

    args, unknown = parser.parse_known_args()

    # Si hay flags --number y --msg, es una llamada de la UI (Fina)
    is_ui_call = (args.number and args.msg) or (args.command == "send_sms")
    
    target_num = args.number or args.pos_num
    target_msg = args.msg or (" ".join(args.pos_msg) if args.pos_msg else "")
    
    # Si viene de posicionarles de terminal y el primer arg era "send_sms"
    if args.command == "send_sms" and not target_num and unknown:
        target_num = unknown[0]
        target_msg = " ".join(unknown[1:])

    hub = UniversalMobileHub(ip=args.ip, silent=is_ui_call)
    
    if not target_num or not target_msg:
        if is_ui_call:
            print(json.dumps({"status": "error", "message": "Faltan datos"}))
        else:
            print("❌ USO: mobile_hub.py [numero] [mensaje]")
        sys.exit(1)

    if hub.send_sms(target_num, target_msg):
        if is_ui_call:
            print(json.dumps({"status": "success", "message": "Enviado"}))
        else:
            print(f"✅ EXITO: Mensaje enviado a {target_num}")
    else:
        if is_ui_call:
            print(json.dumps({"status": "error", "message": "Error de inyeccion"}))
        else:
            print("❌ FALLO: El kernel rechazo el envio.")
