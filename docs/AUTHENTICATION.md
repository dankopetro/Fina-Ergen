# Sistema de Autenticación - Fina Asistente de Voz

Este documento describe el sistema de autenticación por huella digital implementado en Fina, incluyendo su configuración, uso y solución de problemas.

## Resumen

Fina utiliza un sistema de autenticación biométrica basado en `fprintd` para proteger operaciones sensibles como:
- Apagar el sistema
- Suspender el sistema
- Actualizar el sistema
- Operaciones administrativas

## Componentes del Sistema

### 1. Módulo Principal (`auth/fingerprint_auth.py`)

Contiene las funciones principales de autenticación:
- `authenticate_user()`: Función principal que coordina el proceso
- `check_fingerprint_auth()`: Autenticación por huella digital
- `password_fallback()`: Sistema de respaldo por contraseña

### 2. Función de Integración (`utils.py`)

La función `require_face_auth()` sirve como punto de entrada para el sistema de autenticación desde otras partes del código.

## Requisitos del Sistema

### Dependencias del Sistema
```bash
# Ubuntu/Debian
sudo apt-get install fprintd libpam-fprintd

# Arch Linux
sudo pacman -S fprintd

# Fedora
sudo dnf install fprintd pam_fprintd
```

### Dependencias de Python
- Módulo `auth.fingerprint_auth` (incluido en el proyecto)
- No requiere dependencias Python adicionales

## Configuración

### 1. Instalar fprintd
```bash
# Iniciar el servicio
sudo systemctl start fprintd
sudo systemctl enable fprintd
```

### 2. Registrar Huella Digital
```bash
# Registrar tu huella
fprintd-enroll

# Verificar que funciona
fprintd-verify
```

### 3. Configurar PAM (Opcional)
Para habilitar la autenticación por huella en todo el sistema:
```bash
sudo pam-auth-update
```

## Uso

### En el Código Python
```python
from utils import require_face_auth

# Para proteger una operación sensible
if require_face_auth(selected_model):
    # Ejecutar operación
    execute_sensitive_operation()
else:
    # Autenticación fallida
    return
```

### Desde la Línea de Comandos
```bash
# Verificar autenticación
fprintd-verify

# Listar huellas registradas
fprintd-list

# Eliminar huellas
fprintd-delete $USER
```

## Flujo de Autenticación

1. **Inicio del Proceso**: `require_face_auth()` llama a `authenticate_user()`
2. **Autenticación por Huella**: Se intenta autenticar con huella hasta 3 veces
3. **Respaldo por Contraseña**: Si falla la huella, se usa contraseña
4. **Resultado**: Se retorna `True` si tiene éxito, `False` si falla

## Scripts de Prueba

### test_auth.py
Script para probar el sistema completo de autenticación:
```bash
python3 test_auth.py
```

### test_require_face_auth.py
Script para probar la función de integración:
```bash
python3 test_require_face_auth.py
```

## Solución de Problemas

### Problema: "fprintd no está instalado"
**Solución**:
```bash
sudo apt-get install fprintd libpam-fprintd
```

### Problema: "No se encontró lector de huellas"
**Solución**:
1. Verificar que el lector esté conectado
2. Comprobar que el dispositivo sea reconocido:
   ```bash
   lsusb | grep -i fingerprint
   ```
3. Reiniciar el servicio:
   ```bash
   sudo systemctl restart fprintd
   ```

### Problema: "Huella no reconocida"
**Solución**:
1. Limpiar el lector de huellas
2. Registrar la huella nuevamente:
   ```bash
   fprintd-delete $USER
   fprintd-enroll
   ```

### Problema: "Timeout en autenticación"
**Solución**:
1. Aumentar el timeout en el código
2. Verificar que el lector funcione correctamente

## Consideraciones de Seguridad

### Aspectos de Seguridad
- Las contraseñas no se almacenan en texto plano
- El sistema utiliza PAM para autenticación
- Los intentos fallidos se registran en el log

### Recomendaciones
- Configurar huellas de respaldo
- Mantener el sistema actualizado
- Revisar los logs regularmente

## Logs y Monitoreo

### Ubicación de Logs
- Logs del sistema: `/var/log/auth.log`
- Logs de Fina: Configurado en el logging del proyecto

### Verificar Estado del Servicio
```bash
# Estado de fprintd
sudo systemctl status fprintd

# Logs del servicio
sudo journalctl -u fprintd
```

## API Reference

### Funciones Principales

#### `authenticate_user(voice_model=None, speak_func=None)`
- **Parámetros**:
  - `voice_model`: Modelo de voz para TTS
  - `speak_func`: Función de síntesis de voz
- **Retorna**: `bool` - True si autenticación exitosa

#### `require_face_auth(selected_model)`
- **Parámetros**:
  - `selected_model`: Modelo de voz seleccionado
- **Retorna**: `bool` - True si autenticación exitosa

## Actualizaciones y Mantenimiento

### Actualizar fprintd
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get upgrade fprintd

# Arch Linux
sudo pacman -Syu fprintd
```

### Mantener Huellas Actualizadas
```bash
# Verificar huellas registradas
fprintd-list

# Re-registrar si es necesario
fprintd-delete $USER
fprintd-enroll
```

## Contribuciones

Para mejorar el sistema de autenticación:
1. Reportar problemas en el repositorio
2. Proponer mejoras en la seguridad
3. Añadir nuevos métodos de autenticación

---

**Nota**: Este sistema está diseñado para Linux y requiere hardware compatible con lectores de huellas digitales.
