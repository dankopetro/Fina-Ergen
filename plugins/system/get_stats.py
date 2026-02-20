
import psutil
import json
import time
import os
import platform

def get_stats():
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else 0
    cpu_count = psutil.cpu_count()
    
    # RAM
    mem = psutil.virtual_memory()
    ram_percent = mem.percent
    ram_used = round(mem.used / (1024**3), 2)
    ram_total = round(mem.total / (1024**3), 2)
    
    # DISK
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    disk_free = round(disk.free / (1024**3), 2)
    disk_total = round(disk.total / (1024**3), 2)

    # NETWORK
    net = psutil.net_io_counters()
    net_sent = round(net.bytes_sent / (1024**2), 2) # MB
    net_recv = round(net.bytes_recv / (1024**2), 2) # MB

    # UPTIME
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_hours = int(uptime_seconds // 3600)
    uptime_minutes = int((uptime_seconds % 3600) // 60)
    
    # OS
    os_name = platform.system()
    node_name = platform.node()

    return {
        "cpu": {
            "percent": cpu_percent,
            "freq": cpu_freq,
            "cores": cpu_count
        },
        "ram": {
            "percent": ram_percent,
            "used": ram_used,
            "total": ram_total
        },
        "disk": {
            "percent": disk_percent,
            "free": disk_free,
            "total": disk_total
        },
        "net": {
            "sent": net_sent,
            "recv": net_recv
        },
        "uptime": f"{uptime_hours}h {uptime_minutes}m",
        "os": os_name,
        "node": node_name
    }

if __name__ == "__main__":
    print(json.dumps(get_stats()))
