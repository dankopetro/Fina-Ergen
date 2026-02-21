import os
from weasyprint import HTML

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "../../Manual_Guia_Configuracion_Fina.html")
PDF_FILE = os.path.join(BASE_DIR, "../../Manual_Guia_Configuracion_Fina.pdf")

def generate_pdf():
    print(f"📖 Leyendo HTML de Configuración: {HTML_FILE}...")
    try:
        HTML(filename=HTML_FILE).write_pdf(PDF_FILE)
        print(f"✅ PDF generado exitosamente: {PDF_FILE}")
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")

if __name__ == "__main__":
    generate_pdf()
