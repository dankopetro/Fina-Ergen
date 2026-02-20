#!/usr/bin/env python3
"""
Integración de Plugins con Fina
Este módulo conecta el Plugin Manager con el sistema principal de Fina
"""

import json
import logging
import threading
import socket
import re
from typing import Dict, Optional, Callable
from plugin_manager import PluginManager

logger = logging.getLogger("FinaPlugins")

class FinaPluginIntegration:
    """Integra el sistema de plugins con Fina"""
    
    def __init__(self, speak_callback: Callable = None):
        """
        Inicializa la integración de plugins
        
        Args:
            speak_callback: Función para hacer que Fina hable
        """
        self.plugin_manager = PluginManager()
        self.speak = speak_callback or (lambda x: print(f"[FINA]: {x}"))
        self.plugin_intents: Dict[str, dict] = {}
        self.event_listeners: Dict[str, list] = {}
        self.stop_event = threading.Event()
        self.udp_thread = None
        
        logger.info("Integración de plugins inicializada")
        
        # Iniciar servidor UDP para eventos externos (como clima.py)
        self._start_udp_server()
    
    def _start_udp_server(self, port=5005):
        """Inicia un servidor UDP para escuchar eventos de plugins efímeros"""
        def listen():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(("127.0.0.1", port))
                sock.settimeout(1.0)
                logger.info(f"Servidor UDP de eventos iniciado en puerto {port}")
                
                while not self.stop_event.is_set():
                    try:
                        data, addr = sock.recvfrom(4096)
                        try:
                            msg = json.loads(data.decode())
                            event_name = msg.get("event")
                            payload = msg.get("payload")
                            
                            if event_name:
                                self._handle_plugin_event("udp_external", {
                                    "type": "event",
                                    "name": event_name,
                                    "payload": payload
                                })
                        except json.JSONDecodeError:
                            logger.warning(f"UDP data malformada de {addr}")
                    except socket.timeout:
                        continue
                    except Exception as e:
                        logger.error(f"Error en loop UDP: {e}")
            except Exception as e:
                logger.error(f"No se pudo iniciar servidor UDP en puerto {port}: {e}")
            finally:
                sock.close()
        
        self.udp_thread = threading.Thread(target=listen, daemon=True)
        self.udp_thread.start()
    
    def initialize_plugins(self, auto_start: bool = True):
        """
        Descubre, carga e inicia todos los plugins
        
        Args:
            auto_start: Si es True, inicia automáticamente los plugins
        """
        logger.info("Descubriendo plugins...")
        plugins = self.plugin_manager.discover_plugins()
        
        if not plugins:
            logger.info("No se encontraron plugins")
            return
        
        logger.info(f"Encontrados {len(plugins)} plugins: {', '.join(plugins)}")
        
        for plugin_name in plugins:
            try:
                # Cargar plugin
                if self.plugin_manager.load_plugin(plugin_name):
                    logger.info(f"✓ Plugin '{plugin_name}' cargado")
                    
                    # Registrar intents del plugin
                    self._register_plugin_intents(plugin_name)
                    
                    # Iniciar plugin si tiene monitor
                    if auto_start:
                        if self.plugin_manager.start_plugin(plugin_name):
                            logger.info(f"✓ Plugin '{plugin_name}' iniciado")
                            
                            # Iniciar listener de eventos
                            self._start_plugin_listener(plugin_name)
                else:
                    logger.warning(f"No se pudo cargar plugin '{plugin_name}'")
                    
            except Exception as e:
                logger.error(f"Error inicializando plugin '{plugin_name}': {e}")
    
    def _register_plugin_intents(self, plugin_name: str):
        """Registra los intents de un plugin"""
        intents = self.plugin_manager.get_plugin_intents(plugin_name)
        
        for intent in intents:
            intent_name = intent.get('name')
            if intent_name:
                self.plugin_intents[intent_name] = {
                    'plugin': plugin_name,
                    'patterns': intent.get('patterns', []),
                    'response': intent.get('response', ''),
                    'action': intent.get('action', '')
                }
                logger.debug(f"Intent registrado: {intent_name} -> {plugin_name}")
    
    def _start_plugin_listener(self, plugin_name: str):
        """Inicia un hilo para escuchar eventos de un plugin"""
        if plugin_name not in self.plugin_manager.plugin_processes:
            return
        
        process = self.plugin_manager.plugin_processes[plugin_name]
        
        def listen():
            """Escucha stdout del plugin"""
            try:
                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break
                    
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        self._handle_plugin_event(plugin_name, data)
                    except json.JSONDecodeError:
                        logger.debug(f"[{plugin_name}] {line}")
                        
            except Exception as e:
                logger.error(f"Error escuchando plugin {plugin_name}: {e}")
        
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()
        logger.debug(f"Listener iniciado para plugin {plugin_name}")
    
    def _handle_plugin_event(self, plugin_name: str, data: dict):
        """Maneja eventos emitidos por plugins"""
        event_type = data.get('type')
        
        if event_type == 'log':
            # Log del plugin
            level = data.get('level', 'info')
            message = data.get('message', '')
            log_func = getattr(logger, level, logger.info)
            log_func(f"[{plugin_name}] {message}")
            
        elif event_type == 'event':
            # Evento del plugin
            event_name = data.get('name')
            payload = data.get('payload', {})
            
            logger.info(f"Evento de {plugin_name}: {event_name}")
            
            # Manejar eventos especiales
            if event_name == 'fina-speak':
                # Plugin solicita TTS
                if isinstance(payload, dict):
                    text = payload.get('text', '')
                    sink = payload.get('sink')
                else:
                    text = str(payload)
                    sink = None
                
                if text:
                    # Pasar el sink a la función speak si está disponible
                    try:
                        # Si self.speak es el objeto lambda de main.py, intentamos pasar el sink
                        # Como en main.py pasamos: lambda text: speak(text, DEFAULT_VOICE)
                        # Necesitamos que la lambda acepte un argumento opcional o invocar directamente.
                        # Para no romper la lambda actual si no acepta sink, usamos inspección o simplemente
                        # confiamos en que si es una función compleja la llamaremos bien.
                        self.speak(text, sink=sink)
                    except TypeError:
                        # Fallback por si la callback no acepta sink
                        self.speak(text)
            
            elif event_name == 'doorbell-ring':
                # Timbre detectado
                self.speak("Alguien está en la puerta")
                logger.info("🔔 Timbre detectado")
            
            elif event_name == 'doorbell-hangup':
                # Timbre colgado
                logger.info("Timbre colgado")
            
            # Notificar a listeners registrados
            self._notify_event_listeners(event_name, payload)
    
    def _notify_event_listeners(self, event_name: str, payload: dict):
        """Notifica a los listeners de un evento"""
        if event_name in self.event_listeners:
            for callback in self.event_listeners[event_name]:
                try:
                    callback(payload)
                except Exception as e:
                    logger.error(f"Error en listener de {event_name}: {e}")
    
    def register_event_listener(self, event_name: str, callback: Callable):
        """
        Registra un callback para escuchar eventos de plugins
        
        Args:
            event_name: Nombre del evento
            callback: Función a llamar cuando ocurra el evento
        """
        if event_name not in self.event_listeners:
            self.event_listeners[event_name] = []
        
        self.event_listeners[event_name].append(callback)
        logger.debug(f"Listener registrado para evento: {event_name}")
    
    def handle_intent(self, intent_name: str, user_input: str = "") -> bool:
        """
        Maneja un intent de plugin
        
        Args:
            intent_name: Nombre del intent
            user_input: Texto del usuario (opcional)
            
        Returns:
            True si el intent fue manejado
        """
        if intent_name not in self.plugin_intents:
            return False
        
        intent_info = self.plugin_intents[intent_name]
        plugin_name = intent_info['plugin']
        action_script = intent_info['action']
        response = intent_info['response']
        
        # --- NUEVA ESTRATEGIA: PRIORIDAD A CLASE PYTHON ---
        # Si el plugin tiene una instancia cargada, llamamos a su handle_intent directamente
        plugin_result = self.plugin_manager.execute_intent(plugin_name, intent_name, user_input)
        
        if plugin_result:
            # Si el plugin devuelve un mensaje, lo decimos
            if isinstance(plugin_result, str):
                self.speak(plugin_result)
            return True

        # --- FALLBACK: ESTRATEGIA LEGACY (SCRIPTS) ---
        # Responder al usuario (si hay respuesta estática definida)
        if response:
            self.speak(response)
        
        # Ejecutar acción del plugin (si hay script definido)
        if action_script:
            # Reemplazar variables en el script de acción
            final_action = action_script
            
            # Extraer temperatura si existe
            temp_match = re.search(r'(\d+)', user_input)
            if temp_match:
                final_action = final_action.replace("{temp}", temp_match.group(1))
            
            # Determinar estado (on/off)
            if any(word in user_input for word in ["prender", "encender", "activa", "poner", "activar", "on"]):
                final_action = final_action.replace("{state}", "on")
            elif any(word in user_input for word in ["apagar", "detener", "quitar", "desactivar", "off"]):
                final_action = final_action.replace("{state}", "off")
            
            success = self.plugin_manager.execute_plugin_action(
                plugin_name,
                final_action
            )
            
            if success:
                logger.info(f"Acción de plugin ejecutada: {plugin_name}/{final_action}")
                return True
            else:
                logger.error(f"Error ejecutando acción de plugin: {plugin_name}/{final_action}")
                return False
        
        return False # No se manejó ni por clase ni por script
    
    def match_plugin_intent(self, user_input: str) -> Optional[str]:
        """
        Busca si el input del usuario coincide con algún intent de plugin
        
        Args:
            user_input: Texto del usuario
            
        Returns:
            Nombre del intent si hay match, None si no
        """
        user_input_lower = user_input.lower().strip()
        
        for intent_name, intent_info in self.plugin_intents.items():
            patterns = intent_info.get('patterns', [])
            
            for pattern in patterns:
                if pattern.lower() in user_input_lower:
                    logger.debug(f"Match encontrado: '{user_input}' -> {intent_name}")
                    return intent_name
        
        return None
    
    def get_loaded_plugins(self) -> list:
        """Retorna lista de plugins cargados"""
        return self.plugin_manager.list_plugins()
    
    def cleanup(self):
        """Limpia recursos de plugins"""
        logger.info("Limpiando plugins...")
        self.stop_event.set()
        self.plugin_manager.cleanup()


