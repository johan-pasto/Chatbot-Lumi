# entrenar.py — Entrena el clasificador de intenciones de Lumi
"""
Uso:
    python entrenar.py

Genera:
    modelo.pkl, vectorizer.pkl
    embeddings_entrenamiento.pkl, etiquetas_embeddings.pkl  (si sentence-transformers está instalado)
"""

import re
import unicodedata
import numpy as np
import joblib
import os
import sklearn

# Directorio base = donde está este script, sin importar desde dónde se ejecute
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def ruta(nombre):
    return os.path.join(BASE_DIR, nombre)

from data.intents import intents
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

try:
    from sentence_transformers import SentenceTransformer
    USAR_EMBEDDINGS = True
except ImportError:
    USAR_EMBEDDINGS = False
    print("⚠️  sentence-transformers no instalado — solo se usará TF-IDF.")
    print("   Para instalarlo: pip install sentence-transformers\n")


def limpiar_texto(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r'[^a-zñ\s]', '', texto)
    return texto.strip()


# ── Preparar datos ──────────────────────────────────────────────────────────

print("=" * 50)
print("   ENTRENAMIENTO — LUMI")
print("=" * 50)

frases, etiquetas = [], []
for etiqueta, lista in intents.items():
    for frase in lista:
        frases.append(limpiar_texto(frase))
        etiquetas.append(etiqueta)

print(f"\nIntenciones: {len(intents)}")
print(f"Ejemplos:    {len(frases)}\n")


# ── TF-IDF ──────────────────────────────────────────────────────────────────

vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
X = vectorizer.fit_transform(frases)

sklearn_version = tuple(int(x) for x in sklearn.__version__.split(".")[:2])
if sklearn_version >= (1, 5):
    modelo = LogisticRegression(max_iter=1000, C=5.0, solver="lbfgs")
else:
    modelo = LogisticRegression(max_iter=1000, C=5.0, solver="lbfgs", multi_class="auto")

modelo.fit(X, etiquetas)
print(f"Precisión TF-IDF: {modelo.score(X, etiquetas):.2%}")


# ── Embeddings semánticos (opcional) ────────────────────────────────────────

if USAR_EMBEDDINGS:
    print("\nGenerando embeddings (puede tardar la primera vez)...")
    sentence_model = SentenceTransformer("distiluse-base-multilingual-cased-v2")
    embeddings = sentence_model.encode(frases, show_progress_bar=True)
    joblib.dump(embeddings, ruta("embeddings_entrenamiento.pkl"))
    joblib.dump(etiquetas,  ruta("etiquetas_embeddings.pkl"))
    with open(ruta("sentence_model_name.txt"), "w") as f:
        f.write("distiluse-base-multilingual-cased-v2")


# ── Guardar ─────────────────────────────────────────────────────────────────

joblib.dump(vectorizer, ruta("vectorizer.pkl"))
joblib.dump(modelo,     ruta("modelo.pkl"))
joblib.dump(frases,     ruta("frases_entrenamiento.pkl"))
joblib.dump(etiquetas,  ruta("etiquetas_entrenamiento.pkl"))

print("\nArchivos generados:")
for archivo in ["vectorizer.pkl", "modelo.pkl", "frases_entrenamiento.pkl", "etiquetas_entrenamiento.pkl"]:
    p = ruta(archivo)
    if os.path.exists(p):
        kb = os.path.getsize(p) / 1024
        print(f"  ✅ {archivo}  ({kb:.1f} KB)")

print("\n✅ Listo. Ahora puedes ejecutar: python lumi.py")