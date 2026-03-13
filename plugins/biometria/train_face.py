
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

    # Iniciar cámara - Intento robusto
    cap = cv2.VideoCapture()
    for index in [0, 1, 2, -1]: # Indices comunes, -1 es auto
        try:
            print(f"🔍 Probando cámara en índice {index}...")
            # En Linux, V4L2 suele ser más estable para webcams integradas
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2) 
            if cap and cap.isOpened():
                print(f"✅ Cámara abierta en índice {index}")
                break
            
            # Reintento sin backend específico si falla
            cap = cv2.VideoCapture(index)
            if cap and cap.isOpened():
                print(f"✅ Cámara abierta en índice {index} (Legacy)")
                break
        except:
            continue

    if not cap or not cap.isOpened():
        print("❌ No se pudo abrir ninguna cámara.")
        print("Sugerencia: Revisa si alguna otra app (Meet, Zoom) está usando la webcam.")
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
            # Dibujar rectángulo (opcional si no se muestra, pero se mantiene para lógica)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Guardar cara
            count += 1
            face_img = gray[y:y+h, x:x+w]
            file_name = os.path.join(user_dir, f"{user_name}_{count}.jpg")
            cv2.imwrite(file_name, face_img)
            
            # Feedback por consola ya que no hay ventana
            sys.stdout.write(f"\r📸 Capturando: [%-30s] {count}/{max_samples}" % ('#' * count))
            sys.stdout.flush()
            
            # Pequeña pausa para variedad
            time.sleep(0.15)

    cap.release()
    print("\n\n✨ entrenamiento Finalizado!")
    print(f"Se guardaron {count} imágenes en {user_dir}")
    print("Fina ya te reconocerá visualmente.")
    input("\nPresione Enter para cerrar...")

if __name__ == "__main__":
    try:
        user = sys.argv[1] if len(sys.argv) > 1 else (os.getlogin() or "Usuario")
        train_face(user)
    except Exception as e:
        print(f"Error: {e}")
        input("Presione Enter para salir...")
