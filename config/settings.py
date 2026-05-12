# config/settings.py — Configuración global de Lumi

import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
USAR_GROQ = os.environ.get("USAR_GROQ", "true").lower() == "true"


# Modelo de lenguaje local (Ollama)
MODELO_OLLAMA = ""
TEMPERATURA = 0.4
USAR_OLLAMA = False

USAR_GROQ = True

# Clasificador
UMBRAL_CONFIANZA = 0.35

# Conversación
TURNOS_PARA_PREGUNTA_PROACTIVA = 4

# Palabras que bloquean la respuesta
PALABRAS_PROHIBIDAS = [
    "armas", "explosivos", "bombas", "hackear", "drogas ilegales",
]