import logging
import json
import os
import gc
import utils

os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Usar el logger del sistema (ya configurado en utils si se importa desde main)
logger = logging.getLogger("IntentClassifier")
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
logging.getLogger('transformers').setLevel(logging.WARNING)

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
    
    lang = utils.get_sys_lang()
    logger.info(f"⏳ Initializing intent classifier ({lang}) model...")
    
    # Load intents based on language
    intents_file = f'intents-{lang}.json'
    INTENTS_PATH = os.path.join(os.path.dirname(__file__), intents_file)
    
    if not os.path.exists(INTENTS_PATH):
        logger.warning(f"⚠️ {intents_file} not found, falling back to intents-es.json")
        INTENTS_PATH = os.path.join(os.path.dirname(__file__), 'intents-es.json')

    with open(INTENTS_PATH, 'r') as f:
        intents = json.load(f)

    embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cpu')
    embedder.show_progress_bar = False # Desactivar barras en el cargado si aplica

    # Flatten intents into phrases and labels
    intent_phrases = []
    intent_labels = []

    for intent, phrases in intents.items():
        for phrase in phrases:
            intent_phrases.append(phrase.lower().strip())
            intent_labels.append(intent)

    # Precompute embeddings
    phrase_embeddings = embedder.encode(intent_phrases, convert_to_tensor=True, show_progress_bar=False)
    
    # Liberar memoria de strings temporales
    del intent_phrases
    gc.collect()
    
    logger.info(f"✅ Intent classifier initialized ({len(intent_labels)} phrases)")

def detect_intent(text, confidence_threshold=0.55):
    """Returns (intent, confidence) using semantic similarity"""
    _initialize_model()
    
    text = text.lower().strip()
    
    # Regla específica: "noticias" vs noticias de internet
    news_words = ["noticia", "news", "nouvelles", "nachrichten", "ニュース", "新闻"]
    if any(w in text for w in news_words):
        tv_words = ["tele", "tv", "televisión", "television", "télé", "fernseher", "テレビ", "电视"]
        watch_words = ["ver", "watch", "regarder", "sehen", "見る", "看"]
        
        if any(w in text for w in tv_words) or any(w in text for w in watch_words):
            return "tv_set_channel", 0.99
        else:
            return "news", 0.99
            
    # Regla específica: Aire Acondicionado vs TV (Antena de Aire)
    ac_words = ["aire", "air", "clim", "klima", "エアコン", "空调"]
    if any(w in text for w in ac_words):
        tv_trigger = ["tele", "tv", "ver", "antena", "entrada", "entrée", "input", "テレビ", "电视"]
        if any(w in text for w in tv_trigger):
            return "tv_set_input", 0.95
        
        ac_trigger = ["grados", "degrees", "temp", "frío", "calor", "turbo", "cold", "heat", "温度", "冷", "热"]
        if any(w in text for w in ac_trigger):
            return "ac_control", 0.95

    # Regla específica: Timer
    timer_words = ["avísame en", "avisame en", "timer", "cronómetro", "cuenta regresiva", "minuteur", "timer", "タイマー", "计时器"]
    if any(p in text for p in timer_words):
        return "start_timer", 1.0

    from sentence_transformers import util
    query_embedding = embedder.encode(text, convert_to_tensor=True, show_progress_bar=False)
    cosine_scores = util.pytorch_cos_sim(query_embedding, phrase_embeddings)[0]

    top_score, top_idx = float(cosine_scores.max()), int(cosine_scores.argmax())
    
    # Limpieza rápida
    del query_embedding
    
    if top_score >= confidence_threshold:
        return intent_labels[top_idx], top_score
    else:
        logger.warning(f"Unrecognized or ambiguous command: '{text}' (score={top_score:.2f})")
        return None, top_score