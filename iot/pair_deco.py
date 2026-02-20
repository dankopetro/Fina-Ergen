
import asyncio
import os
from androidtvremote2 import AndroidTVRemote

async def pair():
    print("Iniciando emparejamiento con Telecentro 4K (192.168.0.9)...")
    
    # Rutas para guardar los certificados
    cert_path = "./iot/cert.pem"
    key_path = "./iot/key.pem"
    
    client = AndroidTVRemote(
        client_name="Fina Ergen", 
        certfile=cert_path,
        keyfile=key_path,
        host="192.168.0.9"
    )

    try:
        # Generar certificado si no existe
        print("Generando certificados...")
        await client.async_generate_cert_if_missing()
        
        # Iniciar emparejamiento
        print("Solicitando emparejamiento... MIRA LA TV.")
        await client.async_start_pairing()
        
        # Pedir código al usuario
        # Usamos input() síncrono por simplicidad aquí ya que es un script CLI
        print("\n>>> INGRESA EL CÓDIGO DE 6 CARACTERES QUE APARECE EN LA TV:")
        code = input("Código: ").strip()
        
        if not code:
            print("No ingresaste ningún código.")
            return

        print(f"Enviando código: {code}...")
        await client.async_finish_pairing(code)
        
        print("\n¡EMPAREJAMIENTO EXITOSO! 🎉")
        print(f"Certificados guardados en: {cert_path}")
        
    except Exception as e:
        print(f"\n❌ Error durante el emparejamiento: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    # Corremos el loop de forma que podamos usar input()
    asyncio.run(pair())
