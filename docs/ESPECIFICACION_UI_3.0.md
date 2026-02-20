# Fina Ergen UI 3.0: "Visual Domain Expansion"

**Fecha:** 05/02/2026
**Versión Objetivo:** Fina-Ergen v3.0

## 1. Introducción
Este documento detalla la reestructuración completa de la interfaz de visualización de Fina, transformándola de un panel informativo estático a un "Centro de Comando" dinámico y segmentado por dominios. El objetivo es lograr una experiencia "Premium" con estéticas glassmorphism, animaciones fluidas y alta interactividad.

## 2. Nuevos Módulos Principales

### 2.1 Módulo Agenda (Voice-Driven Schedule)
*   **Función:** Visualización del calendario diario.
*   **Interacción:** Carga y recarga mediante comandos de voz ("Fina, ¿qué tengo hoy?", "Agrega una reunión...").
*   **Estética:** Tarjetas translúcidas sobre fondo oscuro/neón, línea de tiempo vertical.
*   **Estado:** Siempre visible o invocado por voz.

### 2.2 Centro de Entretenimiento (Media Domain)
*   **Función:** Gestión de dispositivos multimedia (TV, Servidores, Audio).
*   **Display:**
    *   Grilla de Apps (YouTube, Netflix, Spotify).
    *   Estado de conexión ("Online" verde brillante).
    *   Barra de búsqueda universal.
*   **Control:** Navegación por voz y visualización de canales disponibles.

### 2.3 Monitor Climatológico (Weather Deep-Dive)
*   **Función:** Extensión visual del reporte de clima.
*   **Display:**
    *   Estado actual con iconos de neón grandes.
    *   Pronóstico extendido (5 días).
    *   Detalles: Humedad, Viento, Sensación térmica.
    *   Animaciones de lluvia/tormenta en segundo plano.

### 2.4 Monitor de Sistema (System Stats)
*   **Función:** Dashboard de salud del hardware donde reside Fina (PC, Server, Raspberry).
*   **Métricas:**
    *   CPU (Carga, Temp).
    *   RAM (Uso/Total).
    *   Tráfico de Red (Gráfico en tiempo real visualmente atractivo).
    *   Almacenamiento.

### 2.5 Configuración Unificada (Settings Domain)
Un panel central que dirige a 4 sub-dominios:
1.  **Intelligence Domain:** Ajustes de IA (LLMs, TTS, STT).
2.  **Security Domain:** Mapa de red, logs de intrusión, cámaras.
3.  **Visual Domain:** Temas, fondos, configuración de pantallas.
4.  **Habitat Domain:** Domótica (Termostato, Luces, Escenas).

### 2.6 Nueva Identidad Visual (Avatares Dinámicos)
*   **Concepto:** "Corazón Digital".
*   **Comportamiento:**
    *   **Activo:** Orbe/Corazón que fluctúa y rota al ritmo de la voz.
    *   **Idle/Dormida:** Modo "Screensaver" donde el orbe rebota suavemente por la pantalla (como DVD screensaver) con opacidad reducida.
    *   **Escucha:** Cambio de color y pulsación rápida.

## 3. Guía de Estilos Técnicos
*   **CSS:** Vanilla CSS con variables para paletas de colores.
*   **Efectos:** `backdrop-filter: blur()`, `box-shadow` con colores neón, gradientes lineales suaves.
*   **Tipografía:** 'Outfit' o 'Inter' (Google Fonts).
*   **Animaciones:** CSS Keyframes para "breathing", rotación y rebote.

## 4. Implementación
La implementación se realizará creando componentes Vue modulares en `src/components/` y orquestándolos desde `App.vue` mediante un sistema de navegación por pestañas/dominios.
