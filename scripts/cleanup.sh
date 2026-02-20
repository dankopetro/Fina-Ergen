# REDIRECCIÓN AL NUEVO JANITOR (Alternativa Superior)
# 1. Llamar al NUEVO Conserje de Python (Alternativa Superior)
# El contenido original de cleanup.sh ha sido desactivado a favor de scripts/janitor.py
PYTHON_BIN="python3"
if [ -f "scripts/janitor.py" ]; then
    $PYTHON_BIN scripts/janitor.py
fi
exit 0
