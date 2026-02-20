
import subprocess
import time

def goto_home_and_select_input(ip):
    # 1. HOME (Asegurar punto de partida)
    print("Yendo a HOME...")
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', '3'])
    time.sleep(3)

    # 2. Arriba (Para llegar a la fila de iconos de sistema)
    print("Subiendo...")
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', '19']) # UP
    time.sleep(0.5)

    # 3. Derecha (3 veces para llegar al icono de Entradas/Source)
    print("Navegando a la derecha (3 veces)...")
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', '22']) # RIGHT
    time.sleep(0.3)
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', '22']) # RIGHT
    time.sleep(0.3)
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', '22']) # RIGHT
    time.sleep(0.5)

    # 4. OK (Abrir menú de entradas)
    print("Abriendo menú Entradas...")
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', '66']) # ENTER
    time.sleep(2)

    # 5. Bajar (para buscar HDMI 1 / Deco)
    # Aquí asumimos que al abrirse queda en la primera opción o en la actual.
    # Probaremos bajar 1 vez y seleccionar.
    print("Bajando a opción Deco...")
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', '20']) # DOWN
    time.sleep(0.5)

    # 6. OK Final
    print("Seleccionando Deco...")
    subprocess.run(['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', '66']) # ENTER

if __name__ == "__main__":
    goto_home_and_select_input("192.168.0.10")
