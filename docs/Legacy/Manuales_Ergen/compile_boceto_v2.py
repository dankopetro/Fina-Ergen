
import os
from weasyprint import HTML

# Configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "Boceto_Nueva_Interfaz_v2.html")
PDF_FILE = os.path.join(BASE_DIR, "Boceto_Nueva_Interfaz_UI_3.0_v2.pdf")

def generate_pdf():
    print(f"📖 Leyendo HTML: {HTML_FILE}...")
    print("🎨 Renderizando PDF (Boceto v2) con imágenes de usuario...")
    try:
        HTML(filename=HTML_FILE).write_pdf(PDF_FILE)
        print(f"✅ PDF generado exitosamente: {PDF_FILE}")
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")

if __name__ == "__main__":
    generate_pdf()
