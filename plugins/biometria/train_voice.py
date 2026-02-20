
import sys
import os

# Asegurar que podemos importar auth desde la raíz del proyecto
PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJ_ROOT)

try:
    from auth.voice_auth import VoiceAuthenticator
except ImportError:
    print("❌ No se pudo importar auth.voice_auth. Verifique la estructura del proyecto.")
    sys.exit(1)

def run_voice_train(user="Administrador"):
    print("\n🎙  ENTRENAMIENTO DE VOZ - FINA ERGEN")
    print(f"   Usuario: {user}")
    print("------------------------------------------")
    print("Siga las instrucciones en pantalla y hable claro.")
    print("------------------------------------------\n")

    try:
        # Inicializar autenticador (buscará modelos en raíz/voice_profiles)
        auth = VoiceAuthenticator()
        
        # Iniciar proceso interactivo
        success = auth.enroll_new_user(user, num_samples=3)
        
        if success:
            print("\n✨ ¡Entrenamiento completado exitosamente!")
            print(f"Perfil de voz guardado para {user}.")
        else:
            print("\n⚠ El entrenamiento no pudo completarse.")
            
    except Exception as e:
        print(f"\n❌ Ocurrió un error crítico durante el entrenamiento:\n{e}")
        import traceback
        traceback.print_exc()

    input("\nPresione Enter para cerrar esta ventana...")

if __name__ == "__main__":
    # Soporte para argumento de nombre de usuario
    user_name = sys.argv[1] if len(sys.argv) > 1 else (os.getlogin() or "Usuario")
    run_voice_train(user_name)
