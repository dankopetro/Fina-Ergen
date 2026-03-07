import os
import sys
import subprocess
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger("PluginManager")

class PluginManager:
    """Gestiona el descubrimiento, carga y ejecución de plugins"""
    
    def __init__(self, system_plugins_path: str = None):
        """
        Inicializa el Plugin Manager
        
        Args:
            system_plugins_path: Ruta a los plugins del sistema (opcional)
        """
        # Determinar rutas de plugins
        self.base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        
        # 1. Carpeta del Sistema (dentro de la repo/instalación)
        if system_plugins_path:
            self.system_plugins_dir = Path(system_plugins_path)
        else:
            self.system_plugins_dir = self.base_dir / "plugins"
            
        # 2. Carpeta de Usuario (Persistente en .config)
        # Buscamos en ~/.config/Fina/plugins
        try:
            from utils import get_config_dir
            config_dir = Path(get_config_dir())
        except:
            config_dir = Path(os.path.expanduser("~/.config/Fina"))
        
        self.user_plugins_dir = config_dir / "plugins"
        
        # Asegurar que existan
        self.system_plugins_dir.mkdir(exist_ok=True)
        self.user_plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Para compatibilidad con código viejo que use self.plugins_dir, apuntamos a la de sistema
        self.plugins_dir = self.system_plugins_dir
        
        self.loaded_plugins: Dict[str, dict] = {}
        self.plugin_processes: Dict[str, subprocess.Popen] = {}
        
        logger.info(f"Plugin Manager inicializado.")
        logger.info(f"📂 Sistema: {self.system_plugins_dir}")
        logger.info(f"📂 Usuario: {self.user_plugins_dir}")
    
    def discover_plugins(self) -> List[str]:
        """
        Descubre plugins en las rutas configuradas
        
        Returns:
            Lista de nombres de plugins encontrados
        """
        self._plugins_paths = {} # Nombre -> Path absoluto
        
        def scan_dir(directory: Path):
            if not directory.exists():
                return
            
            for item in directory.iterdir():
                if item.is_dir():
                    # Es un plugin si tiene plugin.yaml o un script principal
                    plugin_name = item.name
                    # Prioridad: la carpeta que se escanee después sobrescribe.
                    # El orden de scan_dir abajo define la prioridad.
                    self._plugins_paths[plugin_name] = item

        # Escanear primero Sistema, luego Usuario para que el usuario tenga prioridad
        scan_dir(self.system_plugins_dir)
        scan_dir(self.user_plugins_dir)
        
        return list(self._plugins_paths.keys())
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Carga la configuración de un plugin
        """
        if plugin_name not in self._plugins_paths:
            return False
            
        plugin_path = self._plugins_paths[plugin_name]
        yaml_path = plugin_path / "plugin.yaml"
        
        if not yaml_path.exists():
            return False
            
        try:
            import yaml
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                
            config['path'] = str(plugin_path)
            self.loaded_plugins[plugin_name] = config
            return True
        except Exception as e:
            logger.error(f"Error cargando plugin {plugin_name}: {e}")
            return False
            
    def start_plugin(self, plugin_name: str) -> bool:
        """
        Inicia el proceso monitor de un plugin (si tiene uno)
        """
        if plugin_name not in self.loaded_plugins:
            return False
            
        config = self.loaded_plugins[plugin_name]
        monitor_script = config.get('monitor')
        
        if not monitor_script:
            return False
            
        script_path = Path(config['path']) / monitor_script
        if not script_path.exists():
            logger.warning(f"No se encontró el monitor {monitor_script} para el plugin {plugin_name}")
            return False
            
        try:
            # Ejecutar plugin como proceso hijo
            # Usamos el mismo ejecutable de python que el actual
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=config['path']
            )
            
            self.plugin_processes[plugin_name] = process
            return True
        except Exception as e:
            logger.error(f"Error iniciando proceso del plugin {plugin_name}: {e}")
            return False

    def execute_plugin_action(self, plugin_name: str, action_cmd: str) -> bool:
        """
        Ejecuta un script de acción de un plugin
        """
        if plugin_name not in self.loaded_plugins:
            # Intentar cargarlo on-the-fly si existe el path pero no está en loaded
            if plugin_name in self._plugins_paths:
                self.load_plugin(plugin_name)
            else:
                return False
                
        config = self.loaded_plugins[plugin_name]
        
        # Simple ejecución de script
        # El action_cmd suele ser algo como "scripts/clima.py --status"
        parts = action_cmd.split(' ')
        script_rel = parts[0]
        args = parts[1:]
        
        script_path = Path(config['path']) / script_rel
        if not script_path.exists():
            return False
            
        try:
            subprocess.Popen([sys.executable, str(script_path)] + args, cwd=config['path'])
            return True
        except:
            return False

    def get_plugin_intents(self, plugin_name: str) -> List[dict]:
        """Retorna los intents definidos en el plugin.yaml"""
        if plugin_name not in self.loaded_plugins:
            return []
        return self.loaded_plugins[plugin_name].get('intents', [])

    def list_plugins(self) -> List[dict]:
        """Lista plugins cargados y su estado"""
        result = []
        for name, config in self.loaded_plugins.items():
            result.append({
                'name': name,
                'version': config.get('version', '0.0.1'),
                'description': config.get('description', ''),
                'running': name in self.plugin_processes and self.plugin_processes[name].poll() is None
            })
        return result

    def cleanup(self):
        """Detiene todos los procesos de plugins"""
        for name, process in self.plugin_processes.items():
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                process.kill()
        self.plugin_processes.clear()

    # --- NUEVOS MÉTODOS PARA INTEGRACIÓN PYTHON DIRECTA ---
    
    def execute_intent(self, plugin_name: str, intent_name: str, user_input: str) -> Optional[str]:
        """
        Ejecuta un intent directamente si el plugin tiene una clase Python vinculada
        """
        # Por ahora es un placeholder para futura expansión
        # En una arquitectura más avanzada, cargaríamos una clase del plugin
        return None
