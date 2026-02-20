
import tinytuya
import json
import os
import time

# Load config
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "..", "tuya_config.json")
with open(CONFIG_PATH, "r") as f:
    conf = json.load(f)

print(f"📷 Attempting to get Stream URL for: {conf['name']}")

try:
    c = tinytuya.Cloud(
        apiRegion=conf['region_code'], 
        apiKey=conf['access_id'], 
        apiSecret=conf['access_secret'], 
        apiDeviceID=conf['device_id']
    )

    # 1. Try to get WebRTC stream URL
    # This is an official Tuya API endpoint for streams
    # POST /v1.0/devices/{device_id}/stream/actions/allocate
    print(" requesting stream token...")
    
    # TinyTuya doesn't have a direct method for this specific endpoint yet, 
    # so we might need to use its loose 'sendcommand' or manual requests if available.
    # But let's check what 'getfunctions' returned earlier to see if stream is supported.
    
    # Alternative: Get RTSP URL (Often not available on battery cameras, but worth a try)
    # We will try to execute the 'ipc_stream' logic if available
    
    # For now, let's look at getting a proper stream URL via the official Cloud API method manually if needed.
    # But first, let's try the simplest:
    
    print("Fetching camera stream endpoint...")
    # NOTE: IPC cameras usually require the "Tuya Smart Camera" API service to be enabled in the project.
    
    # Let's try to get the "stream_url" via standard property or manual request
    # This is experimental
    
    # Method A: webrtc url
    # We construct a manual cloud request
    uri = f'/v1.0/devices/{conf["device_id"]}/stream/actions/allocate'
    body = {
        "type": "hls"  # Changed to hls
    }
    
    response = c.cloudrequest(uri, post=body)
    print("\n--- RTSP Allocation Response ---")
    print(json.dumps(response, indent=4))
    
    if 'result' in response and 'url' in response['result']:
        url = response['result']['url']
        print(f"\n🎉 RTSP URL FOUND: {url}")
        print("You can try opening this in VLC.")
        
        # Save to file
        with open("doorbell_stream.m3u", "w") as f:
            f.write(f"#EXTM3U\n#EXTINF:-1,Timbre\n{url}")
        print("Saved to doorbell_stream.m3u")
    else:
        print("\n❌ Failed to get RTSP stream. Trying WebRTC...")
        
        # Try WebRTC
        body['type'] = 'webrtc'
        response = c.cloudrequest(uri, post=body)
        print(json.dumps(response, indent=4))
        
except Exception as e:
    print(f"Error: {e}")
