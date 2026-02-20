"""
Módulo de autenticación por huella dactilar para Fina
Utiliza PAM (Pluggable Authentication Modules) para autenticación biométrica
"""

import subprocess
import logging
import getpass

logger = logging.getLogger("FinaAuth")

def check_fingerprint_auth(max_attempts=3, voice_model=None, speak_func=None):
    """
    Intenta autenticar al usuario mediante huella dactilar.
    
    Args:
        max_attempts (int): Número máximo de intentos permitidos
        voice_model: Modelo de voz para TTS
        speak_func: Función de síntesis de voz
        
    Returns:
        bool: True si la autenticación fue exitosa, False en caso contrario
    """
    logger.info("Iniciando autenticación por huella dactilar...")
    
    retry_prefix = ""
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Intento {attempt} de {max_attempts}")
            message = f"{retry_prefix}Intento {attempt} de {max_attempts}. Coloca tu dedo en el lector de huellas."
            retry_prefix = "" # Reset prefix
            print(f"\n🔐 {message}")
            if speak_func:
                speak_func(message, voice_model)
            
            # 1. Obtener la lista de dedos registrados para el usuario
            import getpass
            import re
            username = getpass.getuser()
            list_res = subprocess.run(["fprintd-list", username], capture_output=True, text=True)
            fingers = []
            for line in list_res.stdout.splitlines():
                match = re.search(r" - #\d+: ([\w-]+)", line)
                if match:
                    fingers.append(match.group(1))
            
            if not fingers:
                logger.error("No hay huellas registradas en el sistema.")
                if speak_func:
                    speak_func("No hay huellas registradas en el sistema.", voice_model)
                return False

            # 2. Intentar verificar contra CADA dedo registrado (más rápido que modo automático)
            logger.info(f"Dedos registrados: {fingers}")
            auth_success = False
            matched_finger = None
            
            for finger in fingers:
                logger.info(f"Probando verificación contra: {finger}")
                try:
                    # Timeout corto por dedo (8s) para mantener velocidad
                    result = subprocess.run(
                        ['fprintd-verify', username, '-f', finger],
                        capture_output=True,
                        text=True,
                        timeout=8
                    )
                    
                    if result.returncode == 0:
                        auth_success = True
                        matched_finger = finger
                        break
                except subprocess.TimeoutExpired:
                    logger.warning(f"Timeout verificando {finger}, probando siguiente...")
                    continue
            
            if auth_success:
                logger.info(f"✓ Autenticación biométrica exitosa (Dedo: {matched_finger})")
                print(f"✓ Autenticación exitosa! ({matched_finger})")
                return True
            else:
                logger.warning(f"✗ Intento {attempt} fallido (ningún dedo coincidió)")
                remaining = max_attempts - attempt
                fail_msg = f"Huella no reconocida. Intentos restantes: {remaining}"
                print(f"✗ {fail_msg}")
                if speak_func and remaining > 0:
                    speak_func(f"Huella no reconocida. Te quedan {remaining} intentos.", voice_model)
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout en intento {attempt}")
            remaining = max_attempts - attempt
            if attempt < max_attempts:
                retry_prefix = "Tiempo agotado. Intenta nuevamente. "
            else:
                msg = "Tiempo agotado. Intenta nuevamente."
                print(f"⏱ {msg}")
                if speak_func:
                    speak_func(msg, voice_model)
        except FileNotFoundError:
            logger.error("fprintd no está instalado en el sistema")
            print("⚠ Sistema de huellas dactilares no disponible.")
            if speak_func:
                speak_func("Sistema de huellas dactilares no disponible.", voice_model)
            return False
        except Exception as e:
            logger.error(f"Error durante autenticación: {e}")
            print(f"⚠ Error: {e}")
    
    logger.warning("Todos los intentos de huella dactilar fallaron")
    print(f"\n✗ Autenticación por huella dactilar fallida después de {max_attempts} intentos.")
    if speak_func:
        speak_func("Autenticación por huella dactilar fallida.", voice_model)
    return False


def password_fallback(voice_model=None, speak_func=None):
    """
    Sistema de respaldo de autenticación por contraseña.
    Se activa cuando la autenticación por huella dactilar falla.
    
    Args:
        voice_model: Modelo de voz para TTS
        speak_func: Función de síntesis de voz
    
    Returns:
        bool: True si la contraseña es correcta, False en caso contrario
    """
    logger.info("Activando sistema de respaldo por contraseña...")
    print("\n🔑 Activando sistema de respaldo por contraseña...")
    if speak_func:
        speak_func("Activando sistema de respaldo por contraseña.", voice_model)
    
    max_password_attempts = 3
    
    for attempt in range(1, max_password_attempts + 1):
        try:
            logger.info(f"Intento de contraseña {attempt} de {max_password_attempts}")
            print(f"\nIntento {attempt}/{max_password_attempts}")
            if speak_func:
                speak_func(f"Intento {attempt} de {max_password_attempts}. Ingresa tu contraseña.", voice_model)
            
            # Solicitar contraseña del usuario del sistema
            username = getpass.getuser()
            password = getpass.getpass(f"Ingresa la contraseña para {username}: ")
            
            # Verificar contraseña usando PAM
            result = subprocess.run(
                ['sudo', '-S', '-k', 'true'],
                input=password,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.info("✓ Autenticación por contraseña exitosa")
                print("✓ Contraseña correcta!")
                return True
            else:
                logger.warning(f"✗ Contraseña incorrecta (intento {attempt})")
                remaining = max_password_attempts - attempt
                print(f"✗ Contraseña incorrecta. Intentos restantes: {remaining}")
                if speak_func and remaining > 0:
                    speak_func(f"Contraseña incorrecta. Te quedan {remaining} intentos.", voice_model)
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout en verificación de contraseña (intento {attempt})")
            print("⏱ Tiempo agotado.")
            if speak_func:
                speak_func("Tiempo agotado.", voice_model)
        except Exception as e:
            logger.error(f"Error durante verificación de contraseña: {e}")
            print(f"⚠ Error: {e}")
    
    logger.error("Autenticación por contraseña fallida")
    print("\n✗ Autenticación fallida. Acceso denegado.")
    if speak_func:
        speak_func("Autenticación fallida. Acceso denegado.", voice_model)
    return False


def authenticate_user(voice_model=None, speak_func=None):
    """
    Función principal de autenticación.
    Intenta primero con huella dactilar, luego con contraseña como respaldo.
    
    Args:
        voice_model: Modelo de voz para TTS
        speak_func: Función de síntesis de voz
    
    Returns:
        bool: True si cualquier método de autenticación fue exitoso
    """
    logger.info("=== Iniciando proceso de autenticación ===")
    print("\n" + "="*50)
    print("🔐 SISTEMA DE AUTENTICACIÓN FINA")
    print("="*50)
    if speak_func:
        speak_func("Esperando autenticación.", voice_model)
    
    # Intentar autenticación por huella dactilar
    if check_fingerprint_auth(max_attempts=3, voice_model=voice_model, speak_func=speak_func):
        return True
    
    # Si falla, intentar con contraseña
    print("\n⚠ Cambiando a autenticación por contraseña...")
    if speak_func:
        speak_func("Cambiando a autenticación por contraseña.", voice_model)
    return password_fallback(voice_model=voice_model, speak_func=speak_func)

