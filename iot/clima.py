import asyncio
import sys
import argparse
import socket
import json
from msmart.device import AirConditioner as AC
from msmart.device.AC.command import Command
from msmart.const import FrameType

# --- HACK DE ENERGÍA SURREY ---
class EnergyHackCommand(Command):
    def __init__(self, sub_cmd):
        super().__init__(FrameType.QUERY)
        self._payload = bytes([0x41, 0x24, 0x01, sub_cmd])
    def tobytes(self):
        p = bytearray(20)
        p[0:4] = self._payload
        return super().tobytes(p)

def decode_bcd(d):
    return 10 * (d >> 4) + (d & 0xF)
# ------------------------------

# DATOS MAESTROS DEL AIRE SURREY (V2 - Sin necesidad de Token/Key)
IP = "192.168.0.213"
DEVICE_ID = 30786325625801

def send_event(event_name, payload):
    """Envia un evento UDP al Brain de Fina"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # El cerebro Phoenix escucha en el puerto 5555
        message = json.dumps({"type": "event", "name": event_name, "payload": payload, "module": "clima"})
        sock.sendto(message.encode(), ("127.0.0.1", 5555))
        sock.close()
    except Exception as e:
        print(f"Error enviando evento UDP: {e}")

async def control_aire():
    parser = argparse.ArgumentParser()
    parser.add_argument("--power", choices=["on", "off"])
    parser.add_argument("--temp", type=float)
    parser.add_argument("--swing", choices=["on", "off"])
    parser.add_argument("--turbo", choices=["on", "off"])
    parser.add_argument("--mode", choices=["auto", "cool", "dry", "heat", "fan"])
    parser.add_argument("--fan", choices=["auto", "low", "medium", "high", "full"])
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--silent", action="store_true")
    parser.add_argument("--ip", type=str, help="IP del equipo AC")
    args = parser.parse_args()

    try:
        target_ip = args.ip if args.ip else IP
        device = AC(ip=target_ip, port=6444, device_id=DEVICE_ID)
        
        # SI ES STATUS, REFRESCAMOS (Consulta robusta con reintentos)
        if args.status:
            for i in range(3):
                try:
                    await device.refresh()
                    if device.online:
                        break
                except Exception as e:
                    print(f"Intento {i+1} fallido: {e}")
                await asyncio.sleep(1) # Esperar 1s entre reintentos
            
            if not device.online:
                print("Error: El dispositivo parece estar offline.")
                if not args.silent:
                    send_event("fina-speak", "No pude conectar con el aire acondicionado.")
                return

            estado = "encendido" if device.power_state else "apagado"
            mode_names = {1: "Auto", 2: "Cool", 3: "Dry", 4: "Heat", 5: "Fan"}
            modo_actual = mode_names.get(device.operational_mode, "Desconocido")
            
            # --- OBTENER ENERGÍA (HACK) ---
            watts = 0
            total_kwh = 0
            try:
                # 1. Energía Acumulada (Sub-cmd 0x44) - MÁS AGRESIVO
                found_energy = False
                for _ in range(3):
                    resp_energy = await device._send_commands_get_responses([EnergyHackCommand(0x44)])
                    if resp_energy:
                        for r in resp_energy:
                            if r.id == 0xC1 and r.payload[3] == 0x44:
                                d = r.payload
                                # El acumulado viene en Wh, lo pasamos a kWh dividiendo por 1000
                                raw_wh = (10000 * decode_bcd(d[4]) + 100 * decode_bcd(d[5]) + 1 * decode_bcd(d[6]) + 0.01 * decode_bcd(d[7]))
                                total_kwh = round(raw_wh / 1000, 2)
                                found_energy = True
                                break
                    if found_energy: break
                    await asyncio.sleep(0.4)

                # 2. Potencia Instantánea (Sub-cmd 0x43) - Solo si está encendido (ahorro de tiempo)
                if device.power_state:
                    for _ in range(3):
                        resp_power = await device._send_commands_get_responses([EnergyHackCommand(0x43)])
                        if resp_power:
                            found_43 = False
                            for r in resp_power:
                                if r.id == 0xC1 and r.payload[3] == 0x43:
                                    raw_w = r.payload[16]
                                    watts = raw_w * 10
                                    found_43 = True
                                    break
                            if found_43: break
                        await asyncio.sleep(0.3)
                else:
                    watts = 0 # En standby es 0 o despreciable
            except Exception as energy_err:
                if not args.silent: print(f"Error obteniendo energía: {energy_err}")
            # ------------------------------

            msg = f"El aire está {estado} en modo {modo_actual} a {device.target_temperature}°C. Consumo: {watts}W. Acumulado: {total_kwh}kWh. Int: {device.indoor_temperature}°C | Ext: {device.outdoor_temperature or '--'}°C."
            if device.indoor_humidity:
                msg += f" Humedad: {device.indoor_humidity}%"
            
            # Incluir datos de energía en el JSON para la UI
            payload_status = {
                "power": device.power_state,
                "temp": device.target_temperature,
                "mode": modo_actual.upper(),
                "indoor": device.indoor_temperature,
                "outdoor": device.outdoor_temperature,
                "watts": watts,
                "total_kwh": total_kwh
            }
            send_event("ac-status-update", payload_status)
            
            print(msg)
            if not args.silent:
                send_event("fina-speak", msg)
            return

        # SI ES COMANDO, ENVIAMOS DIRECTO (Acción rápida)
        needs_apply = False
        
        if args.power:
            device.power_state = (args.power == "on")
            needs_apply = True
            msg = f"Aire acondicionado {'encendido' if device.power_state else 'apagado'}."

        if args.temp:
            if 17 <= args.temp <= 30:
                device.target_temperature = args.temp
                device.power_state = True 
                needs_apply = True
                msg = f"Aire a {args.temp} grados."
            else:
                print("Temperatura fuera de rango (17-30).")

        if args.mode:
            mode_map = {"auto": 1, "cool": 2, "dry": 3, "heat": 4, "fan": 5}
            device.operational_mode = mode_map.get(args.mode, 2)
            device.power_state = True
            needs_apply = True
            msg = f"Modo {args.mode} activado."

        if args.fan:
            speeds = {"auto": 102, "low": 40, "medium": 60, "high": 80, "full": 100}
            device.fan_speed = speeds.get(args.fan, 102)
            needs_apply = True
            msg = f"Ventilador en {args.fan}."

        if args.swing:
            device.swing_mode = 0x0C if args.swing == "on" else 0x00
            needs_apply = True
            msg = f"Swing {'activado' if args.swing == 'on' else 'desactivado'}."

        if args.turbo:
            device.turbo = (args.turbo == "on")
            needs_apply = True
            msg = f"Turbo {'activado' if args.turbo == 'on' else 'desactivado'}."

        if needs_apply:
            device.beep = True
            await device.apply()
            print(msg)
            if not args.silent:
                send_event("fina-speak", msg)

    except Exception as e:
        print(f"Error controlando el aire: {e}")

if __name__ == "__main__":
    asyncio.run(control_aire())
