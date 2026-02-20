
import asyncio
from androidtvremote2 import AndroidTVRemote

async def move_test():
    ip = "192.168.0.9"
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile="./iot/cert.pem",
        keyfile="./iot/key.pem",
        host=ip
    )
    try:
        await client.async_connect()
        await asyncio.sleep(1)
        
        print("➡️ Moviendo a la DERECHA...")
        client.send_key_command("DPAD_RIGHT")
        await asyncio.sleep(1)
        
        print("⬅️ Moviendo a la IZQUIERDA...")
        client.send_key_command("DPAD_LEFT")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    asyncio.run(move_test())
