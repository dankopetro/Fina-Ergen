
import asyncio
from androidtvremote2 import AndroidTVRemote

async def tune_to_channel_13(ip):
    print(f"Sintonizando Canal 26 (Número 13) en {ip}...")
    
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile="./iot/cert.pem",
        keyfile="./iot/key.pem",
        host=ip
    )

    try:
        await client.async_connect()
        print("✅ CONECTADO.")
        
        # Marcando '1' '3'
        print("🔢 Marcando 1...")
        client.send_key_command(8) # KEYCODE_1
        await asyncio.sleep(0.5)
        
        print("🔢 Marcando 3...")
        client.send_key_command(10) # KEYCODE_3
        await asyncio.sleep(1)
        
        print("🆗 Confirmando con ENTER...")
        client.send_key_command(66) # KEYCODE_ENTER
        
        print("📡 Canal solicitado.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    asyncio.run(tune_to_channel_13("192.168.0.9"))
