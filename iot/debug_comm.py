
import asyncio
from androidtvremote2 import AndroidTVRemote

async def test_comm(ip):
    print(f"Probando comunicación con {ip}...")
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile="./iot/cert.pem",
        keyfile="./iot/key.pem",
        host=ip
    )
    try:
        await client.async_connect()
        print("✅ CONECTADO.")
        
        # Probar Volumen (Invisible casi pero genera feedback si hay barra)
        print("🔊 Subiendo volumen...")
        client.send_key_command("VOLUME_UP")
        await asyncio.sleep(1)
        client.send_key_command("VOLUME_DOWN")
        
        # Probar abrir menú de canales (En TPlay suele ser OK o Arriba/Abajo)
        print("🔼 Enviando 'DPAD_UP' para ver si sale la guía...")
        client.send_key_command("DPAD_UP")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_comm("192.168.0.9"))
