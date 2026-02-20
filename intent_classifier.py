# import torch y sentence_transformers movidos a _initialize_model
import logging
import json
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("IntentClassifier")

# Global variables for lazy loading
embedder = None
phrase_embeddings = None
intent_labels = []

def _initialize_model():
    """Initialize the model and embeddings only when needed"""
    global embedder, phrase_embeddings, intent_labels
    
    if embedder is not None:
        return

    import torch
    from sentence_transformers import SentenceTransformer, util
    logger.info("⏳ Initializing intent classifier model (this may take a moment)...")
    
    # Load intents
    INTENTS_PATH = os.path.join(os.path.dirname(__file__), 'intents.json')
    with open(INTENTS_PATH, 'r') as f:
        intents = json.load(f)

    embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

    # Flatten intents into phrases and labels
    intent_phrases = []
    intent_labels = []

    for intent, phrases in intents.items():
        for phrase in phrases:
            intent_phrases.append(phrase.lower().strip())
            intent_labels.append(intent)

    # Precompute embeddings
    phrase_embeddings = embedder.encode(intent_phrases, convert_to_tensor=True)
    logger.info("✅ Intent classifier initialized")

def detect_intent(text, confidence_threshold=0.55):
    """Returns (intent, confidence) using semantic similarity"""
    _initialize_model()
    
    text = text.lower().strip()

    # Regla específica: "noticias" en la tele vs noticias de internet
    if "noticia" in text:
        has_tv_word = any(w in text for w in [" tele", " tv", " televisión", " television"])
        wants_to_watch = "ver las noticias" in text  # ej: "quiero ver las noticias"

        if has_tv_word or wants_to_watch:
            # Forzar que frases tipo "quiero ver las noticias (en la tele)" vayan a TV
            return "tv_set_channel", 0.99
        else:
            # Frases como "dame las noticias", "noticias" sin "tele" van al intent de noticias generales
            return "news", 0.99
            
    # Regla específica: Aire Acondicionado vs TV (Antena de Aire)
    if "aire" in text:
        # Si menciona la tele o "ver", probablemente es la entrada de TV
        if any(w in text for w in ["tele", "tv", "ver", "antena", "entrada"]):
            return "tv_set_input", 0.95
        # "poné el aire", "subí el aire" sin mencionar TV -> Aire Acondicionado (ac_control)
        # La lógica semántica por defecto suele llevarlo a ac_control, pero podemos forzarlo
        if any(w in text for w in ["grados", "temperatura", "frío", "calor", "turbo"]):
            return "ac_control", 0.95

    # Regla específica: Timer (Hardcode para evitar confusión con screenshot)
    if any(p in text for p in ["avísame en", "avisame en", "timer", "cronómetro", "cuenta regresiva"]):
        return "start_timer", 1.0
    import torch
    from sentence_transformers import SentenceTransformer, util
    query_embedding = embedder.encode(text, convert_to_tensor=True)
    cosine_scores = util.pytorch_cos_sim(query_embedding, phrase_embeddings)[0]

    top_score, top_idx = float(cosine_scores.max()), int(cosine_scores.argmax())
    if top_score >= confidence_threshold:
        return intent_labels[top_idx], top_score
    else:
        logger.warning(f"Unrecognized or ambiguous command: '{text}' (score={top_score:.2f})")
        return None, top_score