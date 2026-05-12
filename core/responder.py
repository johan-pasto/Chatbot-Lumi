# core/responder.py — Construcción de respuestas de Lumi

import random
import unicodedata

from data.respuestas import (
    respuestas, preguntas_seguimiento, continuaciones_contexto,
    preguntas_proactivas, lineas_crisis, paises_keywords,
)
from data.intents import palabras_crisis, expresiones_coloquiales_crisis, fillers
from config.settings import TURNOS_PARA_PREGUNTA_PROACTIVA

INTENTS_EMOCIONALES = {
    "tristeza", "ansiedad", "soledad", "autoestima",
    "motivacion", "trabajo_estudio", "relaciones", "dormir",
}

PALABRAS_A_ACLARAR = {
    "falso":       "¿Qué quiso decir con 'falso'? ¿Que no eres buen amigo o que eres deshonesto?",
    "forro":       "¿Qué quieres decir con 'forro'?",
    "careta":      "¿Qué quiso decir con 'careta'?",
    "boludo":      "¿Lo dijo de forma ofensiva?",
    "gil":         "¿Cómo tomaste eso?",
    "rata":        "¿A qué se refería con eso?",
    "intenso":     "¿Te lo dijo de forma negativa?",
    "pesado":      "¿Te llamó 'pesado/a'? ¿Cómo lo tomaste?",
    "awebao":      "¿Cómo te sientes con eso?",
    "awebo":       "¿Cómo te sientes con eso?",
    "aweonao":     "¿Lo dijo de forma ofensiva?",
    "cagado":      "¿En qué sentido lo dijo?",
}

# Contexto que indica que "me voy a matar" es coloquial
_CONTEXTO_COLOQUIAL = [
    "no puedo aguantar", "no puedo creer", "de risa", "de verguenza",
    "de pena", "de amor", "de nervios", "es que", "todo por",
    "no puedo con", "de la emocion", "del susto", "no aguanto",
]


def _limpiar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def detectar_crisis(texto):
    """
    Detecta crisis reales.
    - Expresión coloquial + contexto justificado ("me voy a matar de risa") → NO crisis
    - Expresión ambigua sola ("me voy a matar") → SÍ crisis, más vale prevenir
    - Frases directas ("quiero morir", "me quiero suicidar") → siempre crisis
    """
    texto_lower = texto.lower()

    # Primero verificar frases directas de crisis — siempre son crisis
    if any(p in texto_lower for p in palabras_crisis):
        return True

    # Verificar expresiones ambiguas
    es_ambigua = any(expr in texto_lower for expr in expresiones_coloquiales_crisis)
    if es_ambigua:
        # Solo NO es crisis si hay contexto claramente coloquial
        if any(ctx in texto_lower for ctx in _CONTEXTO_COLOQUIAL):
            return False
        # Sin contexto coloquial = tratar como crisis por seguridad
        return True

    return False


def detectar_pais(texto):
    texto_limpio = _limpiar(texto)
    for pais, keywords in paises_keywords.items():
        if any(k in texto_limpio for k in keywords):
            return pais
    return None


def es_solicitud_linea(texto):
    texto_limpio = _limpiar(texto)
    keywords = [
        "linea de ayuda", "linea de crisis", "numero de ayuda",
        "telefono de ayuda", "donde llamo", "a quien llamo",
        "linea de", "numero de crisis", "linea para", "quiero la linea",
    ]
    return any(k in texto_limpio for k in keywords)


def es_emocion_general(texto):
    texto_lower = _limpiar(texto).strip()
    emociones = {
        "mal", "muy mal", "bastante mal", "fatal", "horrible", "pesimo",
        "no muy bien", "no tan bien", "bien", "regular", "mas o menos",
        "genial", "excelente", "triste", "ansioso", "solo",
    }
    return texto_lower in emociones


