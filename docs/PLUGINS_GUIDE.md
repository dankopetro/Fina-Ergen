# Guía de Creación de Plugins para Fina

Esta es la arquitectura propuesta para extender las capacidades de Fina sin modificar el archivo `main.py`.

## Estructura de un Plugin
Cada plugin reside en su propia carpeta dentro de `plugins/`:

```text
plugins/
  └── light_control/
      ├── manifest.json
      └── plugin.py
```

### 1. El Manifiesto (`manifest.json`)
Define qué palabras activan el plugin y qué recursos necesita.

```json
{
  "name": "Control de Luces",
  "version": "1.0.0",
  "intent_label": "smart_home_lights",
  "phrases": [
    "enciende la luz",
    "apaga la luz",
    "pon las luces en rojo"
  ],
  "dependencies": ["tinytuya"]
}
```

### 2. El Código (`plugin.py`)
Debe seguir una interfaz estándar para que Fina lo cargue automáticamente.

```python
class FinaPlugin:
    def __init__(self, core_api):
        self.api = core_api # Permite al plugin usar speak(), listen(), etc.

    async def run(self, command, audio_data=None):
        # Lógica del plugin
        if "enciende" in command:
            # magia para encender luces
            self.api.speak("Encendiendo las luces ahora mismo.")
            return True
        return False
```

## Ventajas
- **Aislamiento**: Si un plugin tiene un error, Fina simplemente lo ignora y sigue funcionando.
- **Instalación fácil**: "Plug and Play". Solo arrastras la carpeta.
- **Limpieza**: `main.py` solo se encarga de escuchar y despachar al plugin correcto.
