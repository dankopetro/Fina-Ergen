
import tinytuya
import json
import socket
import time

print("🔍 Scanning User Local Network for Tuya Devices...")
print("Please ensure the device is AWAKE (press the doorbell button now!)")

try:
    # Scan for devices (10 seconds)
    # This sends UDP broadcast packets
    devices = tinytuya.deviceScan(verbose=True)
    
    print(f"\n✅ Scan Finished. Found {len(devices)} devices.")
    
    for device in devices:
        print(f"\nFOUND: {device['ip']} - ID: {device['id']} - Version: {device['version']}")
        print(f"Product Key: {device.get('productKey', 'N/A')}")
        
    # If devices are found, trying to match with our config
    try:
        with open("tuya_config.json", "r") as f:
            config = json.load(f)
            target_id = config.get("device_id")
            
        for device in devices:
            if device['id'] == target_id:
                print(f"\n🎉 MATCH FOUND! The doorbell IP is {device['ip']}")
                
                # Update config with correct local IP
                # We need to preserve the version if detected
                config['ip'] = device['ip']
                config['version'] = device['version']
                
                with open("tuya_config.json", "w") as f:
                    json.dump(config, f, indent=4)
                print("✅ tuya_config.json updated with correct Local IP.")
                break
                
    except FileNotFoundError:
        pass

except Exception as e:
    print(f"❌ Error during scan: {e}")
