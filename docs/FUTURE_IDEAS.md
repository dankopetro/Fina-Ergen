# Ideas Futuras para Fina (Ciencia Ficción)

## 1. Presencia Holográfica
- Integrar con un proyector o pantalla transparente para que Fina tenga un "avatar" visual que te sigue con la mirada (usando la webcam y face tracking).
- Usar **Live2D** o modelos 3D en la ventana Tauri que reaccionan a tu tono de voz (feliz, preocupada).

## 2. Comprensión Contextual Multimodal
- Fina no solo escucha, **VE**.
- Usar la webcam para detectar si estás sosteniendo un objeto. "Fina, ¿qué es esto que tengo en la mano?" -> Usa Vision LLM para identificarlo.
- Detectar si te has ido de la habitación para pausar la música automáticamente.

## 3. "Echo" Mental (Memoria a Largo Plazo con RAG)
- Fina recuerda todo lo que le has dicho hace meses.
- "Fina, ¿dónde te dije que dejé las llaves la semana pasada?"
- "Fina, recomiéndame una película parecida a esa que vimos el mes pasado".
- Implementar base de datos vectorial (ChromaDB) local para almacenar "recuerdos".

## 4. Automatización Proactiva (Minority Report)
- Fina predice lo que vas a pedir.
- Si todos los viernes a las 22:00 pides pizza, a las 21:50 te pregunta: "¿Pido lo de siempre?".
- Si detecta que el clima empeora, te avisa antes de que preguntes: "Va a llover, cierra la ventana".

## 5. Clonación de Voz en Tiempo Real
- Que Fina pueda imitar voces famosas para leer noticias o contar chistes (ya medio posible con ElevenLabs, pero local y low-latency).

## 6. Interfaz Neuronal (Futuro Lejano)
- Integración con dispositivos BCI (Brain Computer Interface) simples para comandos mentales básicos ("Apagar luz") sin hablar.

## 7. Domótica Local Premium (Planeado para Fase 2)
- **Timbre Tuya Instantáneo**: 
  - Usar `tinytuya` con Local Key y IP Estática (ya obtenidos).
  - Reemplazar el monitoreo actual por detección directa de paquetes LAN.
  - Latencia cero en la notificación de "Alguien toca la puerta".

