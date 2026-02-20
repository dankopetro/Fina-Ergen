#!/usr/bin/env python3
"""
Script para corregir líneas cortadas en App.vue
Busca patrones de Vue que están partidos en múltiples líneas y los une en una sola línea.
"""
import re
import sys

def fix_vue_multiline_expressions(filepath):
    """Corrige expresiones Vue partidas en múltiples líneas"""
    
    # Leer el archivo
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Patrón 1: {{ mobileHelpContext === 'missing' ? 'texto...' : 'texto...' }}
    pattern1 = r"(\{\{ mobileHelpContext === 'missing' \? ')([^']+)('\s*:\s*')([^']+)('\s*\}\})"
    
    def fix_multiline(match):
        prefix = match.group(1)
        text1_raw = match.group(2)
        middle = match.group(3)
        text2_raw = match.group(4)
        suffix = match.group(5)
        
        # Limpiar saltos de línea y espacios extras
        text1 = ' '.join(text1_raw.split())
        text2 = ' '.join(text2_raw.split())
        
        return f"{prefix}{text1}{middle}{text2}{suffix}"
    
    content = re.sub(pattern1, fix_multiline, content, flags=re.DOTALL)
    
    # Escribir de vuelta solo si hubo cambios
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Líneas cortadas corregidas en App.vue")
        return True
    else:
        print("✓ No se encontraron líneas cortadas")
        return False

if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else "./src/App.vue"
    fix_vue_multiline_expressions(filepath)
