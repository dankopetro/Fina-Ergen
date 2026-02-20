
import asyncio
from androidtvremote2 import AndroidTVRemote

async def diagnose_deco(ip):
    print(f"Conectando al Deco en {ip}...")
    
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile="./iot/cert.pem",
        keyfile="./iot/key.pem",
        host=ip
    )

    try:
        await client.async_connect()
        print("✅ CONECTADO.")
        
        # 1. Sacarnos de Disney (Volver a Home)
        print("🏠 Volviendo a Home para cerrar Disney...")
        client.send_key_command("HOME")
        await asyncio.sleep(2)

        # 2. Ver qué app está en primer plano
        app = client.current_app
        print(f"📱 App actual en primer plano: {app}")
        
        # 3. Ver info del dispositivo
        info = client.device_info
        print(f"📺 Info dispositivo: {info}")

        # 4. Ver volumen
        vol = client.volume_info
        print(f"🔊 Volumen: {vol}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    asyncio.run(diagnose_deco("192.168.0.9"))
