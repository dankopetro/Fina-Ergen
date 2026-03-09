import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any

# Logger Setup
logger = logging.getLogger("PluginManager")
logger.setLevel(logging.DEBUG)
logger.info("--- PluginManager Inicializado ---")

class PluginManager:
    """Gestiona el descubrimiento, carga y ejecución de plugins"""
    
    def __init__(self, system_plugins_path: Optional[str] = None):
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
        
        self.loaded_plugins: Dict[str, Any] = {}
        self.plugin_processes: Dict[str, subprocess.Popen] = {}
        self._plugins_paths: Dict[str, Path] = {}
        
        logger.info(f"Plugin Manager inicializado.")
        logger.info(f"📂 Sistema: {self.system_plugins_dir}")
        logger.info(f"📂 Usuario: {self.user_plugins_dir}")
    
    def discover_plugins(self) -> List[str]:
        """
        Descubre plugins en las rutas configuradas (soporta categorías anidadas)
        
        Returns:
            Lista de nombres de plugins encontrados
        """
        self._plugins_paths.clear()
        
        def scan_dir(directory: Path):
            if not directory.exists():
                return
            
            # Buscamos archivos plugin.yaml hasta 3 niveles de profundidad
            # de forma que plugins/AirConditioning/Midea-Surrey/plugin.yaml sea detectado
            for yaml_path in list(directory.glob("plugin.yaml")) + \
                             list(directory.glob("*/plugin.yaml")) + \
                             list(directory.glob("*/*/plugin.yaml")) + \
                             list(directory.glob("*/*/*/plugin.yaml")):
                
                plugin_dir = yaml_path.parent
                plugin_name = plugin_dir.name
                
                # Prioridad: la carpeta que se escanee después sobrescribe.
                # El orden de scan_dir abajo define la prioridad (Usuario pisa a Sistema).
                self._plugins_paths[plugin_name] = plugin_dir

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
            config: Dict[str, Any] = { # type: ignore
                'name': plugin_name,
                'version': '0.0.1 (legacy)',
                'description': 'Entorno de plugin legacy',
                'path': str(plugin_path)
            }
            # Intentar detectar el script principal si se llama como la carpeta
            if (plugin_path / f"{plugin_name}.py").exists():
                config['main'] = f"{plugin_name}.py"
                
            self.loaded_plugins[plugin_name] = config
            return True
            
        try:
            try:
                import yaml
            except ImportError:
                # Intento de rescate si no está en el venv principal
                try: 
                    import PyYAML as yaml # type: ignore
                except: return False
                

            with open(yaml_path, 'r', encoding='utf-8') as f:
                config_raw = yaml.safe_load(f)
                
            config: Dict[str, Any] = config_raw if isinstance(config_raw, dict) else {} # type: ignore
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
        parts: List[str] = action_cmd.split(' ')
        script_rel = parts[0]
        args: List[str] = list(parts[1:]) if len(parts) > 1 else [] # type: ignore
        
        # El linter a veces se queja de script_path si Path() falla
        try:
            script_path = Path(config['path']) / script_rel
        except:
            return False
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
