
import sys
import os
import logging

# Setup basic logging to see what happens
logging.basicConfig(level=logging.INFO)

# Configurar ruta para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Importar la función mágica
from utils import show_doorbell_stream

print("🤖 SIMULACIÓN: Usuario dice 'Muéstrame la cámara de la puerta'")
print("-------------------------------------------------------------")

# Ejecutar la función (usando 'None' para el modelo de voz por simplicidad, usará el default)
show_doorbell_stream(selected_model=None)

print("\n✅ Prueba finalizada. Revisa si se abrió VLC y el archivo en el escritorio.")