def detectar_palabra_desconocida(texto, memoria):
    """Pregunta sobre expresiones coloquiales, pero solo una vez por palabra."""
    texto_limpio = _limpiar(texto).encode("ascii", "ignore").decode("utf-8")
    ya_preguntadas = set(memoria.get("palabras_aclaradas", []))
    for palabra, pregunta in PALABRAS_A_ACLARAR.items():
        if palabra in texto_limpio and palabra not in ya_preguntadas:
            memoria.setdefault("palabras_aclaradas", []).append(palabra)
            return pregunta
    return None


def respuesta_crisis(texto):
    pais = detectar_pais(texto)
    if pais and pais in lineas_crisis:
        info = lineas_crisis[pais]
        return (
            f"Lo que me dices es importante y me preocupa. "
            f"No tienes que cargarlo solo/a.\n\n"
            f"En {pais.capitalize()}: {info['nombre']} — {info['numero']}. "
            f"{info['detalle']}\n\n"
            f"¿Hay alguien cerca de ti ahora mismo?"
        )
    return random.choice(respuestas["crisis"])


def respuesta_linea_ayuda(texto):
    texto_limpio = _limpiar(texto)
    pais = detectar_pais(texto)
    solicitud = es_solicitud_linea(texto)
    if solicitud or (pais and any(k in texto_limpio for k in ["linea", "numero", "telefono", "llamo", "ayuda"])):
        if pais and pais in lineas_crisis:
            info = lineas_crisis[pais]
            return f"En {pais.capitalize()}: {info['nombre']} — {info['numero']}. {info['detalle']}"
        if solicitud:
            lista = "\n".join(
                f"  • {p.capitalize()}: {d['numero']} ({d['nombre']})"
                for p, d in lineas_crisis.items()
            )
            return f"Estas son las líneas de crisis disponibles:\n{lista}\n\n¿De qué país eres?"
    return None


def _preguntas_ya_hechas(historial_chat):
    """Extrae todas las preguntas que Lumi ya hizo en esta sesión."""
    preguntas = set()
    for msg in historial_chat:
        if msg["rol"] == "lumi":
            texto = msg["texto"]
            # Guardar fragmentos de preguntas para detectar repetición
            if "qué pasó" in _limpiar(texto):
                preguntas.add("que_paso")
            if "cómo estás" in _limpiar(texto) or "como estas" in _limpiar(texto):
                preguntas.add("como_estas")
            if "cuéntame" in _limpiar(texto) or "cuentame" in _limpiar(texto):
                preguntas.add("cuentame")
            if "desde cuándo" in _limpiar(texto) or "desde cuando" in _limpiar(texto):
                preguntas.add("desde_cuando")
            if "cómo te afecta" in _limpiar(texto) or "como te afecta" in _limpiar(texto):
                preguntas.add("como_afecta")
            if "hablaste" in _limpiar(texto):
                preguntas.add("hablaste")
    return preguntas


def _elegir_pregunta_seguimiento(intent, preguntas_hechas):
    """Elige una pregunta de seguimiento que no se haya hecho antes."""
    candidatas = preguntas_seguimiento.get(intent, [])
    mapa_bloqueo = {
        "que_paso":      ["qué pasó", "que paso"],
        "como_estas":    ["cómo estás", "como estas"],
        "cuentame":      ["cuéntame", "cuentame"],
        "desde_cuando":  ["desde cuándo", "desde cuando"],
        "como_afecta":   ["cómo te afecta", "como te afecta"],
        "hablaste":      ["hablaste"],
    }
    disponibles = []
    for candidata in candidatas:
        c_lower = _limpiar(candidata)
        bloqueada = False
        for clave, frags in mapa_bloqueo.items():
            if clave in preguntas_hechas and any(f in c_lower for f in frags):
                bloqueada = True
                break
        if not bloqueada:
            disponibles.append(candidata)
    if disponibles:
        return random.choice(disponibles)
    return None


def _elegir_pregunta_proactiva(memoria):
    ya_hechas   = set(memoria.get("preguntas_hechas", []))
    disponibles = [p for p in preguntas_proactivas if p not in ya_hechas]
    if not disponibles:
        disponibles = preguntas_proactivas
        memoria["preguntas_hechas"] = []
    pregunta = random.choice(disponibles)
    memoria.setdefault("preguntas_hechas", []).append(pregunta)
    return pregunta


