
import asyncio
import os
import time
from androidtvremote2 import AndroidTVRemote

async def pair():
    print("Iniciando emparejamiento con Telecentro 4K (192.168.0.9)...")
    
    cert_path = "./iot/cert.pem"
    key_path = "./iot/key.pem"
    code_file = "./iot/code.txt"
    
    # Limpiar archivo de código previo
    if os.path.exists(code_file):
        os.remove(code_file)
    
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile=cert_path,
        keyfile=key_path,
        host="192.168.0.9"
    )

    try:
        print("Generando certificados...")
        await client.async_generate_cert_if_missing()
        
        print("Solicitando emparejamiento... MIRA LA TV.")
        await client.async_start_pairing()
        
        print(f"\nESPERANDO CÓDIGO en {code_file}...")
        
        # Esperar hasta 2 minutos
        start_wait = time.time()
        code = None
        while time.time() - start_wait < 120:
            if os.path.exists(code_file):
                with open(code_file, "r") as f:
                    code = f.read().strip()
                if code:
                    break
            await asyncio.sleep(1)
        
        if not code:
            print("Tiempo de espera agotado o código vacío.")
            return

        print(f"Enviando código: {code}...")
        await client.async_finish_pairing(code)
        
        print("\n¡EMPAREJAMIENTO EXITOSO! 🎉")
        
    except Exception as e:
        print(f"\n❌ Error durante el emparejamiento: {e}")
    finally:
        client.disconnect()
        if os.path.exists(code_file):
            os.remove(code_file)

if __name__ == "__main__":
    asyncio.run(pair())
