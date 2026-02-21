import os
from weasyprint import HTML

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "../../Manual_Usuario_Practico_Fina_v3.5.4.html")
PDF_FILE = os.path.join(BASE_DIR, "../../Manual_Usuario_Visual_Fina_v3.5.4.pdf")

def generate_pdf():
    print(f"📖 Leyendo HTML Visual: {HTML_FILE}...")
    try:
        HTML(filename=HTML_FILE).write_pdf(PDF_FILE)
        print(f"✅ PDF generado exitosamente: {PDF_FILE}")
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")

if __name__ == "__main__":
    generate_pdf()
