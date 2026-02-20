
import asyncio
from androidtvremote2 import AndroidTVRemote

async def get_detailed_info():
    ip = "192.168.0.9"
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile="./iot/cert.pem",
        keyfile="./iot/key.pem",
        host=ip
    )

    try:
        await client.async_connect()
        info = client.device_info
        print(f"MODELO: {info.get('model')}")
        print(f"FABRICANTE: {info.get('manufacturer')}")
        print(f"VERSION: {info.get('sw_version')}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    asyncio.run(get_detailed_info())
