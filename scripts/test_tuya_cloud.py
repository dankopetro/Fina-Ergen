
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

print(f"☁️ Connecting to Tuya Cloud for device: {config['name']}...")

try:
    # Connect to Tuya Cloud
    c = tinytuya.Cloud(
        apiRegion=config['region_code'], 
        apiKey=config['access_id'], 
        apiSecret=config['access_secret'], 
        apiDeviceID=config['device_id']
    )

    # Get Status
    print("📡 Fetching device status from Cloud...")
    status = c.getstatus(config['device_id'])
    
    print("\n--- Cloud Status Response ---")
    print(json.dumps(status, indent=4))
    
    if 'result' in status:
        print("\n✅ Cloud Connection Successful!")
        # Try to get specific properties
        props = status['result']
        for p in props:
            print(f" - {p['code']}: {p['value']}")
            
        # Try to get extra functions (like battery)
        print("\n🔋 Checking device functions...")
        funcs = c.getfunctions(config['device_id'])
        print(json.dumps(funcs, indent=4))
        
    else:
        print("\n⚠️ Failed to get status from cloud.")

except Exception as e:
    print(f"\n❌ Cloud Error: {e}")
