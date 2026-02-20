
import subprocess
import time

def sequence_to_deco():
    # 1. Volver a TV Linear (Canal 2, Aire, etc.) para estar en ORIGEN.
    # KEYCODE_TV = 170
    print("Forzando modo TV...")
    subprocess.run(['adb', '-s', '192.168.0.10:5555', 'shell', 'input', 'keyevent', '170'])
    time.sleep(4) # Dar tiempo a que cargue la señal de aire/cable

    # 2. Abrir menú de Entradas
    # KEYCODE_TV_INPUT = 178
    print("Abriendo menú entradas...")
    subprocess.run(['adb', '-s', '192.168.0.10:5555', 'shell', 'input', 'keyevent', '178'])
    time.sleep(2)

    # 3. Bajar 1 VEZ (De 'TV' a 'Telecentro 4K')
    print("Bajando a Telecentro 4K...")
    subprocess.run(['adb', '-s', '192.168.0.10:5555', 'shell', 'input', 'keyevent', '20'])
    time.sleep(0.5)

    # 4. OK
    print("Seleccionando...")
    subprocess.run(['adb', '-s', '192.168.0.10:5555', 'shell', 'input', 'keyevent', '66'])

if __name__ == "__main__":
    sequence_to_deco()
