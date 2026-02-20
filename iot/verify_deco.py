
import asyncio
import time
from androidtvremote2 import AndroidTVRemote

async def verify():
    ip = "192.168.0.9"
    print(f"Intentando reconexión limpia a {ip}...")
    
    cert_path = "./iot/cert.pem"
    key_path = "./iot/key.pem"
    
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile=cert_path,
        keyfile=key_path,
        host=ip
    )

    try:
        await client.async_connect()
        print("✅ CONECTADO AL SERVICIO.")
        
        # Esperar a que el protocolo remoto se inicialice completamente
        await asyncio.sleep(2)
        
        print(f"Estado: {'Encendido' if client.is_on else 'Apagado/Desconocido'}")
        print(f"App: {client.current_app}")
        
        # Intentar comando básico
        print("🏠 Enviando HOME (Codigo 3)...")
        client.send_key_command(3) # KEYCODE_HOME
        
        await asyncio.sleep(1)
        
        print("🆗 Enviando OK (Codigo 23)...")
        client.send_key_command(23) # KEYCODE_DPAD_CENTER
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    asyncio.run(verify())
