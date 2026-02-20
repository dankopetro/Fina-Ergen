
import tinytuya
import json
import os
import time

# Load credentials
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "..", "tuya_config.json")

print(f"Loading config from {CONFIG_PATH}...")
with open(CONFIG_PATH, "r") as f:
    config = json.load(f)

# Initialize Device
# Generic device creation
print(f"Initializing Tuya Device: {config['name']} ({config['device_id']})...")

versions = ['3.3', '3.4', '3.1', '3.5']

for ver in versions:
    print(f"\n⏳ Testing Protocol Version {ver}...")
    try:
        d = tinytuya.Device(
            dev_id=config['device_id'],
            address=config['ip'],      
            local_key=config['local_key'], 
            version=ver
        )
        
        # d.set_socketPersistent(True) # Disable for testing different versions

        print(f"   Connecting using v{ver}...")
        data = d.status() 
        
        if data and 'dps' in data:
            print(f"\n🎉 SUCCESS with Version {ver}!")
            print("--- Device Status ---")
            print(json.dumps(data, indent=4))
            
            # Update config file with working version
            config['version'] = float(ver)
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=4)
            print("✅ Config updated with correct version.")
            break
        elif 'Error' in data:
             print(f"   ❌ Failed v{ver}: {data}")

    except Exception as e:
        print(f"   ❌ Error v{ver}: {e}")
