# Integración Fina Phoenix con Fina Principal

## Resumen
Este documento explica cómo integrar Fina Phoenix (sistema de timbre) con el asistente de voz Fina principal.

## Archivos Modificados

### ✅ Problemas Corregidos

1. **Binario brain portable** (`src-tauri/binaries/brain-x86_64-unknown-linux-gnu`)
   - Ahora usa rutas relativas en lugar de absolutas
   - Funciona desde cualquier ubicación de instalación

2. **Ruta de scripts corregida** (`plugins/doorbell/monitor.py`)
   - Ajustada para encontrar `scripts/start_hidden_system.sh`
   - Sube correctamente desde `test/fina-phoenix/plugins/doorbell/` hasta el root

3. **Función de colgar implementada** (`src/phoenix_brain.py`)
   - Método `hangup_doorbell()` agregado
   - Cierra ventana Scrcpy y servidor de streaming
   - Emite evento `doorbell-hangup`

4. **Listener de comandos stdin** (`src/phoenix_brain.py`)
   - Escucha comandos JSON desde stdin
   - Permite control externo desde Fina principal
   - Comandos soportados: `hangup`, `speak`

5. **Comando Tauri hangup** (`src-tauri/src/lib.rs`)
   - Comando `hangup_doorbell` registrado
   - Ejecuta ADB tap para colgar
   - Cierra procesos relacionados

6. **UI actualizada** (`src/App.vue`)
   - Botón de colgar llama a `invoke("hangup_doorbell")`
   - Manejo de errores implementado

## Integración con Fina Principal

### Opción 1: Script Standalone (Recomendado)

Para integrar el comando de voz "corta el timbre" en Fina principal:

1. **Agregar intent en `intents.json`:**
```json
{
  "intent": "hangup_doorbell",
  "patterns": [
    "corta el timbre",
    "cuelga el timbre",
    "termina la llamada",
    "cierra el timbre"
  ]
}
```

2. **Agregar handler en `main.py`:**
```python
def hangup_doorbell_cmd():
    """Colgar timbre de Fina Phoenix"""
    script_path = os.path.join(
        os.path.dirname(__file__), 
        "test/fina-phoenix/hangup_doorbell.py"
    )
    
    try:
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            speak("Timbre colgado")
        else:
            speak("No pude colgar el timbre")
            
    except Exception as e:
        logger.error(f"Error colgando timbre: {e}")
        speak("Error al colgar el timbre")
```

### Opción 2: Comunicación vía stdin

Si Ergen está corriendo como proceso hijo de Fina:

```python
# En Fina principal, mantener referencia al proceso Ergen
ergen_process = subprocess.Popen(
    ["python3", "test/fina-ergen/src/ergen_brain.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Para colgar:
def hangup_doorbell_cmd():
    command = json.dumps({"command": "hangup"}) + "\n"
    phoenix_process.stdin.write(command)
    phoenix_process.stdin.flush()
    speak("Colgando timbre")
```

## Comandos Disponibles

### Desde stdin (JSON):
```json
{"command": "hangup"}
{"command": "speak", "text": "Mensaje a decir"}
```

### Desde Tauri (Vue):
```javascript
await invoke("hangup_doorbell");
```

### Desde terminal:
```bash
python3 test/fina-phoenix/hangup_doorbell.py
```

## Eventos Emitidos

Phoenix emite eventos que pueden ser escuchados:

- `doorbell-ring`: Timbre detectado
- `doorbell-hangup`: Timbre colgado
- `fina-speak`: Solicitud de TTS

## Arquitectura

```
Fina Principal (main.py)
    ↓ (comando de voz)
    ↓
hangup_doorbell.py (script standalone)
    ↓ (ADB tap)
    ↓
Android/Waydroid (Tuya App)
    ↓
Timbre colgado ✓
```

## Testing

Probar la integración:

```bash
# 1. Iniciar Phoenix
cd .
npm run dev

# 2. En otra terminal, probar colgar manualmente
python3 hangup_doorbell.py

# 3. Verificar que ADB funciona
adb shell input tap 225 710
```

## Notas

- Las coordenadas del botón de colgar son: `(225, 710)`
- El servidor de streaming corre en puerto `8555`
- Waydroid debe estar corriendo para que ADB funcione
- El script `start_hidden_system.sh` se auto-ejecuta si Waydroid está apagado