def _respuestas_ya_usadas(historial_chat):
    """Extrae texto de respuestas que Lumi ya dio."""
    return {_limpiar(msg["texto"]) for msg in historial_chat if msg["rol"] == "lumi"}


def _elegir_sin_repetir(opciones, ya_usadas):
    """Elige una opción que no se haya usado antes. Si todas se usaron, elige cualquiera."""
    disponibles = [o for o in opciones if _limpiar(o) not in ya_usadas]
    return random.choice(disponibles) if disponibles else random.choice(opciones)


def _hay_contexto_real(intent, historial_chat):
    """Devuelve True solo si ya se habló del MISMO tema emocional antes."""
    count = 0
    for msg in historial_chat:
        if msg["rol"] == "lumi":
            txt = _limpiar(msg["texto"])
            if intent == "tristeza" and any(p in txt for p in ["triste", "dificil", "dolor", "pesa"]):
                count += 1
            elif intent == "relaciones" and any(p in txt for p in ["persona", "alguien", "dijo", "hablaste"]):
                count += 1
            elif intent == "ansiedad" and any(p in txt for p in ["nervios", "ansiedad", "calmar"]):
                count += 1
            elif intent == "soledad" and any(p in txt for p in ["solo", "aislad", "acompan"]):
                count += 1
    return count >= 1


def _respuesta_contextual(intent, historial_chat, memoria):
    nombre           = memoria.get("nombre", "")
    historial        = memoria.get("historial_intenciones", [])
    preguntas_hechas = _preguntas_ya_hechas(historial_chat)
    hay_contexto     = _hay_contexto_real(intent, historial_chat)
    ya_usadas        = _respuestas_ya_usadas(historial_chat)

    if hay_contexto and intent in INTENTS_EMOCIONALES:
        validaciones = {
            "tristeza": [
                "Eso suena realmente difícil.",
                "Tiene sentido que te haya afectado.",
                "Es entendible que te haya dolido.",
            ],
            "relaciones": [
                "Que alguien cercano te diga eso duele.",
                "Es duro cuando alguien así te dice algo así.",
            ],
            "ansiedad": [
                "Esa sensación de no poder calmarse es muy incómoda.",
                "Tiene sentido que eso te esté afectando.",
            ],
            "soledad": ["Sentirse así es agotador.", "Eso pesa mucho."],
            "autoestima": [
                "Las palabras de otros pueden quedarse dando vueltas.",
                "Que alguien diga eso duele.",
            ],
        }
        base = _elegir_sin_repetir(validaciones.get(intent, ["Eso suena difícil."]), ya_usadas)

        preguntas_seguidas = sum(1 for i in historial[-3:] if i in INTENTS_EMOCIONALES)
        if preguntas_seguidas < 2:
            pregunta = _elegir_pregunta_seguimiento(intent, preguntas_hechas)
            if pregunta:
                base += f" {pregunta}"

        if nombre and random.random() < 0.15:
            base = f"{nombre}, {base[0].lower()}{base[1:]}"
        return base

    # Primera vez con este intent
    base = _elegir_sin_repetir(respuestas.get(intent, respuestas["no_entendido"]), ya_usadas)

    if nombre and random.random() < 0.15:
        base = f"{nombre}, {base[0].lower()}{base[1:]}"

    if intent in INTENTS_EMOCIONALES and random.random() < 0.25:
        filler = random.choice(fillers)
        base = f"{filler} {base[0].lower()}{base[1:]}"

    if not base.rstrip().endswith("?") and intent in preguntas_seguimiento:
        pregunta = _elegir_pregunta_seguimiento(intent, preguntas_hechas)
        if pregunta:
            base += f" {pregunta}"

    return base


