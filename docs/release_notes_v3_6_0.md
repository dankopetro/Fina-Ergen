# Fina Ergen V3.6.0 - Notas de la Versión (Release Notes)

🎉 **¡Gran Actualización Estructural y Domótica!**

Esta versión 3.6.0 marca un hito en la expansión de capacidades "Smart Home" de Fina Ergen, transformándola en un centro verdaderamente modular y universal para administrar el hábitat completo del usuario sin complejas configuraciones.

## 🌟 Novedades y Funciones

### 1. Nuevo Panel de Hábitat (Frontend)
- **Monitoreo Energético Avanzado:** Se añadió el seguimiento de consumo mensual (`monthly_kwh`) para medir el consumo general mensual de Aire Acondicionado, adicional a la potencia instantánea y los kWh acumulados históricamente.
- **Ecosistema Ampliado "Zero-Config":** El panel de Configuración de Hábitat ahora posee soporte nativo con persistencia de redes locales (IPs) e integración para nuevas categorías de dispositivos:
    - **Ventanas y Persianas:** Soporte base para el estándar abierto (ej. hubs Somfy, Lutron).
    - **Riego Inteligente:** Integración de controladores de agua y aspersores de jardín (ej. Rachio, Rain Bird).
    - **Limpieza Automatizada:** Control de robots aspiradores y reconocimiento visual de su estatus. (ej. Roomba, Roborock).
    - **Electrodomésticos Smart (Línea Blanca):** Panel de diagnóstico de heladeras inteligentes con estatus de temperaturas (refrigerador y freezer) orientados al ecosistema Samsung ThinQ, LG, etc.

### 2. Actualización de API Domótica Interna (Backend Core)
- Mapeados y pre-configurados todos los comandos vocales universales listos para enganchar en el **Fina Plugins Market**:
  - `robot_clean`, `robot_status` y `appliance_status`.
  - `lights_on`, `lights_off`, `set_brightness`.
  - `lock_door`, `unlock_door`, `lock_status`.
  - `open_blinds`, `close_blinds`.
  - `start_watering`.
  - `fridge_status`, `fridge_inventory`, `set_fridge_temp`. 
  - `check_solar_production`, `check_solar_battery`.
- Actualizadas las tablas de asignación de MACs de `iot/network_scan.py` con mapeos listos para el ecosistema expandido.

### 3. Fina Plugins Market Standards
- Nueva documentación de desarrollo para creadores de hardware (Market Plugin Standards V3.6.0).
- Todos los métodos de API esperados y scripts obligatorios por cada nueva categoría fueron estandarizados de manera bilingüe `ES`/`EN`. Las categorías documentadas se extienden ahora con: `Lights`, `Doors`/`Locks`, `Blinds`, `Irrigation`, `Robots`, `Refrigerators` y `Energy`.

### 4. Modelo Semántico Multiidioma Expansivo (Intents)
- Todos los comandos de la nueva arquitectura de control del hogar fueron traducidos y habilitados en toda la subyacente estructura lingüística en: Español, Inglés, Francés, Alemán, Portugués, Japonés y Chino (Mandarin).
- Si Fina se usa en Japonés, un "掃除機をかける" interactuará nativamente con tu Roomba, bajo la misma lógica abstracta "robot_clean".

---
**Commit de actualización en la rama principal (dev/master) preparatoria para el empaquetado AppImage y Debian.**
