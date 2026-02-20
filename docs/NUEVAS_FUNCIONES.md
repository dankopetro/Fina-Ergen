# Nuevas Funcionalidades - Fina

## 📅 Fecha: 2025-12-05

## 🎯 Mejoras Implementadas

### 1. 🎤 Nuevas Palabras de Activación

**Descripción:**
Ahora podés despertar a Fina con más palabras cariñosas además de "Fina".

**Nuevas palabras de activación:**
- ✅ **"bebe"** / **"bebé"**
- ✅ **"nena"**
- ✅ **"dora"**
- ✅ **"loquita"**
- ✅ **"compu"**

**Ejemplos de uso:**
```
"Hola bebe"
"Nena, ¿estás ahí?"
"Compu, despierta"
"Loquita, necesito ayuda"
"Dora, buenos días"
```

### 2. 🌡️ Clima con Sensación Térmica

**Descripción:**
El comando de clima ahora incluye la sensación térmica (feels like).

**Mejoras:**
- ✅ Temperatura real
- ✅ Sensación térmica
- ✅ Humedad
- ✅ Descripción del clima en español
- ✅ Detección automática de ciudad

**Comandos:**
```
"Cómo está el clima"
"Cuál es la sensación térmica"
"Qué temperatura se siente"
"Cómo se siente el clima"
```

**Respuesta ejemplo:**
```
"El clima actual en Buenos Aires es cielo claro 
con una temperatura de 25°C. 
Sensación térmica de 27°C y humedad del 60%."
```

### 3. 🌤️ Pronóstico para Mañana

**Descripción:**
Nuevo intent para consultar el clima de mañana.

**Intent:** `weather_tomorrow`

**Comandos (19 variantes):**
```
"Cómo estará el tiempo mañana"
"Qué tiempo hará mañana"
"Pronóstico para mañana"
"Va a llover mañana"
"Qué temperatura habrá mañana"
"Clima de mañana"
```

**Respuesta ejemplo:**
```
"Mañana en Buenos Aires el clima estará parcialmente nublado 
con una temperatura de 23°C. 
Sensación térmica de 24°C y humedad del 55%."
```

### 4. 🌧️ Cuándo Va a Llover

**Descripción:**
Nuevo intent para saber cuándo lloverá en los próximos 5 días.

**Intent:** `when_will_rain`

**Comandos (19 variantes):**
```
"Cuándo va a llover"
"Cuándo llueve"
"Va a llover esta semana"
"Cuándo caerá lluvia"
"En qué día llueve"
"Habrá lluvia"
```

**Respuestas ejemplo:**
```
Caso 1 (lluvia en un solo día):
"Lloverá el miércoles 06/12 a las 15:00."

Caso 2 (lluvia en varios días):
"Se espera lluvia en los siguientes días: 
miércoles 06/12, jueves 07/12, viernes 08/12."

Caso 3 (sin lluvia):
"No se espera lluvia en los próximos 5 días."
```

## 🔧 Detalles Técnicos

### Archivos Modificados:

1. **`intents.json`**
   - Agregadas 15 nuevas palabras de activación
   - Agregado intent `weather_tomorrow` (19 variantes)
   - Agregado intent `when_will_rain` (19 variantes)
   - Agregadas 6 variantes para sensación térmica en `get_weather`

2. **`utils.py`**
   - Actualizada función `get_weather()` con sensación térmica
   - Nueva función `get_weather_tomorrow()`
   - Nueva función `when_will_rain()`
   - Detección automática de ciudad en todas las funciones

3. **`main.py`**
   - Importadas nuevas funciones de clima
   - Agregados handlers para `weather_tomorrow`
   - Agregados handlers para `when_will_rain`
   - Actualizado handler de `get_weather`

### Funciones de Clima:

#### `get_weather(city=None)`
- Obtiene clima actual
- Incluye sensación térmica
- Detección automática de ciudad
- Respuesta en español

