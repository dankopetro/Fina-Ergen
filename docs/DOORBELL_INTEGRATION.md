# INTEGRACIÓN Y ESTABILIZACIÓN DEL SISTEMA DE TIMBRE (DOORBELL) - FINA ERGEN

## Fecha: 2026-02-19
## Módulos Afectados: Fina UI (`App.vue`), Monitor (`monitor_ergen.py`), Test (`test_doorbell.py`)

---

## OBJETIVO
Garantizar que cuando alguien toque el timbre (o cuando se simule con el script de prueba), la interfaz de Fina reaccione de forma 100% fiable abriendo la ventana del video, se avise al visitante por voz, se espere el tiempo adecuado y se finalice la llamada limpiando por completo el entorno de Android (Waydroid) para futuros eventos.

---

## CAMBIOS REALIZADOS

### 1. Robustez en la Comunicación Backend -> Frontend
**Problema:** La interfaz de Fina a veces ignoraba el comando para abrir la cámara porque la comunicación por comandos estándar (stdout) podía perderse.
**Solución:**
- Se configuró el frontend (`src/App.vue`) para que al consultar la API REST de Fina (`/api/state`) procese activamente los comandos `doorbell-ring` y `doorbell-hangup`.
- Ahora, cuando los scripts de Python detectan el timbre, envían una petición HTTP POST redundante directamente a `http://127.0.0.1:8000/api/command` asegurando que la UI abra y cierre la ventana de vídeo de inmediato.

### 2. Flujo Lineal y a Prueba de Errores en la Secuencia
**Archivos:** `plugins/doorbell/monitor_ergen.py` & `plugins/doorbell/test_doorbell.py`
- Se corrigieron errores de anidación (IndentationErrors) que impedían que la secuencia de colgado se ejecutara correctamente.
- La secuencia final ahora es **estricta y lineal**, asegurando que el colgado de la llamada y la limpieza se ejecuten SIEMPRE, incluso si llegara a fallar el enrutamiento de audio del micrófono.

### 3. "Despertar" la Interfaz de Tuya Smart
**Problema:** El stream de video de Tuya a veces se quedaba congelado o no reaccionaba de inmediato al traer la ventana al frente.
**Solución:** 
- Inmediatamente después de traer Waydroid al frente con `windowactivate`, el script realiza una **"sacudida táctil"** (dos `swipe` muy rápidos y cortos en la pantalla).
- Esto obliga a la aplicación de Android a registrar actividad y a "despertar" el stream de video antes de que Fina intente "atender" la llamada.

### 4. Corrección de Coordenadas y Colgado Seguro
**Problema:** El script intentaba colgar haciendo tap en unas coordenadas incorrectas (`150`, arriba) y, además, los botones de Tuya desaparecen tras unos segundos de inactividad de vídeo.
**Solución:**
- Se corrigieron las coordenadas del botón ROJO de colgar a su posición real **(X: 360, Y: 760)** (Abajo a la derecha).
- Para evitar el problema de los botones ocultos, el script ahora realiza un **toque preventivo en el centro de la pantalla (300, 400)** para revelar los controles de la interfaz justo antes de darle al botón de colgar.

### 5. Ajuste de Tiempos
- **Tiempo de Estabilización de Llamada:** Reducido de 5 a **3 segundos**. Waydroid se minimiza más rápido para que la UI de Fina retome el control visual.
- **Tiempo de Espera del Visitante:** Aumentado de 10 a **20 segundos**. Le da tiempo al visitante a escuchar a Fina, y da tiempo para monitorear el exterior antes de que Fina corte automáticamente.

### 6. Rutina de Limpieza Extrema (Clean-up)
**Problema:** Si Tuya Smart se quedaba abierta en la sección del timbre tras cortar la llamada, la próxima vez que tocaran el timbre la interfaz no arrancaba limpiamente.
**Solución:**
- Se añadió un bloque de limpieza final en los scripts:
  1. `$ am force-stop com.tuya.smart` (Mata la aplicación por completo).
  2. `$ input keyevent KEYCODE_HOME` (Regresa Waydroid al escritorio principal).
- Con esto, Waydroid queda totalmente limpio (y oculto en el dock) esperando al próximo evento.

---

## ARCHIVOS MODIFICADOS

1. **`/home/claudio/Descargas/Fina-Ergen/src/App.vue`**
   - Lógica añadida en el `setInterval` de polling para procesar `cmd.name === 'doorbell-ring'` y `doorbell-hangup`.

2. **`/home/claudio/Descargas/Fina-Ergen/plugins/doorbell/monitor_ergen.py`**
   - Notificación vía requests HTTP a la API.
   - Secuencia de "sacudida" inicial.
   - Reestructuración de bloque Try-Catch para asegurar el colgado.
   - Tap de doble paso (centro + botón 360,760) para colgar.
   - Limpieza (`force-stop` y `Home`) al finalizar.
   - Tiempos de espera ajustados (3s estabilización, 20s visualización).

3. **`/home/claudio/Descargas/Fina-Ergen/plugins/doorbell/test_doorbell.py`**
   - Actualizado con exactamente el mismo flujo, tiempos, sacudidas y limpiezas que el monitor real para garantizar simulaciones fidedignas al 100%.

---

## CÓMO PROBAR

**Para simular una llamada sin tener que salir a tocar el timbre:**
1. Iniciar Fina con su entorno completo:
   ```bash
   bash /home/claudio/Descargas/Fina-Ergen/lanzar_fina_simple.sh
   ```
2. Desde otra terminal, lanzar el simulador:
   ```bash
   python3 /home/claudio/Descargas/Fina-Ergen/plugins/doorbell/test_doorbell.py
   ```

**Flujo esperado en la simulación:**
- La consola anunciará el timbre y enviará orden a Fina.
- La ventana de Waydroid saltará, se "sacudirá" y luego atenderá la llamada.
- Fina minimizará Waydroid y mostrará su propia interfaz de cámara.
- Fina hablará ("Hola, buenos días...").
- Mantendrá la ventana 20 segundos.
- Volverá a llamar a Waydroid, tocará la pantalla, colgará, matará la app de Tuya, volverá a Home y le dirá a la UI de Fina que cierre la ventana roja.

## RESUMEN
✅ Comunicación redundante Frontend/Backend
✅ Interfaz de Tuya reacciona mejor ("sacudida")
✅ Colgado 100% fiable en las coordenadas correctas
✅ Limpieza total del sistema entre llamadas
✅ Timings optimizados para una mejor experiencia de usuario.
