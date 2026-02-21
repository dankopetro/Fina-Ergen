
import os
import sys
import datetime
import time

# Logs paths - RUTA UNIVERSAL: ~/.config/Fina/Logs/plugins
LOGS_DIR = os.path.expanduser("~/.config/Fina/Logs/plugins")
COMMANDS_LOG = os.path.join(LOGS_DIR, 'commands.log')
ERRORS_LOG = os.path.join(LOGS_DIR, 'errors.log')

def ensure_logs_dir():
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

def should_rotate_commands():
    if not os.path.exists(COMMANDS_LOG):
        return False
    # Check if improved mod time > 24h
    mtime = os.path.getmtime(COMMANDS_LOG)
    now = time.time()
    return (now - mtime) > 86400  # 24 hours in seconds

def rotate_logs():
    if should_rotate_commands():
        # Rotate commands log (clear it or archive)
        # Here we just clear as requested "que se limpien cada 24 hs"
        with open(COMMANDS_LOG, 'w') as f:
            f.write(f"--- Log rotated at {datetime.datetime.now()} ---\n")

def log_command(msg):
    ensure_logs_dir()
    rotate_logs()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(COMMANDS_LOG, 'a') as f:
        f.write(f"[{timestamp}] [CMD] {msg}\n")
    print(f"Logged command: {msg}")

def log_error(msg):
    ensure_logs_dir()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERRORS_LOG, 'a') as f:
        f.write(f"[{timestamp}] [ERR] {msg}\n")
    print(f"Logged error: {msg}")

def get_recent_logs(lines=50):
    ensure_logs_dir()
    all_logs = []
    
    # Read commands
    if os.path.exists(COMMANDS_LOG):
        with open(COMMANDS_LOG, 'r') as f:
            all_logs.extend(f.readlines())
            
    # Read errors
    if os.path.exists(ERRORS_LOG):
        with open(ERRORS_LOG, 'r') as f:
            all_logs.extend(f.readlines())
            
    # Sort by timestamp (approximate string sort works for ISO-ish format)
    # Filter out empty lines
    all_logs = [l.strip() for l in all_logs if l.strip()]
    all_logs.sort()
    
    # Return last N lines
    return all_logs[-lines:]

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['log_cmd', 'log_err', 'read'], help='Action to perform')
    parser.add_argument('message', nargs='?', help='Message to log')
    args = parser.parse_args()

    if args.action == 'log_cmd':
        if args.message:
            log_command(args.message)
        else:
            print("Error: Message required for log_cmd")
    elif args.action == 'log_err':
        if args.message:
            log_error(args.message)
        else:
            print("Error: Message required for log_err")
    elif args.action == 'read':
        logs = get_recent_logs()
        for l in logs:
            print(l)
