
import asyncio
from androidtvremote2 import AndroidTVRemote

async def test_channels(ip):
    print(f"Conectando al Deco en {ip} para probar canales...")
    
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile="./iot/cert.pem",
        keyfile="./iot/key.pem",
        host=ip
    )

    try:
        await client.async_connect()
        print("✅ CONECTADO.")
        
        # Intentar poner canal 26 (como ejemplo)
        # KEYCODE_2 = 9, KEYCODE_6 = 13
        print("🔢 Enviando dígito 2...")
        client.send_key_command(9) 
        await asyncio.sleep(0.5)
        
        print("🔢 Enviando dígito 6...")
        client.send_key_command(13)
        await asyncio.sleep(1)
        
        print("🆗 Enviando ENTER para confirmar canal...")
        client.send_key_command(66)
        
        await asyncio.sleep(2)
        
        print("🔼 Probando CHANNEL_UP (166)...")
        client.send_key_command(166)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_channels("192.168.0.9"))
