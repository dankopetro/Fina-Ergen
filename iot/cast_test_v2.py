
import pychromecast
import time
import sys

def test_cast_control(ip):
    print(f"Buscando Chromecast/Deco en {ip}...")
    
    # Discovery
    services, browser = pychromecast.discovery.discover_chromecasts(timeout=5)
    
    target_cast = None
    
    # Try to find by IP in discovered devices
    if services:
        for cast_info in services:
            # host comes as (ip, port) or just ip depending on version/zeroconf
            # cast_info.host is usually a string IP
            if cast_info.host == ip:
                print(f"Encontrado en discovery: {cast_info.friendly_name}")
                target_cast = pychromecast.get_chromecast_from_cast_info(cast_info, browser.zc)
                break
    
    # Fallback manual connection
    if not target_cast:
        print(f"No encontrado en discovery, intentando conexión directa a {ip}...")
        try:
            target_cast = pychromecast.Chromecast(ip)
        except Exception as e:
            print(f"Error conectando manualmente: {e}")
            return

    if target_cast:
        # Wait for connection
        target_cast.wait()
        
        print(f"\n✅ CONECTADO EXITOSAMENTE")
        print(f"Nombre: {target_cast.name}")
        print(f"Modelo: {target_cast.model_name}")
        print(f"UUID: {target_cast.uuid}")
        
        # Status
        status = target_cast.status
        if status:
            vol_pct = status.volume_level * 100 if status.volume_level else 0
            print(f"Volumen actual: {vol_pct:.0f}%")
            print(f"Muteado: {status.volume_muted}")
            print(f"App Id: {target_cast.app_id}")
            print(f"App Name: {target_cast.app_display_name}")
        
        # TEST CONTROL: Volume Mute Toggle
        print("\n🔊 Probando MUTE/UNMUTE...")
        original_mute = status.volume_muted
        
        print(f"Cambiando mute a {not original_mute}...")
        target_cast.set_volume_muted(not original_mute)
        time.sleep(3)
        
        status_after = target_cast.status
        print(f"Estado mute nuevo: {status_after.volume_muted}")
        
        print(f"Restaurando mute a {original_mute}...")
        target_cast.set_volume_muted(original_mute)
        time.sleep(1)
        
        print("\n📺 Probando lanzar YouTube (Splash screen)...")
        # YouTube App ID: 233637DE
        # Just launching the app to see if it reacts
        try:
            target_cast.start_app("233637DE")
            print("Comando de apertura de YouTube enviado.")
            time.sleep(5)
            # Quit app to be polite? Or just leave it.
            # target_cast.quit_app()
        except Exception as e:
            print(f"Error lanzando app: {e}")

    else:
        print("No se pudo obtener el objeto Chromecast.")

    # Stop discovery
    pychromecast.discovery.stop_discovery(browser)

if __name__ == "__main__":
    test_cast_control("192.168.0.9")
