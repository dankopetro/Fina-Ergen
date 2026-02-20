# Especificación Técnica: Sistema de Intents Dinámicos para Fina Ergen

**Objetivo:** Permitir que Fina reconozca y controle dispositivos descubiertos automáticamente o configurados por el usuario sin necesidad de editar manualmente archivos de configuración o intents estáticos.

**Prioridad:** ALTA (Bloqueante para release de usuario final)

---

## 1. El Problema Actual
Actualmente, los intents son estáticos (`intents.json`). Si un usuario compra una nueva TV y la llama "TV Quincho", Fina no sabrá qué hacer con el comando "Enciende la TV del Quincho" a menos que un desarrollador agregue manualmente frases al JSON y lógica al plugin.

## 2. La Solución: Context-Aware Intent Injection

Necesitamos un sistema que:
1.  **Escanee la red** en busca de dispositivos compatibles (TVs, Luces, Enchufes).
2.  **Permita al usuario nombrar** estos dispositivos vía voz o UI ("Esta es la tele de la cocina").
3.  **Genere "Intents Virtuales"** en tiempo de ejecución.

### Workflow del Usuario (Ejemplo)
1.  **Usuario:** "Fina, busca dispositivos."
2.  **Fina:** (Escanea red) "Encontré un dispositivo Chromecast en 192.168.1.50. ¿Cómo quieres llamarlo?"
3.  **Usuario:** "Ponle Tele de la Cocina."
4.  **Fina:** *Guarda configuración y recarga vocabulario.*
5.  **Usuario:** "Enciende la Tele de la Cocina."
6.  **Fina:** (Reconoce entidad 'Tele de la Cocina' -> Mapea a IP -> Ejecuta) "Encendiendo."

---

## 3. Arquitectura Propuesta

### A. Gestor de Dispositivos (`device_manager.py`)
Mantiene una base de datos local (`devices.json`) de todos los dispositivos conocidos.
```json
{
  "devices": [
    {
      "id": "dev_01",
      "type": "tv",
      "name": "Tele de la Cocina",
      "driver": "chromecast",
      "ip": "192.168.1.50",
      "aliases": ["tele cocina", "tv cocina", "pantalla cocina"]
    }
  ]
}
```

### B. Inyección de Frases en Vosk/Recognizer
En lugar de cargar solo `intents.json`, el sistema de reconocimiento (Vosk) debe cargar una lista combinada:
`Vocabulary = Static_Intents + Dynamic_Device_Aliases`

Cuando se inicia el `intent_classifier.py`, debe:
1.  Cargar `intents.json` (Base).
2.  Leer `devices.json`.
3.  Generar permutaciones:
    *   `turn_on_tv` + `[alias]` -> "Enciende {alias}"
    *   `turn_off_tv` + `[alias]` -> "Apaga {alias}"

### C. Resolución de Entidades
El clasificador de intents debe devolver no solo el intent (`turn_on_tv`), sino también la **Entidad Objetivo**.

*   **Entrada:** "Prende la tele del cuarto"
*   **Intent:** `turn_on_tv`
*   **Target:** `device_id: "tv_dormitorio"` (resuelto por coincidencia de alias)

## 4. Plan de Implementación

### Fase 1: Estructura de Datos (Inmediato)
- Crear `config/devices.json` para separar dispositivos de la configuración global.
- Migrar `settings.json['tvs']` a este nuevo formato.

### Fase 2: Descubrimiento Automático (Próximo Sprint)
- Implementar escáner ARP/mDNS (ya existen scripts parciales).
- Crear flujo de diálogo para "nombrar" dispositivos nuevos.

### Fase 3: Compilación Dinámica de Modelos (Release Final)
- Modificar `intent_classifier.py` para usar **Slots**.
- En lugar de frases rígidas, usar templates: `["enciende {device_name}", "prende {device_name}"]`.
- Al iniciar, reemplazar `{device_name}` con todos los nombres en `devices.json`.

---
**Nota para el usuario:** Esta funcionalidad transformará a Fina de un script personal a un producto de consumo real.
