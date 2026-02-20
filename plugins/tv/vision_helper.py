
import logging

def detect_user_location():
    """
    Simula (o implementa) la detección visual del usuario para saber en qué habitación está.
    Retorna: 'Living', 'Dormitorio' o None si no se detecta.
    """
    logger = logging.getLogger("TVPlugin.Vision")
    
    # ------------------------------------------------------------------
    # TODO: INTEGRACIÓN FUTURA CON OPENCV / YOLO / CÁMARA
    # ------------------------------------------------------------------
    # Aquí iría el código para capturar un frame de la webcam y analizarlo.
    # Ejemplo conceptual:
    # 
    # frame = capture_frame()
    # predictions = yolo_model.predict(frame)
    # 
    # separate logic for camera ID mapping:
    # if camera_id == 0: room = "Living"
    # elif camera_id == 1: room = "Dormitorio"
    #
    # if "person" in predictions:
    #     logger.info(f"👤 Usuario detectado visualmente en {room}")
    #     return room
    # ------------------------------------------------------------------

    # POR AHORA: Retornamos None para forzar la pregunta verbal
    # logger.info("👀 No se detectó presencia visual (cámara no implementada aún).")
    return None
