
import cv2
import os
import time
import sys

def train_face(user_name="Administrador"):
    print("📸 Iniciando entrenamiento facial para:", user_name)
    print("Mire a la cámara y mueva ligeramente la cabeza...")

    # Crear directorio para guardar caras - RUTA UNIVERSAL
    def get_config_dir():
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return os.path.join(xdg_config, "Fina")
        try:
            from pathlib import Path
            return os.path.join(str(Path.home()), ".config", "Fina")
        except:
            return os.path.expanduser("~/.config/Fina")

    base_dir = os.path.join(get_config_dir(), "faces")
    user_dir = os.path.join(base_dir, user_name)
    os.makedirs(user_dir, exist_ok=True)

    # Iniciar cámara
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara")
        return

    # Cargar Haar Cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    count = 0
    max_samples = 30

    while count < max_samples:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            # Dibujar rectángulo
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Guardar cara cada 10 frames aprox para variedad (o simplemente delay)
            # Aquí lo hacemos simple: guardar si detecta
            count += 1
            face_img = gray[y:y+h, x:x+w]
            file_name = os.path.join(user_dir, f"{user_name}_{count}.jpg")
            cv2.imwrite(file_name, face_img)
            print(f"✅ Captura {count}/{max_samples}")
            
            # Pequeña pausa para no guardar frames idénticos
            time.sleep(0.1)

        cv2.imshow('Entrenamiento Facial - Fina Ergen', frame)

        # Salir con 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n✨ Entrenamiento Finalizado!")
    print(f"Se guardaron {count} imágenes en {user_dir}")
    input("\nPresione Enter para cerrar...")

if __name__ == "__main__":
    try:
        user = sys.argv[1] if len(sys.argv) > 1 else (os.getlogin() or "Usuario")
        train_face(user)
    except Exception as e:
        print(f"Error: {e}")
        input("Presione Enter para salir...")
