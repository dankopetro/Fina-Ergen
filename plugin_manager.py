#!/usr/bin/env python3
"""
Plugin Manager para Fina
Gestiona la carga, descarga e instalación de plugins
"""

import os
import json
import subprocess
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class PluginManager:
    """Gestor de plugins para Fina"""
    
    def __init__(self, plugins_dir: str = None):
        """
        Inicializa el gestor de plugins con soporte para rutas de Sistema y Usuario
        """
        self.root_dir = Path(__file__).parent.absolute()
        
        def get_config_dir():
            xdg_config = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config:
                return os.path.join(xdg_config, "Fina")
            try:
                from pathlib import Path
                return os.path.join(str(Path.home()), ".config", "Fina")
            except:
                return os.path.expanduser("~/.config/Fina")

        config_dir = Path(get_config_dir())
        
        # 1. Carpeta de Sistema (dentro del proyecto/AppImage)
        self.system_plugins_dir = self.root_dir / "plugins"
        
        # 2. Carpeta de Usuario (Persistente en .config)
        self.user_plugins_dir = config_dir / "plugins"
        
        # Asegurar que existan
        self.system_plugins_dir.mkdir(exist_ok=True)
        self.user_plugins_dir.mkdir(parents=True, exist_ok=True)
        
        # Para compatibilidad con código viejo que use self.plugins_dir, apuntamos a la de sistema
        self.plugins_dir = self.system_plugins_dir
        
        self.loaded_plugins: Dict[str, dict] = {}
        self.plugin_processes: Dict[str, subprocess.Popen] = {}
        
        logger.info(f"Plugin Manager (Universal) inicializado.")
        logger.info(f"📂 Sistema: {self.system_plugins_dir}")
        logger.info(f"📂 Usuario: {self.user_plugins_dir}")
    
    def discover_plugins(self) -> List[str]:
        """
        Descubre plugins en ambas carpetas de forma recursiva (hasta 3 niveles). 
        Si hay colisión de nombres (basado en el nombre de la carpeta), 
        el de Usuario tiene prioridad.
        """
        self._plugins_paths = {} # name -> Path
        
        def scan_dir(base_path):
            if not base_path.exists():
                return
            
            # Buscamos todos los plugin.yaml o plugin.json recursivamente
            # Limitamos a rglob para encontrar los archivos de configuración
            for config_file in list(base_path.rglob("plugin.yaml")) + list(base_path.rglob("plugin.json")):
                plugin_dir = config_file.parent
                plugin_name = plugin_dir.name
                
                # Guardamos la ruta. Al escanear sistema primero y usuario después,
                # usuario naturalmente sobrescribirá a sistema si tienen el mismo nombre de carpeta.
                self._plugins_paths[plugin_name] = plugin_dir

        # Escanear primero Sistema, luego Usuario
        scan_dir(self.system_plugins_dir)
        scan_dir(self.user_plugins_dir)
        
        return list(self._plugins_paths.keys())
    
    def _get_plugin_path(self, plugin_name: str) -> Optional[Path]:
        """Busca la ruta real de un plugin usando el mapa de descubrimiento"""
        # Si no hemos descubierto aún, lo hacemos
        if not hasattr(self, '_plugins_paths') or not self._plugins_paths:
            self.discover_plugins()
            
        return self._plugins_paths.get(plugin_name)

    def load_plugin_metadata(self, plugin_name: str) -> Optional[dict]:
        """
        Carga los metadatos buscando en ambas rutas posibles
        """
        plugin_path = self._get_plugin_path(plugin_name)
        if not plugin_path:
            logger.error(f"No se encontró ruta para plugin {plugin_name}")
            return None
        
        yaml_file = plugin_path / "plugin.yaml"
        json_file = plugin_path / "plugin.json"
        
        data = None
        try:
            if yaml_file.exists():
                # Intentamos usar PyYAML si está disponible
                try:
                    import yaml
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                except ImportError:
                    logger.error(f"PyYAML no instalado. No se puede leer {yaml_file}")
                    return None
            elif json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parseando JSON de {plugin_name}: {e}")
                    return None
            else:
                logger.error(f"No se encontró archivo de configuración para {plugin_name}")
                return None
                
            # Agregar ruta del plugin
            data['_path'] = str(plugin_path)
            return data

        except Exception as e:
            logger.error(f"Error cargando metadata de {plugin_name}: {e}")
            return None
    
    def check_requirements(self, plugin_name: str) -> tuple[bool, List[str]]:
        """
        Verifica que se cumplan los requisitos del plugin
        """
        metadata = self.load_plugin_metadata(plugin_name)
        if not metadata:
            return False, ["No se pudo cargar metadata"]
        
        missing = []
        requirements = metadata.get('requirements', {})
        
        # Verificar comandos del sistema
        system_reqs = requirements.get('system', [])
        for cmd in system_reqs:
            if not self._command_exists(cmd):
                missing.append(f"Sistema: {cmd}")
        
        # Verificar versión de Python
        python_req = requirements.get('python', [])
        if python_req:
            # Simplificado
            pass
        
        # Verificar paquetes Python
        python_packages = requirements.get('packages', [])
        for package in python_packages:
            if not self._package_exists(package):
                missing.append(f"Python package: {package}")
        
        return len(missing) == 0, missing
    
    def install_plugin(self, plugin_name: str, auto_deps: bool = True) -> bool:
        """
        Instala un plugin (ejecuta setup.sh si existe)
        """
        metadata = self.load_plugin_metadata(plugin_name)
        if not metadata:
            return False
        
        plugin_path = Path(metadata['_path'])
        
        # Ejecutar script de setup si existe
        setup_script = metadata.get('scripts', {}).get('setup')
        if setup_script:
            setup_path = plugin_path / setup_script
            if setup_path.exists():
                logger.info(f"Ejecutando setup para {plugin_name}...")
                try:
                    result = subprocess.run(
                        ['bash', str(setup_path)],
                        cwd=str(plugin_path),
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    return result.returncode == 0
                except Exception as e:
                    logger.error(f"Error setup {plugin_name}: {e}")
                    return False
        
        return True
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Carga un plugin en memoria (instancia si es Clase Python)
        """
        if plugin_name in self.loaded_plugins:
            return True
        
        metadata = self.load_plugin_metadata(plugin_name)
        if not metadata:
            return False
        
        # Verificar requisitos
        ok, missing = self.check_requirements(plugin_name)
        if not ok:
            logger.error(f"Plugin {plugin_name} faltan requisitos: {missing}")
            return False
        
        self.loaded_plugins[plugin_name] = metadata
        
        # --- CARGA DINÁMICA DE CLASE PYTHON (NUEVO) ---
        if "main_class" in metadata and "main_file" in metadata:
            try:
                plugin_path = Path(metadata['_path'])
                sys.path.insert(0, str(plugin_path)) # Añadir al path
                
                module_name = metadata["main_file"].replace(".py", "")
                spec = importlib.util.spec_from_file_location(module_name, plugin_path / metadata["main_file"])
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, metadata["main_class"]):
                        cls = getattr(module, metadata["main_class"])
                        # Instanciamos pasando el manager como contexto
                        instance = cls(self)
                        
                        # Guardamos la instancia
                        self.loaded_plugins[plugin_name]['_instance'] = instance
                        
                        # Si tiene método verify_scripts, ejecutarlo
                        if hasattr(instance, 'verify_scripts'):
                            instance.verify_scripts()
                            
                        logger.info(f"✓ Plugin {plugin_name} (Clase Python) cargado e instanciado.")
                    else:
                        logger.error(f"Clase {metadata['main_class']} no encontrada en {module_name}")
            except Exception as e:
                logger.error(f"Error instanciando plugin {plugin_name}: {e}")
                import traceback
                traceback.print_exc()
                return False
                
        logger.info(f"✓ Plugin {plugin_name} cargado")
        return True
    
    def start_plugin(self, plugin_name: str) -> bool:
        """
        Inicia el proceso monitor de un plugin
        
        Args:
            plugin_name: Nombre del plugin
            
        Returns:
            True si se inició exitosamente
        """
        if plugin_name not in self.loaded_plugins:
            logger.error(f"Plugin {plugin_name} no está cargado")
            return False
        
        if plugin_name in self.plugin_processes:
            logger.warning(f"Plugin {plugin_name} ya está corriendo")
            return True
        
        metadata = self.loaded_plugins[plugin_name]
        plugin_path = Path(metadata['_path'])
        
        # Obtener script monitor
        monitor_script = metadata.get('scripts', {}).get('monitor')
        if not monitor_script:
            logger.warning(f"Plugin {plugin_name} no tiene script monitor")
            return True  # No es error, simplemente no tiene monitor
        
        monitor_path = plugin_path / monitor_script
        if not monitor_path.exists():
            logger.error(f"Script monitor no encontrado: {monitor_path}")
            return False
        
        try:
            # Iniciar proceso
            process = subprocess.Popen(
                [sys.executable, '-u', str(monitor_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            self.plugin_processes[plugin_name] = process
            logger.info(f"✓ Plugin {plugin_name} iniciado (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Error iniciando plugin {plugin_name}: {e}")
            return False
    
    def stop_plugin(self, plugin_name: str) -> bool:
        """
        Detiene el proceso de un plugin
        
        Args:
            plugin_name: Nombre del plugin
            
        Returns:
            True si se detuvo exitosamente
        """
        if plugin_name not in self.plugin_processes:
            logger.warning(f"Plugin {plugin_name} no está corriendo")
            return True
        
        process = self.plugin_processes[plugin_name]
        
        try:
            process.terminate()
            process.wait(timeout=5)
            del self.plugin_processes[plugin_name]
            logger.info(f"✓ Plugin {plugin_name} detenido")
            return True
        except subprocess.TimeoutExpired:
            logger.warning(f"Plugin {plugin_name} no respondió a SIGTERM, usando SIGKILL")
            process.kill()
            del self.plugin_processes[plugin_name]
            return True
        except Exception as e:
            logger.error(f"Error deteniendo plugin {plugin_name}: {e}")
            return False
    
    def get_plugin_intents(self, plugin_name: str) -> List[dict]:
        """
        Obtiene los intents del plugin (Normalizado a Lista de dicts)
        Returns: [{'name': '...', 'patterns': [...]}, ...]
        """
        if plugin_name not in self.loaded_plugins:
            return []
            
        meta = self.loaded_plugins[plugin_name]
        intents = []
        
        # 1. Instancia Python (Prioridad)
        if '_instance' in meta:
            try:
                raw_intents = meta['_instance'].get_intents()
                # Normalizar si devuelve dict {name: [patterns]}
                if isinstance(raw_intents, dict):
                    for name, patterns in raw_intents.items():
                        intents.append({
                            'name': name,
                            'patterns': patterns
                        })
                elif isinstance(raw_intents, list):
                    intents = raw_intents
            except Exception as e:
                logger.error(f"Error obteniendo intents dinámicos de {plugin_name}: {e}")
        
        # 2. Definición Estática (YAML/JSON)
        # Si la clase no devolvió nada o falló, o no hay clase, usamos lo del YAML
        if not intents:
            intents = meta.get('intents', [])
            
        return intents

    def execute_intent(self, plugin_name: str, intent_name: str, command: str, **kwargs):
        """
        Ejecuta un intent. 
        - Si es plugin con clase, llama a handle_intent.
        - Si es plugin script (legacy), intenta ejecutar_plugin_action si se pasa el script... 
          pero idealmente main.py maneja eso.
        """
        if plugin_name not in self.loaded_plugins: return None
        meta = self.loaded_plugins[plugin_name]
        
        if '_instance' in meta:
            return meta['_instance'].handle_intent(intent_name, command, **kwargs)
        
        logger.warning(f"Plugin {plugin_name} no tiene instancia para ejecutar intent {intent_name} dinámicamente.")
        return None

    def execute_plugin_action(self, plugin_name: str, action_command: str) -> bool:
        """
        Ejecuta un comando o script asociado a un plugin
        """
        if plugin_name not in self.loaded_plugins:
            return False
            
        metadata = self.loaded_plugins[plugin_name]
        plugin_path = Path(metadata['_path'])
        
        try:
            # Si el comando es una ruta a un archivo dentro del plugin
            potential_script = plugin_path / action_command
            if potential_script.exists():
                subprocess.Popen(['bash' if action_command.endswith('.sh') else sys.executable, str(potential_script)],
                               cwd=str(plugin_path),
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            else:
                # Ejecutar como comando de shell
                subprocess.Popen(action_command, shell=True, cwd=str(plugin_path),
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            logger.error(f"Error ejecutando acción de {plugin_name}: {e}")
            return False
    
    def list_plugins(self) -> List[dict]:
        """
        Lista todos los plugins disponibles con su metadata
        
        Returns:
            Lista de diccionarios con info de plugins
        """
        plugins = []
        for plugin_name in self.discover_plugins():
            metadata = self.load_plugin_metadata(plugin_name)
            if metadata:
                plugins.append({
                    'name': plugin_name,
                    'version': metadata.get('version', 'unknown'),
                    'description': metadata.get('description', ''),
                    'author': metadata.get('author', 'unknown'),
                    'category': metadata.get('category', 'other'),
                    'loaded': plugin_name in self.loaded_plugins,
                    'running': plugin_name in self.plugin_processes
                })
        
        return plugins
    
    def _command_exists(self, cmd: str) -> bool:
        """Verifica si un comando existe en el sistema"""
        try:
            subprocess.run(
                ['which', cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _package_exists(self, package: str) -> bool:
        """Verifica si un paquete Python está instalado"""
        try:
            importlib.import_module(package)
            return True
        except ImportError:
            return False
    
    def cleanup(self):
        """Detiene todos los plugins y limpia recursos"""
        logger.info("Limpiando Plugin Manager...")
        for plugin_name in list(self.plugin_processes.keys()):
            self.stop_plugin(plugin_name)


# CLI para testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    manager = PluginManager()
    
    print("🔌 Fina Plugin Manager")
    print("=" * 50)
    
    # Descubrir plugins
    plugins = manager.discover_plugins()
    print(f"\nPlugins encontrados: {len(plugins)}")
    
    for plugin_name in plugins:
        print(f"\n📦 {plugin_name}")
        metadata = manager.load_plugin_metadata(plugin_name)
        if metadata:
            print(f"   Versión: {metadata.get('version')}")
            print(f"   Autor: {metadata.get('author')}")
            print(f"   Descripción: {metadata.get('description')}")
            
            # Verificar requisitos
            ok, missing = manager.check_requirements(plugin_name)
            if ok:
                print("   ✓ Requisitos cumplidos")
            else:
                print("   ✗ Requisitos faltantes:")
                for item in missing:
                    print(f"     - {item}")
