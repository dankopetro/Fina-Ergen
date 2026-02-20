
import subprocess
import re
import argparse
import sys
import time

def parse_hdmi_control(ip):
    """
    Parses `dumpsys hdmi_control` to find connected devices and ports.
    """
    cmd = ['adb', '-s', f'{ip}:5555', 'shell', 'dumpsys', 'hdmi_control']
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = res.stdout
        
        devices = []
        # Regex to find logical devices
        # Often: "mDeviceInfos: \n...logical_address: 4, physical_address: 0x1000..."
        # But format varies heavily by vendor. Let's look for "logical_address:" 
        
        # Simplified parsing for standard Android TV dumpsys
        # Looking for lines like:
        # logical_address: 4, physical_address: 0x1000, port_id: 1, device_type: 4
        
        lines = output.split('\n')
        current_device = {}
        
        print("\n--- Raw Device Info ---")
        for line in lines:
            if "logical_address:" in line:
                print(line.strip())
                # Extract logical address
                match = re.search(r'logical_address: (\d+)', line)
                if match:
                    current_device['logical'] = int(match.group(1))
                
                # Extract physical address
                match_phy = re.search(r'physical_address: (0x[0-9a-fA-F]+)', line)
                if match_phy:
                    current_device['physical'] = match_phy.group(1)
                
                # Extract port id if present
                match_port = re.search(r'port_id: (\d+)', line)
                if match_port:
                    current_device['port'] = int(match_port.group(1))
                
                if current_device:
                    devices.append(current_device)
                    current_device = {}

        return devices

    except Exception as e:
        print(f"Error parsing HDMI control: {e}")
        return []

def switch_input(ip, keycode):
    """
    Switches input using keyevent.
    KEYCODE_TV_INPUT_HDMI1 = 243
    KEYCODE_TV_INPUT_HDMI2 = 244
    KEYCODE_TV_INPUT_HDMI3 = 245
    KEYCODE_TV_INPUT_HDMI4 = 246
    """
    print(f"Switching input on {ip} with keycode {keycode}...")
    cmd = ['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', str(keycode)]
    subprocess.run(cmd)

def send_key(ip, keycode):
    print(f"Sending key {keycode} to {ip}...")
    cmd = ['adb', '-s', f'{ip}:5555', 'shell', 'input', 'keyevent', str(keycode)]
    subprocess.run(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HDMI-CEC Control via ADB')
    parser.add_argument('--ip', default='192.168.0.10', help='TV IP address')
    parser.add_argument('--scan', action='store_true', help='Scan for CEC devices')
    parser.add_argument('--switch', type=int, help='Switch to HDMI port (1-4)')
    parser.add_argument('--key', type=str, help='Send key (e.g., UP, DOWN, CENTER, BACK)')
    
    args = parser.parse_args()

    if args.scan:
        devices = parse_hdmi_control(args.ip)
        print(f"\nFound {len(devices)} CEC devices.")
        for d in devices:
            print(d)
    
    if args.switch:
        # Map port to keycode
        keycodes = {
            1: 243,
            2: 244,
            3: 245,
            4: 246
        }
        if args.switch in keycodes:
            switch_input(args.ip, keycodes[args.switch])
        else:
            print("Invalid port. Use 1-4.")

    if args.key:
        key_map = {
            "UP": 19,
            "DOWN": 20,
            "LEFT": 21,
            "RIGHT": 22,
            "CENTER": 23,
            "ENTER": 66,
            "BACK": 4,
            "HOME": 3,
            "MENU": 82
        }
        
        k = args.key.upper()
        if k in key_map:
            send_key(args.ip, key_map[k])
        elif k.isdigit():
             send_key(args.ip, int(k))
        else:
            print(f"Unknown key: {args.key}")
