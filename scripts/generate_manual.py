
import json
import os
from fpdf import FPDF
import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTENTS_FILE = os.path.join(PROJECT_ROOT, "intents.json")
MANUAL_PATH = os.path.join(PROJECT_ROOT, "Manual_Usuario_Fina.pdf")

class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Title
        self.cell(0, 10, 'Manual de Usuario - Fina Asistente de Voz', 0, 1, 'C')
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Página ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

def generate_manual():
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Colores
    COLOR_TITLE = (41, 128, 185)    # Azul para títulos
    COLOR_SUBTITLE = (22, 160, 133) # Verde azulado para secciones
    COLOR_TEXT = (0, 0, 0)          # Texto normal
    COLOR_CODE = (90, 90, 90)       # Bloques de código
    COLOR_HIGHLIGHT = (155, 89, 182) # Detalles / ideas futuras

    # 1. Introducción
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '1. Introducción', 0, 1)
    
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, '¡Bienvenido a Fina! Tu asistente de voz personal para Linux y tu hogar. Fina te permite controlar tu computadora, reproducir música, gestionar aplicaciones, automatizar tareas y manejar tu TV Android usando comandos de voz naturales en español.')
    pdf.ln(2)
    pdf.set_font('Arial', 'I', 11)
    pdf.multi_cell(0, 8, 'Nota: Fina es un fork avanzado del proyecto \'Jarvis Voice Assistant\', adaptado y ampliado para el idioma español, con foco en control de TV Android, automatización de escritorio y flujos cotidianos.')
    pdf.ln(3)

    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.multi_cell(0, 6, 'Proyecto original (Jarvis): https://github.com/mayooear/jarvis')
    pdf.set_text_color(*COLOR_TEXT)
    pdf.multi_cell(0, 6, 'Repositorio de Fina (fork): (actualizado 2026)')
    pdf.ln(5)

    # 2. Instalación
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '2. Instalación y Requisitos', 0, 1)
    
    # 2.1 Requisitos generales
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 10, '2.1 Requisitos del Sistema', 0, 1)
    
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', '', 12)
    steps = [
        "Python 3.8 o superior",
        "Conexión a internet para APIs (clima, noticias, etc.)",
        "Herramientas Android: adb (para TV Android)",
        "Audio: audacious, mpv/celluloid (o reproductor favorito)",
        "Herramientas de escritorio: xclip, scrot/maim, libnotify, xdotool",
        "Interfaz Desktop: webkit2gtk (para el Dashboard)"
    ]
    for step in steps:
        pdf.cell(0, 7, f"- {step}", 0, 1)
    
    pdf.ln(4)

    # 2.2 Instalación rápida
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 10, '2.2 Instalación Rápida', 0, 1)

    pdf.set_text_color(*COLOR_CODE)
    pdf.set_font('Courier', '', 10)
    install_quick = """
    git clone <URL_FINA>
    sudo apt update && sudo apt install -y \\
        python3 python3-venv python3-pip git \\
        adb audacious mpv xclip scrot libnotify-bin xdotool libwebkit2gtk-4.0-37
 vía Web Dashboard
    """
    pdf.multi_cell(0, 5, install_quick)
    pdf.ln(4)

    # 3. Centro de Comando Web (NUEVO)
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '3. Centro de Comando Web (Fina Dashboard)', 0, 1)
    
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, 'Fina cuenta con una interfaz web inmersiva de última generación para monitoreo y configuración.')
    pdf.ln(2)

    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, '3.1 Acceso y Lanzamiento', 0, 1)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 6, 'Ejecuta el script: ./run_web_panel.sh\nAccede en tu navegador a: http://localhost:8000')
    pdf.ln(2)

    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, '3.2 Características principales', 0, 1)
    features = [
        "Avatar inmersivo: Fondo traslúcido con halo dinámico reactivo al audio.",
        "Detección de TVs: Escaneo inteligente de televisores Android en la red local.",
        "Sincronización: Importación de canales y aplicaciones directamente desde la TV.",
        "Biometría: Interfaz visual para gestión y validación de huellas dactilares.",
        "Seguridad: Opción de visualizar u ocultar claves API sensibles.",
        "Auto-apagado: El servidor se cierra automáticamente al cerrar la pestaña web."
    ]
    pdf.set_text_color(*COLOR_TEXT)
    for f in features:
        pdf.multi_cell(0, 6, f"- {f}")
    pdf.ln(4)

    # 4. Biometría
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '4. Seguridad y Biometría', 0, 1)
    
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, 'Fina integra seguridad biométrica mediante fprintd para validar comandos sensibles.')
    biometric_points = [
        "Visualización: Pantalla de escaneo neón a pantalla completa en el Dashboard.",
        "Gestión: Pestaña dedicada en el panel web para ver lectores y huellas.",
        "Fallback: Si la biometría falla, solicita contraseña de sistema de respaldo.",
        "Requisitos: Lector de huellas compatible con Linux y servicio fprintd activo."
    ]
    for p in biometric_points:
        pdf.multi_cell(0, 6, f"- {p}")
    pdf.ln(5)

    # 5. Configuración y uso de TV Android
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '5. Control de TV Android', 0, 1)

    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 7, 'Control total de Smart TVs mediante ADB y Wake-on-LAN.')
    pdf.ln(2)

    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, '5.1 Autodetección', 0, 1)
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 6, 'Desde el Dashboard Web, pestaña Televisores, usa el botón "DETECTAR TVS". Fina encontrará tus dispositivos y te permitirá agregarlos instantáneamente con su IP y modelo real.')
    pdf.ln(4)

    # 6. Comandos de voz
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '6. Comandos de Voz', 0, 1)
    
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, 'Tabla de comandos agrupados por categoría:')
    pdf.ln(4)

    try:
        with open(INTENTS_FILE, 'r', encoding='utf-8') as f:
            intents = json.load(f)
        
        groups = {
            "Control de TV": ["turn_on_tv", "turn_off_tv", "tv_set_channel", "tv_open_app"],
            "Multimedia": ["play_music", "stop_music", "pause_music", "download_instagram"],
            "Sistema": ["suspend", "shutdown", "take_screenshot", "battery_status"],
            "Utilidades": ["get_weather", "weather_tomorrow", "when_will_rain", "generate_image"]
        }

        for group_name, intent_keys in groups.items():
            pdf.set_text_color(*COLOR_SUBTITLE)
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, group_name, 0, 1)
            
            for key in intent_keys:
                if key in intents:
                    phrases = intents[key]
                    readable_name = key.replace("_", " ").capitalize()
                    pdf.set_text_color(*COLOR_TITLE)
                    pdf.set_font('Arial', 'B', 12)
                    pdf.write(6, f"- {readable_name}: ")
                    pdf.set_text_color(*COLOR_TEXT)
                    pdf.set_font('Arial', '', 11)
                    pdf.write(6, f'"{phrases[0]}"\n')
            pdf.ln(4)

    except Exception as e:
        pdf.multi_cell(0, 10, f"Error leyendo comandos: {str(e)}")

    pdf.output(MANUAL_PATH)
    print(f"Manual generado en: {MANUAL_PATH}")
    return MANUAL_PATH

if __name__ == "__main__":
    generate_manual()
