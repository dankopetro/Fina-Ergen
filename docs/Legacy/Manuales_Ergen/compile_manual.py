
import os
from weasyprint import HTML

# Configuración
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "Manual_Pro_Ergen_v2.5.html")
PDF_FILE = os.path.join(BASE_DIR, "Manual_Usuario_Fina_Ergen_PRO_MIX.pdf")

def generate_pdf():
    print(f"📖 Leyendo HTML: {HTML_FILE}...")
    
    # Renderizar PDF usando WeasyPrint
    # WeasyPrint procesará el CSS interno del archivo HTML automáticamente.
    print("🎨 Renderizando PDF...")
    try:
        HTML(filename=HTML_FILE).write_pdf(PDF_FILE)
        print(f"✅ PDF generado exitosamente: {PDF_FILE}")
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")

if __name__ == "__main__":
    generate_pdf()
