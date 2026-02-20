
import asyncio
from androidtvremote2 import AndroidTVRemote

async def test_navigation(ip):
    print(f"Conectando al Deco en {ip} para test de navegación...")
    
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile="./iot/cert.pem",
        keyfile="./iot/key.pem",
        host=ip
    )

    try:
        await client.async_connect()
        print("✅ CONECTADO.")
        
        # Prueba 1: Botón Home (Si esto funciona, el Deco DEBE ir al menú de Android)
        print("🏠 Enviando HOME...")
        client.send_key_command("HOME")
        await asyncio.sleep(2)
        
        # Prueba 2: Volver a la app (Usualmente con Back o volviendo a entrar)
        print("⬅️ Enviando BACK...")
        client.send_key_command("BACK")
        await asyncio.sleep(2)
        
        # Prueba 3: Moverse en el mosaico
        print("⬇️ Enviando ABAJO...")
        client.send_key_command("DPAD_DOWN")
        await asyncio.sleep(1)
        
        print("➡️ Enviando DERECHA...")
        client.send_key_command("DPAD_RIGHT")
        await asyncio.sleep(1)
        
        print("🆗 Enviando OK (DPAD_CENTER)...")
        client.send_key_command("DPAD_CENTER")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_navigation("192.168.0.9"))
