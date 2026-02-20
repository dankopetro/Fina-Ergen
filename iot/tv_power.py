
import subprocess
import sys
import time
import socket
import os

# Intento de cargar la última IP usada
def get_target_ip():
    try:
        with open("/tmp/fina_last_tv_ip", "r") as f:
            return f.read().strip()
    except:
        return '192.168.0.11' # Default

TARGET_IP = get_target_ip()

def send_power_command(ip):
    """Envía el comando de encendido a la TV"""
    try:
        print(f'Enviando comando de encendido a {ip}...')
        subprocess.run(
            ['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', 'KEYCODE_POWER'],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f'✓ Comando de encendido enviado exitosamente a {ip}')
        return True
            
    except subprocess.TimeoutExpired:
        print(f'⚠ Comando enviado (timeout esperado)')
        return True
    except Exception as e:
        print(f'✗ Error al enviar comando: {e}')
        return False

def main():
    print('=' * 60)
    print(f'TV POWER SCRIPT - TARGET: {TARGET_IP}')
    print('=' * 60)
    
    send_power_command(TARGET_IP)

if __name__ == '__main__':
    main()