def _usuario_quiere_hablar(texto, historial_chat):
    """
    Detecta si el usuario está abriendo activamente un tema emocional
    (vs solo mencionarlo de paso).
    """
    texto_lower = _limpiar(texto)
    # Señales de que quiere hablar: frases largas, "es que", "estoy", narración
    senales = ["es que", "estoy", "me siento", "me pasa", "tengo", "hoy", "ayer", "desde"]
    return (
        len(texto.split()) >= 4 or
        any(s in texto_lower for s in senales)
    )


def _usuario_cierra_tema(texto_lower):
    """Detecta si el usuario está cerrando el tema — 'nada', 'eso es todo', etc."""
    cierres = {
        "nada", "nada mas", "eso", "eso es todo", "eso nomas", "ya",
        "no nada", "nada mas eso", "solo eso", "nada mas que eso",
    }
    return texto_lower.strip() in cierres or texto_lower.strip().startswith("nada ")


def construir_respuesta(texto, intent, memoria, turnos_sin_pregunta, historial_chat=None):
    """
    Fallback cuando Ollama no está disponible.
    Devuelve (texto_respuesta, se_hizo_pregunta_proactiva).
    """
    if historial_chat is None:
        historial_chat = []

    historial = memoria.get("historial_intenciones", [])
    ultimo_emocional = next(
        (i for i in reversed(historial) if i in INTENTS_EMOCIONALES), None
    )

    # Usuario cierra el tema → soltar y acompañar sin preguntar más
    if _usuario_cierra_tema(_limpiar(texto)) and ultimo_emocional:
        return random.choice([
            "Okey, aquí estoy si se te ocurre algo más.",
            "Dale, no hay apuro.",
            "Entendido. Aquí estoy.",
        ]), False

    # El usuario no entiende algo → volver al hilo
    if intent in {"no_entendido", "respuesta_corta"} and ultimo_emocional:
        texto_lower = _limpiar(texto)
        if any(p in texto_lower for p in ["a que", "que quieres", "no entiendo", "como asi", "que"]):
            return random.choice([
                "Perdona, me perdí. ¿Qué me estabas diciendo?",
                "Me fui por las ramas. ¿Seguimos con lo que me contabas?",
            ]), False
        opciones = continuaciones_contexto.get(ultimo_emocional, [
            "Cuéntame más.",
            "¿Qué más pasó?",
        ])
        return random.choice(opciones), False

    if intent == "respuesta_corta":
        return random.choice([
            "Dale, cuéntame.",
            "¿Cómo así?",
            "¿Qué pasó?",
        ]), False

    # Para intents emocionales: solo profundizar si el usuario claramente quiere hablar
    # Si solo lo menciona de pasada ("malo"), respuesta corta y casual
    if intent in INTENTS_EMOCIONALES and not _usuario_quiere_hablar(texto, historial_chat):
        respuestas_cortas = {
            "tristeza":  ["¿Qué pasó?", "Ay, ¿qué anda mal?", "Cuéntame."],
            "ansiedad":  ["¿Qué te tiene así?", "¿Qué está pasando?"],
            "soledad":   ["¿Qué pasó?", "¿Cómo así?"],
            "autoestima":["¿Por qué dices eso?", "¿Qué pasó?"],
            "relaciones":["¿Qué pasó?", "Cuéntame."],
        }
        opciones = respuestas_cortas.get(intent, ["¿Qué pasó?", "Cuéntame."])
        return random.choice(opciones), False

    # Respuesta completa con contexto
    base = _respuesta_contextual(intent, historial_chat, memoria)

    # Agradecimiento que sigue a un tema emocional → continuar ese hilo
    ultimo = historial[-2] if len(historial) >= 2 else None
    if intent == "agradecimiento" and ultimo in INTENTS_EMOCIONALES:
        base = _respuesta_contextual(ultimo, historial_chat, memoria)

    # Pregunta proactiva solo cuando la conversación se pierde completamente
    if (intent in {"no_entendido", "agradecimiento"}
            and turnos_sin_pregunta >= TURNOS_PARA_PREGUNTA_PROACTIVA
            and random.random() < 0.5):
        pregunta = _elegir_pregunta_proactiva(memoria)
        base += f" {pregunta[0].lower()}{pregunta[1:]}"
        return base, True

    return base, False