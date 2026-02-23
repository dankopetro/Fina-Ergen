import glob, os, re
target_dir = "/home/claudio/Descargas/Fina-Ergen/Fina-Plugins-Market/TVs"
files = glob.glob(os.path.join(target_dir, "**", "*.py"), recursive=True)

new_def = '''    def _load_settings(self) -> dict:
        """Loads configuration from ~/.config/Fina/settings.json robustly"""
        config_dir = None
        
        # 1. Prioridad: XDG_CONFIG_HOME
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = os.path.join(xdg_config, "Fina")
        else:
            # 2. Rescate: Home del usuario real
            try:
                from pathlib import Path
                config_dir = os.path.join(str(Path.home()), ".config", "Fina")
            except:
                config_dir = os.path.expanduser("~/.config/Fina")
                
        settings_path = os.path.join(config_dir, "settings.json")
        fallback_settings = os.path.join(os.path.dirname(os.path.dirname(self.plugin_dir)), "config", "settings.json")
        
        paths_to_check = [settings_path, fallback_settings]
        self.logger.info(f"🔎 TVPlugin buscando settings en: {paths_to_check}")
        
        import json
        for p in paths_to_check:
            if os.path.exists(p):
                try:
                    with open(p, 'r') as f:
                        self.logger.info(f"✅ TVPlugin: Cargando settings desde {p}")
                        return json.load(f)
                except Exception as e:
                    self.logger.error(f"Error leyendo settings {p}: {e}")

        self.logger.error(f"❌ CRÍTICO: No se encontró settings.json en NINGUNA ruta. (Probado: {paths_to_check})")
        return {"tvs": []}\n'''

for file in files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # match the whole def _load_settings up to the next def
    pattern = re.compile(r'^\s*def _load_settings.*?^            return json\.load\(f\).*?return \{"tvs": \[\]\}', re.MULTILINE | re.DOTALL)
    
    if pattern.search(content):
        # We need a highly robust regex to avoid matching multiple methods.
        pass

    # Actually we can just do a very simple string replacement.
    def replace_load_settings(text):
        lines = text.split('\n')
        out_lines = []
        in_load = False
        replaced = False
        
        for i, line in enumerate(lines):
            if re.match(r'^\s*def _load_settings\(self\)', line):
                in_load = True
                out_lines.append(new_def)
                replaced = True
                continue
                
            if in_load:
                # We stop ignoring when we hit another method or a non-indented string
                # We know the method ends usually around 'return {"tvs": []}'
                if 'return {"tvs": []}' in line:
                    in_load = False
                continue
                
            out_lines.append(line)
        return '\n'.join(out_lines) if replaced else None

    res = replace_load_settings(content)
    if res:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(res)
        print("Patched:", file)
    else:
        print("Not found in:", file)
