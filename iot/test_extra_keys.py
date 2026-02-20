
import asyncio
from androidtvremote2 import AndroidTVRemote

async def test_keys(ip):
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile="./iot/cert.pem",
        keyfile="./iot/key.pem",
        host=ip
    )
    try:
        await client.async_connect()
        await asyncio.sleep(1)
        
        # Probar codigos numericos directos que suelen ser Guide e Info
        print("尝试 KEYCODE_GUIDE (172)...")
        client.send_key_command(172)
        await asyncio.sleep(3)
        
        print("尝试 KEYCODE_INFO (165)...")
        client.send_key_command(165)
        await asyncio.sleep(3)

        print("尝试 KEYCODE_MENU (82)...")
        client.send_key_command(82)
        await asyncio.sleep(3)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_keys("192.168.0.9"))