#### `get_weather_tomorrow(city=None)`
- Pronóstico para mañana (mediodía)
- Temperatura y sensación térmica
- Descripción del clima
- Humedad

#### `when_will_rain(city=None)`
- Busca lluvia en próximos 5 días
- Muestra días y horarios
- Traduce nombres de días al español
- Informa si no habrá lluvia

## 📊 Resumen de Comandos

### Palabras de Activación (Total: 15 nuevas)
```
bebe, bebé, nena, dora, loquita, compu
+ variantes con "Hola"
```

### Comandos de Clima (Total: 50+ variantes)

**Clima actual:**
- "Cómo está el clima"
- "Sensación térmica"
- "Qué temperatura se siente"

**Mañana:**
- "Cómo estará mañana"
- "Pronóstico para mañana"
- "Va a llover mañana"

**Cuándo lloverá:**
- "Cuándo va a llover"
- "Cuándo llueve"
- "Habrá lluvia"

## 🧪 Pruebas Recomendadas

1. **Probar nuevas palabras de activación:**
   ```
   "Hola bebe"
   "Nena"
   "Compu, despierta"
   ```

2. **Probar clima con sensación térmica:**
   ```
   "Cómo está el clima"
   "Cuál es la sensación térmica"
   ```

3. **Probar pronóstico de mañana:**
   ```
   "Cómo estará el tiempo mañana"
   "Qué temperatura habrá mañana"
   ```

4. **Probar cuándo lloverá:**
   ```
   "Cuándo va a llover"
   "Va a llover esta semana"
   ```

## 📝 Notas

- Todas las funciones de clima detectan automáticamente la ciudad
- Las respuestas están en español
- Los nombres de días se traducen automáticamente
- La API de OpenWeatherMap proporciona pronósticos de 5 días
- La sensación térmica se calcula automáticamente por la API

---

**Implementado por:** Antigravity AI  
**Fecha:** 2025-12-05 00:20  
**Estado:** ✅ Completado y compilado

## 📅 Fecha: 2025-12-10

### 5. 🛠️ Panel de Configuración y Autodetección de TV

**Descripción:**

Se agregó un **panel gráfico de configuración** para Fina y nuevas herramientas de autodetección para televisores Android:

- Panel `fina_config_panel.py` (Python + Flet).
- Configuración visual de TVs, APIs, rutas internas, canales y apps de TV.
- Autodetección de canales desde la TV (vía ADB).
- Autodetección de aplicaciones instaladas en la TV (vía ADB).

**Nuevas capacidades:**

- Editar hasta **4 TVs** con IP, MAC, estado *Activa* y *Principal*.
- Editar claves API y rutas sin tocar `config.py` a mano.
- Gestionar **canales favoritos** y **canales personalizados** (estos últimos se guardan aparte en `fina_settings.json`).
- Escanear la base de datos de canales de la TV y ampliar automáticamente `channels.json`.
- Detectar paquetes Android relevantes en la TV y construir un mapa `nombre amigable → paquete` para abrir apps por voz.

**Flujo de uso (resumen):**

1. Ejecutar el panel:
   ```bash
   python3 fina_config_panel.py
   ```
2. Configurar TVs, APIs y rutas desde las pestañas correspondientes.
3. En **Canales**:
   - Pulsar `Escanear canales desde la TV` para importar canales reales.
   - Marcar favoritos y definir canales personalizados.
4. En **Apps TV**:
   - Pulsar `Detectar apps en la TV` para listar paquetes instalados y generar mapeos.
   - Guardar el mapa para que `tv_open_app_cmd` lo use en los intents.

**Archivos modificados/creados:**

1. **`fina_config_panel.py`** (nuevo)
   - Panel con pestañas: TVs, APIs/Paths, Canales, Apps TV.
   - Integra lectura/escritura de `fina_settings.json` y actualización opcional de `config.py`.

