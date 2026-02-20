#!/usr/bin/env python3
"""
Script para generar PDF del manual de Fina Rust usando ReportLab
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime
import os

def register_fonts():
    """Registrar fuentes que soportan caracteres especiales"""
    try:
        # Intentar registrar fuentes del sistema
        pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        return 'Arial'
    except:
        # Fallback a fuentes por defecto
        return 'Helvetica'

def generate_fina_rust_manual_pdf():
    """Generar PDF del manual de Fina Rust con ReportLab"""
    
    # Configuración del documento
    doc = SimpleDocTemplate(
        "./Manual_Fina_Rust.pdf",
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Registrar fuentes
    font_name = register_fonts()
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para títulos
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1,  # Centrado
        fontName=font_name
    )
    
    # Estilo para subtítulos
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        textColor=colors.darkgreen,
        fontName=font_name
    )
    
    # Estilo para código
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontSize=10,
        spaceAfter=6,
        backgroundColor=colors.lightgrey,
        fontName='Courier'
    )
    
    # Contenido del documento
    story = []
    
    # 1. Portada
    story.append(Paragraph("Manual de Desarrollo - Fina Rust", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Guia completa de desarrollo, troubleshooting y mejores practicas", styles['Italic']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Fecha: {datetime.datetime.now().strftime('%d de %B de %Y')}", styles['Normal']))
    story.append(Paragraph("Version: v0.1.1", styles['Normal']))
    story.append(Spacer(1, 30))
    
    # 2. Configuración Inicial
    story.append(Paragraph("1. Configuracion Inicial", subtitle_style))
    
    story.append(Paragraph("1.1 Requisitos Previos", styles['Heading3']))
    
    code_text = """# Verificar instalacion de Rust
rustc --version

# Instalar Tauri CLI (requerido para desarrollo)
cargo install tauri-cli

# Verificar instalacion
cargo tauri --version"""
    
    story.append(Paragraph(code_text, code_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("1.2 Estructura del Proyecto", styles['Heading3']))
    
    structure_text = """src-tauri/
