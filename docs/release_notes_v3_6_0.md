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

### 2. Procesamiento de Lenguaje y Clasificador de Inteligencia Artificial
- **Lazy Loading de Modelos:** El clasificador de intents (SentenceTransformer) ahora se inicializa *a demanda* ("Lazy Load"). Fina inicia muchísimo más rápido y solo carga el peso en memoria y GPU del modelo de machine learning cuando se recibe el primer comando de voz.
- **Aprendizaje de Modismos en Caliente (`learn_idiom`):** Agregada capacidad para que Fina aprenda frases personalizadas en tiempo de ejecución. Los usuarios ahora pueden decir *"cuando yo diga [x], quiero que [y]"*. Las definiciones se persisten en `~/.config/Fina/custom_intents.json`.
- **Desambiguación de Contexto (News vs TV):** Retocadas las lógicas de inferencia profunda para no confundir *"quiero ver las noticias"* (TV, requiere plugin) vs *"dime las noticias de hoy"* (Briefing proactivo del asistente). Igualmente, se afinó la separación del aire acondicionado y comando a canales de TV.

### 3. Actualización de Core (Backend)
- **Correcciones Core de i18n:** Arreglado un bug vital en la función de internalización global en `utils.py`. Ahora Fina es plenamente capaz de buscar, anidar y traducir estructuras internas en el prefijo `ui_` anidado del archivo `lang.json` para reflejar el estado en el frontend de Vue dinámicamente.
- **Detección Automática de `venv` Mejorada:** Reestructuración de la inicialización de ambientes de Python en `main.py` y `fina_api.py`. Ahora es más resiliente priorizando la ejecución sobre entornos virtuales nativos para aislar dependencias del sistema operativo del usuario.
- **Escáner de Red MAC-Vendor:** Ampliado el modelo de descubrimiento IoT en `iot/network_scan.py`. El script ahora cruza prefijos OUI de direcciones MAC contra una gran base de datos para inferir automáticamente si una IP descubierta pertenece a un Roku, LG, Somfy, Tuya, Rain Bird o Roomba.

### 4. Nuevos Comandos y Mapeos de Mercado (Plugin Market)
- Eje central conectado al **Fina Plugins Market**:
  - `robot_clean`, `robot_status` y `appliance_status`.
  - `lights_on`, `lights_off`, `set_brightness`.
  - `lock_door`, `unlock_door`, `lock_status`.
  - `open_blinds`, `close_blinds`.
  - `start_watering`.
  - `fridge_status`, `fridge_inventory`, `set_fridge_temp`. 
  - `check_solar_production`, `check_solar_battery`.

### 5. Documentación de Estándares Modulares
- Nueva documentación de desarrollo para creadores de hardware (Market Plugin Standards V3.6.0).
- Todos los métodos de API esperados y scripts obligatorios por cada nueva categoría fueron estandarizados de manera bilingüe `ES`/`EN`. Las categorías documentadas se extienden con: `Lights`, `Doors`/`Locks`, `Blinds`, `Irrigation`, `Robots`, `Refrigerators` y `Energy`.

### 6. Expansión Lingüística Multirregional
- El ecosistema "Zero-Config" de inteligencia habitacional ahora fue traducido a: Español, Inglés, Francés, Alemán, Portugués, Japonés y Chino (Mandarin) local y offline.
- Fina ahora comprende a nivel nativo combinaciones de disparo en su módulo `intents-[lang].json`. Ej: *"掃除機をかける"* (Japonés) activará correctamente un iRobot bajo el intent `robot_clean` unificado.
- Nueva documentación de desarrollo para creadores de hardware (Market Plugin Standards V3.6.0).
- Todos los métodos de API esperados y scripts obligatorios por cada nueva categoría fueron estandarizados de manera bilingüe `ES`/`EN`. Las categorías documentadas se extienden ahora con: `Lights`, `Doors`/`Locks`, `Blinds`, `Irrigation`, `Robots`, `Refrigerators` y `Energy`.

### 4. Modelo Semántico Multiidioma Expansivo (Intents)
- Todos los comandos de la nueva arquitectura de control del hogar fueron traducidos y habilitados en toda la subyacente estructura lingüística en: Español, Inglés, Francés, Alemán, Portugués, Japonés y Chino (Mandarin).
- Si Fina se usa en Japonés, un "掃除機をかける" interactuará nativamente con tu Roomba, bajo la misma lógica abstracta "robot_clean".

---
**Commit de actualización en la rama principal (dev/master) preparatoria para el empaquetado AppImage y Debian.**
