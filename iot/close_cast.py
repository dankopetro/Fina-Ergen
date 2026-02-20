
import pychromecast

def close_cast_app(ip):
    # Discovery
    services, browser = pychromecast.discovery.discover_chromecasts(timeout=5)
    
    target_cast = None
    if services:
        for cast_info in services:
            if cast_info.host == ip:
                target_cast = pychromecast.get_chromecast_from_cast_info(cast_info, browser.zc)
                break
    
    if not target_cast:
        try: target_cast = pychromecast.Chromecast(ip)
        except: return

    if target_cast:
        target_cast.wait()
        name = target_cast.name or target_cast.device.friendly_name or "Unknown Device"
        print(f"Saliendo de Cast en {name}...")
        target_cast.quit_app()
    
    pychromecast.discovery.stop_discovery(browser)

if __name__ == "__main__":
    close_cast_app("192.168.0.9")
