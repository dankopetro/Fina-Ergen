
import os
import sys
import datetime
import time

def get_config_dir():
    """Retorna el directorio de configuración universal ~/.config/Fina."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return os.path.join(xdg_config, "Fina")
    return os.path.expanduser("~/.config/Fina")

# Logs paths - RUTA UNIVERSAL: ~/.config/Fina/Logs/plugins
LOGS_DIR = os.path.join(get_config_dir(), "Logs", "plugins")
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

def tail_file(filename, lines=50):
    """Lee las últimas N líneas de un archivo de forma eficiente sin cargar todo en memoria."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            buffer_size = 1024 * 4
            data = b""
            pos = file_size
            
            while len(data.split(b'\n')) <= lines + 1 and pos > 0:
                seek_pos = max(0, pos - buffer_size)
                f.seek(seek_pos)
                chunk = f.read(pos - seek_pos)
                data = chunk + data
                pos = seek_pos
                
            decoded_lines = data.decode('utf-8', errors='ignore').splitlines()
            if not decoded_lines:
                return []
            return decoded_lines[-lines:] if len(decoded_lines) > lines else decoded_lines
    except (OSError, IOError):
        # Fallback para archivos especiales o errores de acceso
        try:
            with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                lines_list = f.readlines()
                if not lines_list:
                    return []
                return lines_list[-lines:] if len(lines_list) > lines else lines_list
        except Exception:
            return []

def get_recent_logs(lines=50):
    ensure_logs_dir()
    # Read end of files
    cmd_logs = tail_file(COMMANDS_LOG, lines)
    err_logs = tail_file(ERRORS_LOG, lines)
    
    # Merge, sort and clip again to be sure
    all_logs = cmd_logs + err_logs
    all_logs = [l.strip() for l in all_logs if l.strip()]
    all_logs.sort()
    
    return all_logs[-lines:] if len(all_logs) > lines else all_logs

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
