import os
import glob
import re

def get_universal_prefix():
    return '''
    config_dir = os.environ.get("XDG_CONFIG_HOME")
    if config_dir:
        config_dir = os.path.join(config_dir, "Fina")
    else:
        config_dir = os.path.expanduser("~/.config/Fina")
    '''

files = []
# Gather all python files
for root, _, filenames in os.walk("/home/claudio/Descargas/Fina-Ergen/market_check"):
    for f in filenames:
        if f.endswith(".py"):
            files.append(os.path.join(root, f))

fixes = 0
for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    # Check for direct os.path.join(PROJECT_ROOT, "config", "settings.json")
    if 'os.path.join(PROJECT_ROOT, "config", "settings.json")' in content:
        # replace with universal paths
        replacement = '''
    config_dir = os.environ.get("XDG_CONFIG_HOME")
    if config_dir:
        config_dir = os.path.join(config_dir, "Fina")
    else:
        config_dir = os.path.expanduser("~/.config/Fina")
    paths = [os.path.join(config_dir, "settings.json"), os.path.join(PROJECT_ROOT, "config", "settings.json")]
        '''
        
        # Replace the paths definition
        content = re.sub(
            r'paths\s*=\s*\[\s*os\.path\.join\(PROJECT_ROOT,\s*"config",\s*"settings\.json"\)\s*\]',
            replacement.strip(),
            content
        )
        changed = True

    # SETTINGS_FILE = "./config/settings.json"
    if 'SETTINGS_FILE = "./config/settings.json"' in content or 'SETTINGS_FILE = os.path.join(PROJECT_ROOT, "config", "settings.json")' in content:
        # Some scripts just declare it at module level, this requires slightly different handling
        pass
        
    if changed:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        fixes += 1
        print("Patched settings path in:", file)

print(f"Total fixes: {fixes}")
