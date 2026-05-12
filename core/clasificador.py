# core/clasificador.py — Clasificación de intenciones

import unicodedata
import re
import numpy as np
import joblib
import os

from data.intents import intents
from config.settings import UMBRAL_CONFIANZA

USAR_EMBEDDINGS = False

# Los .pkl siempre están en lumi/ (carpeta padre de core/)
_LUMI_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _ruta(nombre):
    return os.path.join(_LUMI_DIR, nombre)


def limpiar_texto(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r'[^a-zñ\s]', '', texto)
    return texto.strip()


# Correcciones de tipeos comunes
_CORRECCIONES = {
    r'\bmorido\b':  'murio',
    r'\bmuerto\b':  'murio',
    r'\bele\b':    'el',
    r'\belas\b':   'las',
    r'\belos\b':   'los',
    r'\blgato\b':  'gato',
    r'\bpero\b':   'perro',
    r'\bgatoo\b':  'gato',
    r'\bgatp\b':   'gato',
    r'\btritse\b': 'triste',
    r'\btrits\b':  'triste',
    r'\bestoi\b':  'estoy',
    r'\bsoto\b':   'solo',
    r'\bsolla\b':  'sola',
    r'\bmsl\b':    'mal',
    r'\bmal\b':    'mal',
}

def corregir_tipeos(texto):
    for patron, reemplazo in _CORRECCIONES.items():
        texto = re.sub(patron, reemplazo, texto)
    # Colapsar letras repetidas: "alfommbra" → "alfombra", "muyyy" → "muy"
    texto = re.sub(r'(.)\1{2,}', r'\1\1', texto)
    return texto


# ──────────────────────────────────────────────
# Carga de modelos
# ──────────────────────────────────────────────

def cargar_clasificador():
    """Carga TF-IDF + Logistic Regression si existen los archivos."""
    modelo_path    = _ruta("modelo.pkl")
    vectorizer_path = _ruta("vectorizer.pkl")
    if os.path.exists(modelo_path) and os.path.exists(vectorizer_path):
        modelo     = joblib.load(modelo_path)
        vectorizer = joblib.load(vectorizer_path)
        print("[Lumi] Modelo TF-IDF cargado ✅")
        return modelo, vectorizer
    print("[Lumi] Modelo no encontrado — usando palabras clave como fallback.")
    print("[Lumi] Ejecuta 'python entrenar.py' para entrenar el modelo.\n")
    return None, None


def cargar_embeddings():
    """Carga embeddings semánticos si existen."""
    global USAR_EMBEDDINGS
    archivos = ["embeddings_entrenamiento.pkl", "etiquetas_embeddings.pkl", "sentence_model_name.txt"]
    if not all(os.path.exists(_ruta(a)) for a in archivos):
        return None, None, None
    try:
        from sentence_transformers import SentenceTransformer
        embeddings = joblib.load(_ruta("embeddings_entrenamiento.pkl"))
        etiquetas  = joblib.load(_ruta("etiquetas_embeddings.pkl"))
        with open(_ruta("sentence_model_name.txt")) as f:
            nombre_modelo = f.read().strip()
        sentence_model = SentenceTransformer(nombre_modelo)
        USAR_EMBEDDINGS = True
        print("[Lumi] Embeddings semánticos cargados ✅")
        return sentence_model, embeddings, etiquetas
    except Exception as e:
        print(f"[Lumi] Embeddings no disponibles: {e}")
        return None, None, None


# ──────────────────────────────────────────────
# Clasificadores
# ──────────────────────────────────────────────

def _tfidf(texto, modelo, vectorizer):
    X = vectorizer.transform([limpiar_texto(texto)])
    try:
        proba = modelo.predict_proba(X)[0]
    except AttributeError:
        # Compatibilidad: modelo viejo tiene multi_class como @property roto
        modelo.__dict__.pop("multi_class", None)
        modelo.__dict__.pop("_multi_class", None)
        proba = modelo.predict_proba(X)[0]
    idx = np.argmax(proba)
    return modelo.classes_[idx], proba[idx]


def _embeddings(texto, sentence_model, embeddings, etiquetas):
    from sklearn.metrics.pairwise import cosine_similarity
    emb  = sentence_model.encode([limpiar_texto(texto)])
    sims = cosine_similarity(emb, embeddings)[0]
    idx  = np.argmax(sims)
    return etiquetas[idx], sims[idx]


def _keywords(texto):
    texto_limpio = limpiar_texto(texto)
    for intent_nombre, frases in intents.items():
        for frase in frases:
            f = limpiar_texto(frase)
            if f in texto_limpio or texto_limpio in f:
                return intent_nombre, 0.8
    for intent_nombre, frases in intents.items():
        palabras_intent  = set(" ".join(frases).split())
        palabras_usuario = set(texto_limpio.split())
        if len(palabras_intent & palabras_usuario) >= 2:
            return intent_nombre, 0.5
    return "no_entendido", 0.0


def obtener_intent(texto, modelo, vectorizer, sentence_model, embeddings, etiquetas_emb):
    """Cascada: TF-IDF → Embeddings → Keywords."""
    texto = corregir_tipeos(texto)
    if modelo and vectorizer:
        intent, conf = _tfidf(texto, modelo, vectorizer)
        if conf >= UMBRAL_CONFIANZA:
            return intent, conf

    if USAR_EMBEDDINGS and sentence_model is not None:
        intent, conf = _embeddings(texto, sentence_model, embeddings, etiquetas_emb)
        if conf >= 0.5:
            return intent, conf

    return _keywords(texto)