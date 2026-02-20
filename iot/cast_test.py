import time
import pychromecast

def test_cast_control(ip):
    print(f"Buscando Chromecast/Deco en {ip}...")
    
    # Conexión directa por IP (más rápido que discovery)
    cast = pychromecast.Chromecast(ip)
    cast.wait()
    
    print(f"\n✅ CONECTADO A: {cast.device.friendly_name}")
    print(f"Modelo: {cast.device.model_name}")
    print(f"UUID: {cast.device.uuid}")
    
    # Obtener estado actual
    status = cast.status
    print(f"\nEstado Actual:")
    print(f"- Volumen: {status.volume_level * 100:.0f}%")
    print(f"- Muteado: {status.volume_muted}")
    print(f"- App Activa: {cast.app_display_name}")
    
    mc = cast.media_controller
    if mc.status.player_state:
        print(f"- Reproduciendo: {mc.status.title or 'Desconocido'}")
        print(f"- Estado Player: {mc.status.player_state}")
    
    # Prueba de control simple: Mute Toggle (Rápido para ver si reacciona)
    print("\n🔊 Probando control de volumen (Mute Toggle)...")
    original_mute = status.volume_muted
    cast.set_volume_muted(not original_mute)
    time.sleep(2)
    cast.set_volume_muted(original_mute) # Restaurar
    print("Mute test completado.")
    
    # Prueba de lanzamiento de app (YouTube) si no hay nada
    # print("\n📺 Abriendo YouTube (Prueba)...")
    # youtube_app_id = "233637DE"
    # cast.start_app(youtube_app_id)

if __name__ == "__main__":
    try:
        test_cast_control("192.168.0.9")
    except Exception as e:
        print(f"Error: {e}")
