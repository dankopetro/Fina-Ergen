
import asyncio
from androidtvremote2 import AndroidTVRemote

async def test_control():
    print("Conectando al Deco Telecentro 4K...")
    
    cert_path = "./iot/cert.pem"
    key_path = "./iot/key.pem"
    
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile=cert_path,
        keyfile=key_path,
        host="192.168.0.9"
    )

    try:
        await client.async_connect()
        print("✅ CONECTADO.")
        
        # Probar ir a la derecha y luego OK (lo que antes no funcionaba por CEC)
        print("👉 Enviando DERECHA...")
        client.send_key_command("DPAD_RIGHT")
        await asyncio.sleep(1)
        
        print("✅ Enviando ENTER/OK...")
        client.send_key_command("DPAD_CENTER")
        await asyncio.sleep(1)
        
        print("Control de prueba finalizado.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_control())