├── src/
│   └── main.rs              # Backend Rust
├── Cargo.toml              # Dependencias Rust
├── tauri.conf.json         # Configuracion Tauri
└── target/                 # Binarios compilados"""
    
    story.append(Paragraph(structure_text, code_style))
    story.append(Spacer(1, 20))
    
    # 3. Ejecución en Modo Desarrollo
    story.append(Paragraph("2. Ejecucion en Modo Desarrollo", subtitle_style))
    
    story.append(Paragraph("2.1 Metodo Manual", styles['Heading3']))
    
    manual_text = """cd ./src-tauri
cargo tauri dev"""
    
    story.append(Paragraph(manual_text, code_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("2.2 Metodo 2: Script Automatico", styles['Heading3']))
    
    auto_text = """cd .
npm run dev"""
    
    story.append(Paragraph(auto_text, code_style))
    story.append(Spacer(1, 20))
    
    # 4. Problemas Comunes y Soluciones
    story.append(Paragraph("3. Problemas Comunes y Soluciones", subtitle_style))
    
    # Tabla de problemas
    problems_data = [
        ['Error', 'Causa', 'Solucion'],
        ['no such command: tauri', 'Tauri CLI no instalado', 'cargo install tauri-cli'],
        ['Property toggleWindowMode not defined', 'Funcion no expuesta en Vue', 'Agregar al return del componente Vue'],
        ['address already in use', 'Puerto 8000 ya esta en uso', 'sudo lsof -ti:8000 | xargs kill -9']
    ]
    
    problems_table = Table(problems_data, colWidths=[2.5*inch, 2*inch, 2.5*inch])
    problems_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(problems_table)
    story.append(Spacer(1, 20))
    
    # 5. Arquitectura Frontend-Backend
    story.append(Paragraph("4. Arquitectura Frontend-Backend", subtitle_style))
    
    story.append(Paragraph("4.1 Backend Rust", styles['Heading3']))
    
    backend_code = """#[tauri::command]
fn toggle_fullscreen(window: Window) -> Result<(), String> {
    match window.is_fullscreen() {
        Ok(is_fullscreen) => {
            let new_state = !is_fullscreen;
            window.set_fullscreen(new_state)
        }
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![toggle_fullscreen])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}"""
    
    story.append(Paragraph(backend_code, code_style))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("4.2 Frontend JavaScript", styles['Heading3']))
    
    frontend_code = """// Definicion de funcion
const toggleWindowMode = async () => {
    if (window.__TAURI__) {
        const { invoke } = window.__TAURI__.core;
        await invoke('toggle_fullscreen');
    }
};

// Exposicion en Vue
return {
    toggleWindowMode,  // <-- Requerido para template
};

// Uso en template
<button @click="toggleWindowMode">MODO VENTANA (F11)</button>"""
    
    story.append(Paragraph(frontend_code, code_style))
    story.append(Spacer(1, 20))
    
    # 6. Comandos Útiles
    story.append(Paragraph("5. Comandos Utiles", subtitle_style))
    
    commands_data = [
        ['Categoria', 'Comando'],
        ['Desarrollo', 'cargo tauri dev'],
        ['Produccion', 'cargo tauri build'],
        ['Limpiar', 'cargo clean'],
        ['Ver procesos', 'pgrep -f fina-app'],
        ['Ver puertos', 'lsof -i :8000'],
        ['Logs detallados', 'RUST_LOG=debug cargo tauri dev']
    ]
    
    commands_table = Table(commands_data, colWidths=[2*inch, 4*inch])
    commands_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(commands_table)
    story.append(Spacer(1, 20))
    
    # 7. Caso de Estudio: Fix Pantalla Completa
    story.append(Paragraph("6. Caso de Estudio: Fix Pantalla Completa", subtitle_style))
    
    story.append(Paragraph("Problema: F11 funcionaba pero el boton no funcionaba.", styles['Normal']))
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("6.1 Solucion Paso a Paso", styles['Heading3']))
    
    steps = [
        "1. Instalar Tauri CLI: cargo install tauri-cli",
        "2. Agregar logs en backend y frontend",
        "3. Corregir comunicacion: Usar invoke",
        "4. Exponer funcion en Vue return",
        "5. Probar ambos metodos (F11 y boton)"
    ]
    
    for step in steps:
        story.append(Paragraph(step, styles['Normal']))
    
    story.append(Spacer(1, 12))
    story.append(Paragraph("Resultado:", styles['Heading3']))
    story.append(Paragraph("✅ F11 funciona<br/>✅ Boton funciona<br/>✅ Sin errores<br/>✅ Logs funcionales", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # 8. Recursos Adicionales
    story.append(Paragraph("7. Recursos Adicionales", subtitle_style))
    
    resources = [
        "• Tauri Documentation: https://tauri.app/v1/guides/",
        "• Rust Book: https://doc.rust-lang.org/book/",
        "• Vue 3 Guide: https://vuejs.org/guide/",
        "• Scripts de diagnostico: debug_fullscreen.py, launch_fina_rust.py"
    ]
    
    for resource in resources:
        story.append(Paragraph(resource, styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Footer final
    story.append(Paragraph("Ultima actualizacion: 5 de Enero, 2026", styles['Italic']))
    story.append(Paragraph("Version: Fina Rust v0.1.1", styles['Italic']))
    story.append(Paragraph("Estado: Fully Functional ✅", styles['Italic']))
    
    # Generar PDF
    try:
        doc.build(story)
        print("✅ Manual PDF generado exitosamente!")
        print("📍 Ubicacion: ./Manual_Fina_Rust.pdf")
        return True
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        return False

if __name__ == "__main__":
    generate_fina_rust_manual_pdf()
