
import subprocess
import sys
import os

def enroll_finger(user="Administrador"):
    print("\n👆 REGISTRO DE HUELLA DACTILAR - FINA ERGEN")
    print(f"   Usuario: {user}")
    print("------------------------------------------")
    print("Siga las instrucciones en consola:\n")

    try:
        # Intentar conectar con fprintd en modo interactivo
        res = subprocess.run(["fprintd-enroll", user], check=False)
        
        if res.returncode == 0:
            print("\n✅ Huella registrada correctamente.")
        else:
            print(f"\n❌ Error al registrar huella (Código {res.returncode}).")
            
    except FileNotFoundError:
        print("\n❌ Error: El comando 'fprintd-enroll' no está instalado.")
        print("Instale fprintd: sudo apt install fprintd")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

    input("\nPresione Enter para cerrar esta ventana...")

if __name__ == "__main__":
    user_name = sys.argv[1] if len(sys.argv) > 1 else (os.getlogin() or "Usuario")
    enroll_finger(user_name)