2. **`fina_settings.json`** (nuevo)
   - Almacena:
     - `tvs`: configuración de televisores.
     - `apis` y `paths`.
     - `channels`: `favorites` y `custom` (canales personalizados se mantienen aparte de `channels.json`).
     - `tv_apps`: mapa nombre amigable → paquete Android.

3. **`scripts/tv_on.py`**
   - Ahora lee las TVs desde `fina_settings.json` en lugar de una lista fija.

4. **`utils.py`**
   - `_get_connected_tv_ip()` ahora usa las TVs configuradas en `fina_settings.json`.
   - `tv_open_app_cmd()` lee el mapa `tv_apps` desde `fina_settings.json`, con fallback a un mapa por defecto.

5. **`MANUAL_DE_USUARIO.md`**
   - Nueva sección explicando el panel de configuración y su uso básico.

**Notas:**

- Los canales personalizados (`channels.custom`) se mantienen **separados** y no sobreescriben `channels.json`.
- La autodetección requiere que la TV esté accesible por **ADB** (misma configuración que el resto de funciones de TV).

---

**Implementado por:** Cascade + Claudio  
**Fecha:** 2025-12-10  
**Estado:** ✅ Completado e integrado

---

## 📅 Fecha: 2026-01-04

### 6. 🌐 Centro de Comando Web e Interfaz Inmersiva

**Descripción:**

Se ha desarrollado un nuevo **Centro de Comando Web** (Dashboard) que reemplaza la configuración estática por una experiencia de usuario moderna, inmersiva y en tiempo real.

**Nuevas características de la interfaz:**
- ✅ **Avatar Inmersivo**: Un fondo con un avatar traslúcido y un "Halo" dinámico que reacciona visualmente al audio de Fina y al micrófono del usuario.
- ✅ **Dashboard en Tiempo Real**: Visualización clara del estado de Fina (IDLE, Hablando, Escuchando, Autenticando).
- ✅ **Píldora de Estado**: Indica el proceso específico que Fina está ejecutando en cada momento.
- ✅ **Saludo Dinámico**: Bienvenida personalizada ("Bienvenido Claudio") con corrección de mayúsculas automática.
- ✅ **Navegación Intuitiva**: Menú lateral colapsable con acceso a todas las configuraciones.

**Gestión de TV y Seguridad:**
- ✅ **Detección ADB de TVs**: Escaneo automático de la red local para encontrar y configurar televisores Android.
- ✅ **Escaneo de Canales y Apps**: Importación directa de la lista de canales y aplicaciones desde la TV al panel.
- ✅ **Biometría Visual**: Interfaz de autenticación por huella dactilar a pantalla completa con soporte integrado para `fprintd`.
- ✅ **Visibilidad de APIs**: Botón de alternancia para ver/ocultar claves API en los formularios.

**Mejoras de Sistema:**
- ✅ **Auto-Apagado Inteligente**: El servidor de la API se cierra automáticamente al detectar el cierre de la pestaña del navegador (usando `Beacon API` y `pagehide`).
- ✅ **Refuerzo de Estabilidad**: Migración de la comunicación de estado a un sistema de polling optimizado para evitar latencia visual.

**Archivos modificados/creados:**

1. **`fina_api.py`**
   - Nuevos endpoints: `/api/scan-tvs`, `/api/shutdown`, `/api/state` (mejorado), `/api/system-info`.
2. **`static/index.html`** (nuevo/rediseñado)
   - SPA (Single Page Application) construida con Vue.js 3 y Tailwind CSS.
3. **`run_web_panel.sh`**
   - Script para lanzar el entorno web fácilmente.
4. **`auth/fingerprint_auth.py`**
   - Soporte para la validación visual y estados de autenticación.

---

**Implementado por:** Antigravity AI + Claudio  
**Fecha:** 2026-01-04  
**Estado:** ✅ Completado y desplegado