# Función helper para integrar con main.py
def setup_plugins(speak_callback: Callable = None) -> FinaPluginIntegration:
    """
    Configura el sistema de plugins para Fina
    
    Args:
        speak_callback: Función de TTS de Fina
        
    Returns:
        Instancia de FinaPluginIntegration
    """
    integration = FinaPluginIntegration(speak_callback)
    integration.initialize_plugins(auto_start=True)
    return integration


# Testing
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    def test_speak(text):
        print(f"🗣️ FINA: {text}")
    
    # Inicializar
    integration = setup_plugins(test_speak)
    
    # Mostrar plugins cargados
    print("\n📦 Plugins cargados:")
    for plugin in integration.get_loaded_plugins():
        status = "🟢" if plugin['running'] else "⚪"
        print(f"{status} {plugin['name']} v{plugin['version']} - {plugin['description']}")
    
    # Mostrar intents disponibles
    print("\n🎤 Comandos de voz de plugins:")
    for intent_name, intent_info in integration.plugin_intents.items():
        print(f"\n  {intent_name}:")
        for pattern in intent_info['patterns']:
            print(f"    - \"{pattern}\"")
    
    # Simular comando
    print("\n🧪 Probando comando 'hola mundo'...")
    intent = integration.match_plugin_intent("hola mundo")
    if intent:
        integration.handle_intent(intent)
    
    # Mantener vivo para escuchar eventos
    print("\n👂 Escuchando eventos de plugins... (Ctrl+C para salir)")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo...")
        integration.cleanup()
