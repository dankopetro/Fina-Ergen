# imports pesados movidos a _initialize_classifier internos de ergen

# Global variables for lazy loading
embedder = None
code_classifier = None

def _initialize_classifier():
    """Initialize the classifier only when needed"""
    global embedder, code_classifier
    
    if embedder is not None and code_classifier is not None:
        return

    print("⏳ Inicializando clasificador secundario (esto puede tardar un momento)...")
    from sentence_transformers import SentenceTransformer
    from sklearn.linear_model import LogisticRegression
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Labels
    codeworthy_texts = codeworthy_examples + non_code_examples
    codeworthy_labels = [1] * len(codeworthy_examples) + [0] * len(non_code_examples)

    # Encode the texts
    X_cw = embedder.encode(codeworthy_texts)

    # Train the classifier
    code_classifier = LogisticRegression()
    code_classifier.fit(X_cw, codeworthy_labels)
    print("✅ Clasificador secundario inicializado")

# Function to check if text is code-worthy
def is_code_worthy(text, threshold=0.5):
    _initialize_classifier()
    x = embedder.encode([text])
    prob = code_classifier.predict_proba(x)[0][1]  
    return prob > threshold

# Classification labels:
# 1 = Code-worthy (Requiere código/técnico), 0 = Casual conversation (Conversación casual)

codeworthy_examples = [
    # Tareas de programación generales
    "escribe un script de python", "crea una función para ordenar", "necesito código para esto",
    "cómo hago un bucle for", "genera una clase en java", "implementa un algoritmo de búsqueda",
    "dame un ejemplo de recursión", "escribe un programa que calcule pi", "necesito un script de bash",
    
    # Análisis de datos y visualización
    "dibuja una onda senoidal", "grafica estos datos", "haz un histograma",
    "analiza este archivo csv", "visualiza las ventas mensuales", "crea un gráfico de barras",
    "calcula la media y la desviación estándar", "usa pandas para leer esto",
    
    # Web Scraping y Automatización
    "descarga imágenes de esta url", "haz scraping de esta página web", "automatiza el envío de correos",
    "crea un bot de discord", "extrae datos de este sitio", "automatiza esta tarea repetitiva",
    
    # Sistemas y Archivos
    "lista los archivos en este directorio", "encuentra archivos duplicados", "haz un backup de mi carpeta",
    "renombra estos archivos masivamente", "monitoriza el uso de cpu", "comprime estos videos",
    
    # Algoritmos y Matemáticas
    "calcula la secuencia de fibonacci", "resuelve esta ecuación diferencial", "implementa el cifrado rsa",
    "simula un sistema de partículas", "calcula números primos", "optimiza esta consulta sql",
    
    # Desarrollo Web
    "crea una api rest", "genera un endpoint de webhook", "valida este json",
    "implementa autenticación oauth", "crea una página html simple", "estila esto con css",
    
    # Otros técnicos
    "convierte este markdown a html", "genera un código qr", "traduce este código a c++",
    "explícame cómo funciona este código", "depura este error", "optimiza este algoritmo",
    "crea un diagrama uml", "genera documentación para esto", "implementa un árbol de decisión"
]

non_code_examples = [
    # Saludos y cortesía
    "hola", "buenos días", "buenas tardes", "buenas noches", "¿cómo estás?",
    "qué tal todo", "gracias", "muchas gracias", "de nada", "adiós", "hasta luego",
    
    # Preguntas personales al asistente
    "¿cómo te llamas?", "¿quién te creó?", "¿eres un robot?", "¿tienes sentimientos?",
    "¿cuál es tu color favorito?", "¿qué edad tienes?", "¿te gusta la música?",
    "cuéntame sobre ti", "¿tienes hermanos?", "¿dónde vives?",
    
    # Conversación casual
    "cuéntame un chiste", "dime algo gracioso", "estoy aburrido", "me siento feliz hoy",
    "qué opinas del clima", "hace calor hoy", "está lloviendo mucho",
    "me gusta la pizza", "¿te gusta el chocolate?", "recomiéndame una película",
    "cuéntame una historia", "cántame una canción", "dime una curiosidad",
    
    # Preguntas generales (no técnicas)
    "¿qué hora es?", "¿qué día es hoy?", "¿cuál es el sentido de la vida?",
    "¿existe la suerte?", "¿crees en los fantasmas?", "¿qué es el amor?",
    "dame un consejo", "¿cómo puedo relajarme?", "¿qué es la felicidad?",
    
    # Frases cortas y comandos simples no técnicos
    "repite eso", "no te entendí", "habla más alto", "baja el volumen",
    "para", "detente", "continúa", "siguiente", "anterior",
    "genial", "interesante", "no lo sabía", "increíble", "qué bien",
    
    # Filosofía y opiniones
    "¿qué opinas de la inteligencia artificial?", "¿los robots dominarán el mundo?",
    "la vida es bella", "el tiempo vuela", "todo pasa por algo",
    "me gusta aprender cosas nuevas", "viajar es vivir", "la música es vida"
]
