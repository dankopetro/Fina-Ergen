#!/usr/bin/env python3
"""
Script para generar PDF del manual de Fina Rust
"""

import os
from fpdf import FPDF
import datetime

class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Title
        self.cell(0, 10, 'Manual de Desarrollo - Fina Rust', 0, 1, 'C')
        # Line break
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Página ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

def generate_fina_rust_manual():
    """Generar PDF del manual de Fina Rust"""
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Configurar para soporte Unicode
    pdf.set_font('Arial', '', 12)  # Fuente que soporta caracteres especiales
    
    # Colores
    COLOR_TITLE = (41, 128, 185)    # Azul para títulos
    COLOR_SUBTITLE = (22, 160, 133) # Verde azulado para secciones
    COLOR_TEXT = (0, 0, 0)          # Texto normal
    COLOR_CODE = (90, 90, 90)       # Bloques de código
    COLOR_HIGHLIGHT = (155, 89, 182) # Detalles / ideas futuras
    
    # 1. Título y Portada
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 15, 'Manual de Desarrollo - Fina Rust', 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', 'I', 12)
    pdf.cell(0, 10, 'Guia completa de desarrollo, troubleshooting y mejores practicas', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, f'Fecha: {datetime.datetime.now().strftime("%d de %B de %Y")}', 0, 1, 'C')
    pdf.cell(0, 8, 'Version: v0.1.1', 0, 1, 'C')
    pdf.ln(15)
    
    # 2. Configuración Inicial
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '1. Configuración Inicial', 0, 1)
    
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, '1.1 Requisitos Previos', 0, 1)
    
    pdf.set_text_color(*COLOR_CODE)
    pdf.set_font('Courier', '', 10)
    code_requirements = """# Verificar instalacion de Rust
rustc --version

# Instalar Tauri CLI (requerido para desarrollo)
cargo install tauri-cli

# Verificar instalacion
cargo tauri --version"""
    
    pdf.multi_cell(0, 5, code_requirements)
    pdf.ln(5)
    
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, '1.2 Estructura del Proyecto', 0, 1)
    
    pdf.set_text_color(*COLOR_CODE)
    pdf.set_font('Courier', '', 10)
    structure = """test/fina-rust/src-tauri/
├── src/
│   └── main.rs              # Backend Rust
├── Cargo.toml              # Dependencias Rust
├── tauri.conf.json         # Configuracion Tauri
└── target/                 # Binarios compilados"""
    
    pdf.multi_cell(0, 5, structure)
    pdf.ln(8)
    
    # 3. Ejecución en Modo Desarrollo
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '2. Ejecución en Modo Desarrollo', 0, 1)
    
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, '2.1 Método Manual', 0, 1)
    
    pdf.set_text_color(*COLOR_CODE)
    pdf.set_font('Courier', '', 10)
    manual_exec = """cd ./src-tauri
cargo tauri dev"""
    
    pdf.multi_cell(0, 5, manual_exec)
    pdf.ln(5)
    
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, '2.2 Metodo 2: Script Automatico', 0, 1)
    
    pdf.set_text_color(*COLOR_CODE)
    pdf.set_font('Courier', '', 10)
    auto_exec = """cd .
python launch_fina_rust.py"""
    
    pdf.multi_cell(0, 5, auto_exec)
    pdf.ln(8)
    
    # 4. Problemas Comunes y Soluciones
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '3. Problemas Comunes y Soluciones', 0, 1)
    
    problems = [
        {
            "error": "no such command: 'tauri'",
            "causa": "Tauri CLI no instalado",
            "solucion": "cargo install tauri-cli"
        },
        {
            "error": "Property 'toggleWindowMode' was accessed during render but is not defined",
            "causa": "Funcion no expuesta en Vue",
            "solucion": "Agregar al return del componente Vue"
        },
        {
            "error": "address already in use",
            "causa": "Puerto 8000 ya esta en uso",
            "solucion": "sudo lsof -ti:8000 | xargs kill -9"
        }
    ]
    
    for i, problem in enumerate(problems, 1):
        pdf.set_text_color(*COLOR_SUBTITLE)
        pdf.set_font('Arial', 'B', 13)
        pdf.cell(0, 8, f'3.{i} Error: {problem["error"]}', 0, 1)
        
        pdf.set_text_color(*COLOR_TEXT)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 6, f'Causa: {problem["causa"]}', 0, 1)
        pdf.cell(0, 6, f'Solución: {problem["solucion"]}', 0, 1)
        pdf.ln(5)
    
    # 5. Arquitectura Frontend-Backend
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '4. Arquitectura Frontend-Backend', 0, 1)
    
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, '4.1 Backend Rust', 0, 1)
    
    pdf.set_text_color(*COLOR_CODE)
    pdf.set_font('Courier', '', 10)
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
    
    pdf.multi_cell(0, 5, backend_code)
    pdf.ln(5)
    
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, '4.2 Frontend JavaScript', 0, 1)
    
    pdf.set_text_color(*COLOR_CODE)
    pdf.set_font('Courier', '', 10)
    frontend_code = """// Definición de función
const toggleWindowMode = async () => {
    if (window.__TAURI__) {
        const { invoke } = window.__TAURI__.core;
        await invoke('toggle_fullscreen');
    }
};

// Exposición en Vue
return {
    toggleWindowMode,  // <-- Requerido para template
};

// Uso en template
<button @click="toggleWindowMode">MODO VENTANA (F11)</button>"""
    
    pdf.multi_cell(0, 5, frontend_code)
    pdf.ln(8)
    
    # 6. Debugging y Logs
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '5. Debugging y Logs', 0, 1)
    
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, '5.1 Logs de Backend Rust', 0, 1)
    
    pdf.set_text_color(*COLOR_CODE)
    pdf.set_font('Courier', '', 10)
    backend_logs = """#[tauri::command]
fn toggle_fullscreen(window: Window) -> Result<(), String> {
    println!("toggle_fullscreen llamado");  // Log en terminal
    
    match window.is_fullscreen() {
        Ok(is_fullscreen) => {
            println!("Estado actual fullscreen: {}", is_fullscreen);
            // ... más lógica
        }
    }
}"""
    
    pdf.multi_cell(0, 5, backend_logs)
    pdf.ln(5)
    
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, '5.2 Logs de Frontend JavaScript', 0, 1)
    
    pdf.set_text_color(*COLOR_CODE)
    pdf.set_font('Courier', '', 10)
    frontend_logs = """const toggleWindowMode = async () => {
    console.log("toggleWindowMode llamado");  // Log en DevTools
    
    if (window.__TAURI__) {
        console.log("Usando Tauri API");
        const { invoke } = window.__TAURI__.core;
        console.log("Invocando toggle_fullscreen...");
        
        try {
            await invoke('toggle_fullscreen');
            console.log("toggle_fullscreen invocado exitosamente");
        } catch (e) {
            console.error("Fallo switch fullscreen Tauri:", e);
        }
    }
};"""
    
    pdf.multi_cell(0, 5, frontend_logs)
    pdf.ln(8)
    
    # 7. Comandos Útiles
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '6. Comandos Útiles', 0, 1)
    
    commands = [
        ("Desarrollo", "cargo tauri dev"),
        ("Producción", "cargo tauri build"),
        ("Limpiar", "cargo clean"),
        ("Ver procesos", "pgrep -f fina-app"),
        ("Ver puertos", "lsof -i :8000"),
        ("Logs detallados", "RUST_LOG=debug cargo tauri dev")
    ]
    
    for i, (category, command) in enumerate(commands, 1):
        pdf.set_text_color(*COLOR_SUBTITLE)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 6, f'6.{i} {category}', 0, 1)
        
        pdf.set_text_color(*COLOR_CODE)
        pdf.set_font('Courier', '', 10)
        pdf.cell(0, 6, command, 0, 1)
        pdf.ln(4)
    
    # 8. Caso de Estudio: Fix Pantalla Completa
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '7. Caso de Estudio: Fix Pantalla Completa', 0, 1)
    
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 8, 'Problema: F11 funcionaba pero el botón no funcionaba.')
    pdf.ln(2)
    
    pdf.set_text_color(*COLOR_SUBTITLE)
    pdf.set_font('Arial', 'B', 13)
    pdf.cell(0, 8, '7.1 Solución Paso a Paso', 0, 1)
    
    steps = [
        "Instalar Tauri CLI: cargo install tauri-cli",
        "Agregar logs en backend y frontend",
        "Corregir comunicación: Usar invoke",
        "Exponer función en Vue return",
        "Probar ambos métodos (F11 y botón)"
    ]
    
    for i, step in enumerate(steps, 1):
        pdf.set_text_color(*COLOR_TEXT)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 6, f'{i}. {step}', 0, 1)
    
    pdf.ln(5)
    
    pdf.set_text_color(*COLOR_HIGHLIGHT)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Resultado:', 0, 1)
    
    pdf.set_text_color(*COLOR_TEXT)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 6, '✅ F11 funciona\n✅ Botón funciona\n✅ Sin errores\n✅ Logs funcionales')
    pdf.ln(8)
    
    # 9. Recursos Adicionales
    pdf.set_text_color(*COLOR_TITLE)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, '8. Recursos Adicionales', 0, 1)
    
    resources = [
        "Tauri Documentation: https://tauri.app/v1/guides/",
        "Rust Book: https://doc.rust-lang.org/book/",
        "Vue 3 Guide: https://vuejs.org/guide/",
        "Scripts de diagnóstico: debug_fullscreen.py, launch_fina_rust.py"
    ]
    
    for resource in resources:
        pdf.set_text_color(*COLOR_TEXT)
        pdf.set_font('Arial', '', 10)
        pdf.multi_cell(0, 6, f'• {resource}')
    
    pdf.ln(10)
    
    # Footer final
    pdf.set_text_color(*COLOR_HIGHLIGHT)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 8, 'Última actualización: 5 de Enero, 2026', 0, 1, 'C')
    pdf.cell(0, 8, 'Versión: Fina Rust v0.1.1', 0, 1, 'C')
    pdf.cell(0, 8, 'Estado: Fully Functional ✅', 0, 1, 'C')
    
    # Guardar PDF
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Manual_Fina_Rust.pdf")
    pdf.output(output_path)
    print(f"✅ Manual PDF generado en: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_fina_rust_manual()
