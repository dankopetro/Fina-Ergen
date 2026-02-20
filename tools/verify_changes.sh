#!/bin/bash
# Script de Verificación de Cambios - Fina Ergen
# Verifica que todas las correcciones estén aplicadas

BASE_DIR="."

echo "🔍 VERIFICANDO CAMBIOS EN FINA ERGEN ($BASE_DIR)..."
echo ""

ERRORS=0
WARNINGS=0

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar doorbell_monitor.py en main.py
echo "1️⃣  Verificando lanzamiento de Weston+Waydroid..."
if grep -q "doorbell_monitor.py" "$BASE_DIR/main.py"; then
    echo -e "${GREEN}✓ doorbell_monitor.py configurado correctamente${NC}"
else
    echo -e "${RED}✗ FALLO: doorbell_monitor.py NO encontrado en main.py${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 2. Verificar "Intente de nuevo"
echo ""
echo "2️⃣  Verificando mensaje 'Intente de nuevo'..."
if grep -q 'speak("Intente de nuevo."' "$BASE_DIR/main.py"; then
    echo -e "${GREEN}✓ Mensaje 'Intente de nuevo' restaurado${NC}"
else
    echo -e "${RED}✗ FALLO: Mensaje 'Intente de nuevo' NO encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 3. Verificar eventos de voz en utils.py
echo ""
echo "3️⃣  Verificando emisión de eventos de voz..."
if grep -q '"fina-state"' "$BASE_DIR/utils.py"; then
    echo -e "${GREEN}✓ Eventos JSON de voz configurados${NC}"
else
    echo -e "${YELLOW}⚠ ADVERTENCIA: Eventos de voz no encontrados en utils.py${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 4. Verificar sección de Seguridad en App.vue
echo ""
echo "4️⃣  Verificando pestaña de Seguridad..."
if grep -q "activeSettingsDomain === 'seguridad'" "$BASE_DIR/src/App.vue"; then
    echo -e "${GREEN}✓ Pestaña de Seguridad presente${NC}"
else
    echo -e "${RED}✗ FALLO: Pestaña de Seguridad NO encontrada${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 5. Verificar botón de Registrar Contraseña
echo ""
echo "5️⃣  Verificando botón de Contraseña Maestra..."
if grep -q "registerMasterPassword" "$BASE_DIR/src/App.vue"; then
    echo -e "${GREEN}✓ Botón de Contraseña Maestra configurado${NC}"
else
    echo -e "${RED}✗ FALLO: Botón de Contraseña Maestra NO encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 6. Verificar botón de Escanear Apps
echo ""
echo "6️⃣  Verificando botón de Escanear Apps de TV..."
if grep -q "Escanear Apps Instaladas" "$BASE_DIR/src/App.vue"; then
    echo -e "${GREEN}✓ Botón de Escanear Apps presente${NC}"
else
    echo -e "${RED}✗ FALLO: Botón de Escanear Apps NO encontrado${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 7. Verificar sección de Canales Manuales
echo ""
echo "7️⃣  Verificando sección de Canales Manuales..."
if grep -q "Canales Guardados" "$BASE_DIR/src/App.vue" || grep -q "Gestion de Canales" "$BASE_DIR/src/App.vue" || grep -q "Canales" "$BASE_DIR/src/App.vue"; then
    echo -e "${GREEN}✓ Sección de Gestión de Canales presente${NC}"
else
    echo -e "${RED}✗ FALLO: Sección de Canales NO encontrada${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 8. Verificar animación de anillos pulsantes
echo ""
echo "8️⃣  Verificando animación de anillos al hablar..."
if grep -q "speechAnimationInterval" "$BASE_DIR/src/App.vue"; then
    echo -e "${GREEN}✓ Animación de anillos configurada${NC}"
else
    echo -e "${RED}✗ FALLO: Animación de anillos NO encontrada${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 9. Verificar GLOBAL_ROOT en main.py
echo ""
echo "9️⃣  Verificando variable GLOBAL_ROOT..."
if grep -q "GLOBAL_ROOT =" "$BASE_DIR/main.py"; then
    echo -e "${GREEN}✓ GLOBAL_ROOT configurada${NC}"
else
    echo -e "${RED}✗ FALLO: GLOBAL_ROOT NO encontrada${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 10. Verificar que el build de frontend esté actualizado
echo ""
echo "🔟 Verificando build del frontend..."
if [ -f "$BASE_DIR/dist/index.html" ]; then
    BUILD_TIME=$(stat -c %Y "$BASE_DIR/dist/index.html")
    CURRENT_TIME=$(date +%s)
    TIME_DIFF=$((CURRENT_TIME - BUILD_TIME))
    
    if [ $TIME_DIFF -lt 600 ]; then  # Menos de 10 minutos
        echo -e "${GREEN}✓ Build del frontend actualizado (hace $((TIME_DIFF / 60)) minutos)${NC}"
    else
        echo -e "${YELLOW}⚠ ADVERTENCIA: Build tiene más de 10 minutos. Considera ejecutar 'npm run build'${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠ ADVERTENCIA: No se encontró build del frontend${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Resumen final
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 RESUMEN DE VERIFICACIÓN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ TODOS LOS CAMBIOS VERIFICADOS CORRECTAMENTE${NC}"
    echo ""
    echo "🚀 Fina Ergen está lista para lanzarse."
    echo "   Ejecutá desde el menú o con: npm run tauri dev"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  VERIFICACIÓN COMPLETA CON ADVERTENCIAS${NC}"
    echo -e "   Errores críticos: ${GREEN}0${NC}"
    echo -e "   Advertencias: ${YELLOW}${WARNINGS}${NC}"
    echo ""
    echo "Los cambios están aplicados pero hay advertencias menores."
    exit 0
else
    echo -e "${RED}❌ VERIFICACIÓN FALLIDA${NC}"
    echo -e "   Errores críticos: ${RED}${ERRORS}${NC}"
    echo -e "   Advertencias: ${YELLOW}${WARNINGS}${NC}"
    echo ""
    echo "Algunos cambios NO se aplicaron correctamente."
    echo "Revisá los errores arriba y contactá al desarrollador."
    exit 1
fi
