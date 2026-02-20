
import subprocess
import time
import pychromecast

DECO_IP = "192.168.0.9"

def wake_deco_with_cast():
    print("🚀 Lanzando Cast (YouTube) para despertar Deco y cambiar Input...")
    try:
        # Discovery para asegurar conexión fresca
        services, browser = pychromecast.discovery.discover_chromecasts(timeout=5)
        cast = None
        for s in services:
             if s.host == DECO_IP:
                 cast = pychromecast.get_chromecast_from_cast_info(s, browser.zc)
                 break
        
        if not cast:
            cast = pychromecast.Chromecast(DECO_IP)
            
        cast.wait()
        
        # YouTube Wake Up Call
        print(f"   Conectado a {cast.name}. Abriendo YouTube...")
        cast.start_app("233637DE")
        
        # Esperamos suficiente para que:
        # 1. El Deco despierte (salga de sleep/screensaver)
        # 2. La TV detecte señal y cambie a HDMI automáticamente (CEC One Touch Play)
        time.sleep(12) 
        
        print("🛑 Cerrando Cast para volver a TV en vivo...")
        cast.quit_app()
        
    except Exception as e:
        print(f"   Error en Cast: {e}")

if __name__ == "__main__":
    wake_deco_with_cast()
