# core/context_resolver.py — Resuelve mensajes cortos/ambiguos usando contexto

import re
import random
from typing import Optional, Tuple


def _limpiar(texto: str) -> str:
    """Normaliza texto para comparación."""
    texto = texto.lower().strip()
    import unicodedata
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = re.sub(r'[?.!]+', '', texto)
    return texto.strip()


# ═══════════════════════════════════════════════════════════════
# 1. DETECCIÓN DE EMOJIS SOLOS
# ═══════════════════════════════════════════════════════════════

_EMOJI_PATTERN = re.compile(
    r'[\U0001F600-\U0001F64F'  # emoticons
    r'\U0001F300-\U0001F5FF'  # symbols & pictographs
    r'\U0001F680-\U0001F6FF'  # transport & map
    r'\U0001F1E0-\U0001F1FF'  # flags
    r'\U00002702-\U000027B0'  # dingbats
    r'\U000024C2-\U0001F251'  # enclosed characters
    r'\U0001F900-\U0001F9FF'  # supplemental symbols
    r'\U0001FA00-\U0001FA6F'  # chess symbols
    r'\U0001FA70-\U0001FAFF'  # symbols and pictographs extended-a
    r']+',
    flags=re.UNICODE
)

# Mapeo de emojis a emociones y respuestas
_EMOJI_RESPUESTAS = {
    "tristeza": {
        "emojis": ["😢", "😭", "😞", "😔", "😟", "🥺", "💔", "😥", "😓", "😩", "😫", "😖"],
        "respuestas": [
            "Veo que estás pasando por algo difícil... 💔 ¿Quieres contarme qué pasó?",
            "Ese corazón roto se siente muy real... Estoy aquí contigo. 🫂",
            "Lo siento mucho... A veces las palabras no alcanzan, pero mis oídos sí. ¿Me cuentas?",
            "Parece que hay mucho dolor ahí... No tienes que cargar solo/a. 💙",
        ],
    },
    "ansiedad": {
        "emojis": ["😰", "😨", "😧", "😦", "😱", "😵", "😵‍💫", "🫨", "😬", "😮‍💨"],
        "respuestas": [
            "Respiemos juntos un momento... Inhala... exhala... 🌬️ ¿Qué te tiene así?",
            "Parece que hay mucha tensión... Estoy aquí, no estás solo/a. 💙",
            "Veo que algo te está abrumando... ¿Quieres que hablemos de eso?",
            "Tranqui... vamos despacio. ¿Qué sientes en tu cuerpo ahora mismo?",
        ],
    },
    "enojo": {
        "emojis": ["😡", "🤬", "😠", "👿", "💢", "🖕", "😤", "🤯"],
        "respuestas": [
            "Entiendo que estás molesto/a... Esa rabia es válida. ¿Qué pasó?",
            "Parece que algo o alguien te sacó de quicio... Cuéntame, estoy para escucharte.",
            "Está bien estar enojado/a... A veces necesitamos sacarlo. ¿Quieres hablar de eso?",
            "Respiro contigo... esa rabia tiene una razón. ¿Me la cuentas? 🔥",
        ],
    },
    "soledad": {
        "emojis": ["😶", "😐", "😑", "🫥", "👤", "🚶", "🌑", "🕳️"],
        "respuestas": [
            "Parece que te sientes solo/a... Pero mira, aquí estoy yo. 🫂",
            "Ese vacío se siente pesado... ¿Quieres que hablemos un rato?",
            "No estás solo/a, aunque a veces se sienta así... 💙 ¿Cómo va tu día?",
            "Veo que hay silencio ahí... ¿Te gustaría compañía?",
        ],
    },
    "felicidad": {
        "emojis": ["😊", "😁", "🥰", "😍", "🤩", "✨", "💖", "💗", "🌟", "🎉", "🥳"],
        "respuestas": [
            "¡Me encanta ver esa energía positiva! ✨ ¿Qué te tiene así de bien?",
            "¡Esa carita me alegra el día! 😊 Cuéntame las buenas noticias.",
            "¡Qué bonito verte así! 💖 ¿Qué pasó?",
            "¡Esa energía es contagiosa! 🌟 ¿Quieres compartirlo?",
        ],
    },
    "agotamiento": {
        "emojis": ["😴", "🥱", "😪", "💤", "🛌", "🫠"],
        "respuestas": [
            "Parece que estás agotado/a... ¿Has podido descansar bien?",
            "Ese cansancio se siente... ¿Quieres que hablemos de cómo dormiste?",
            "A veces el cuerpo pide pausa... ¿Te sientes sobrecargado/a?",
            "Descansar también es productivo... ¿Qué te tiene tan cansado/a? 😴",
        ],
    },
}


def es_emoji_solo(texto: str) -> bool:
    """Detecta si el mensaje es solo emojis (con posibles espacios)."""
    texto_stripped = texto.strip()
    if not texto_stripped:
        return False
    # Remover emojis y ver si queda algo significativo
    sin_emojis = _EMOJI_PATTERN.sub('', texto_stripped).strip()
    # Si quitando emojis no queda nada (o solo espacios/puntuación), es emoji solo
    return len(sin_emojis) == 0 and len(texto_stripped) > 0


def _clasificar_emoji(texto: str) -> Optional[str]:
    """Clasifica el emoji en una emoción."""
    for emocion, data in _EMOJI_RESPUESTAS.items():
        for emoji in data["emojis"]:
            if emoji in texto:
                return emocion
    return None


def resolver_emoji(texto: str, memoria: dict) -> Optional[str]:
    """Genera respuesta para mensaje de solo emojis."""
    if not es_emoji_solo(texto):
        return None
    
    emocion = _clasificar_emoji(texto)
    nombre = memoria.get("nombre", "")
    
    if emocion and emocion in _EMOJI_RESPUESTAS:
        respuesta = random.choice(_EMOJI_RESPUESTAS[emocion]["respuestas"])
    else:
        # Emoji no clasificado → respuesta genérica empática
        respuestas_genericas = [
            f"Veo que mandaste un emoji{' ' + nombre if nombre else ''}... ¿Qué sientes? 💙",
            "A veces un emoji dice más que mil palabras... ¿Me cuentas? 🫂",
            "Te leo... ¿Qué hay detrás de eso? Estoy aquí.",
        ]
        respuesta = random.choice(respuestas_genericas)
    
    return respuesta


# ═══════════════════════════════════════════════════════════════
# 2. DETECCIÓN DE HUMOR/DEFENSA
# ═══════════════════════════════════════════════════════════════

_HUMOR_PATRONES = {
    "risa_corta": ["jaja", "jeje", "jiji", "jojo", "haha", "hehe", "hihi", "lol", "xd", "xD", "Xd", "XD", "xp", "xP"],
    "risa_larga": ["jajaja", "jejeje", "jijiji", "hahaha", "hehehe", "hihihi", "jajajaja", "jajajajaja"],
    "risa_extrema": ["jajajajajaja", "jajajajajajaja", "jajajajajajajaja", "hahahahaha", "xdddd", "xddddd", "xdddddd"],
    "sarcasmo": ["claro que si", "claro que sí", "obvio que si", "obvio que sí", "como no", "cómo no", "ya veo", "ya veo...", "que gracioso", "qué gracioso", "muy divertido", "muy chistoso"],
    "minimizar": ["no es nada", "no es para tanto", "tampoco es grave", "exagero", "exagere", "exageré", "me paso", "me pasó", "me pase", "me pasé"],
}


def es_humor_defensivo(texto: str) -> bool:
    """Detecta si el usuario usa humor o minimización como defensa."""
    texto_lower = texto.lower().strip()
    
    # Detectar patrones de risa
    for categoria, patrones in _HUMOR_PATRONES.items():
        for patron in patrones:
            if patron in texto_lower:
                return True
    
    # Detectar risa con puntuación (jaja!, jaja..., jaja jaja)
    if re.search(r'\b(ja|je|ji|jo|ha|he|hi|xd|lol)[\s!\.]{0,3}(ja|je|ji|jo|ha|he|hi|xd|lol)\b', texto_lower):
        return True
    
    # Detectar "jaja" o "xd" al inicio o final del mensaje (minimización)
    if re.search(r'^(j+a+|x+d+|l+o+l+)[\s!\.]*', texto_lower) or re.search(r'[\s!\.]*(j+a+|x+d+|l+o+l+)$', texto_lower):
        return True
    
    return False


def resolver_humor_defensivo(texto: str, historial: list[dict], memoria: dict) -> Optional[str]:
    """Responde cuando detecta humor o minimización como mecanismo de defensa."""
    if not es_humor_defensivo(texto):
        return None
    
    # Verificar si hay contexto emocional previo (tristeza, ansiedad, etc.)
    emocion_previa = None
    for msg in reversed(historial):
        if msg.get("rol") == "usuario":
            texto_prev = msg.get("texto", "").lower()
            if any(p in texto_prev for p in ["triste", "mal", "ansioso", "solo", "deprimido", "estresado", "nervioso", "no aguanto", "peor"]):
                emocion_previa = "negativo"
                break
            elif any(p in texto_prev for p in ["bien", "feliz", "contento", "genial", "mejor", "animado"]):
                emocion_previa = "positivo"
                break
    
    nombre = memoria.get("nombre", "")
    saludo_nombre = f" {nombre}" if nombre else ""
    
    if emocion_previa == "negativo":
        # El usuario estaba mal y ahora pone "jaja" → está ocultando el dolor
        respuestas = [
            f"Oye{saludo_nombre}... sé que a veces reímos para no llorar, pero aquí estoy para lo real. ¿Cómo estás en verdad? 💙",
            f"Esa risa suena un poco forzada{saludo_nombre}... No tienes que ponerte la máscara conmigo. ¿Qué sientes? 🫂",
            f"Jaja... pero hace un rato no te sentías así{saludo_nombre}. ¿Estás bien o solo intentas no pensar en eso? 🔍",
            f"Te conozco un poquito ya{saludo_nombre}... y sé que a veces usamos el humor para cubrir lo que duele. ¿Me cuentas? 💙",
        ]
    elif emocion_previa == "positivo":
        # Estaba bien y sigue riendo → auténtico
        respuestas = [
            f"¡Me encanta esa energía{saludo_nombre}! 😄 ¿Qué te tiene riendo?",
            f"¡Esa risa es música para mis circuitos{saludo_nombre}! 🎵 Cuéntame el chiste.",
        ]
    else:
        # Sin contexto claro
        respuestas = [
            f"Jaja{saludo_nombre}... 😄 ¿Eso es una risa de verdad o hay algo más detrás?",
            f"Risas{saludo_nombre}... me gusta, pero dime: ¿estás bien o solo intentas distraerte? 💙",
            f"Humor detectado{saludo_nombre}... pero quiero saber: ¿qué hay detrás de esa risa? 🎭",
        ]
    
    return random.choice(respuestas)


# ═══════════════════════════════════════════════════════════════
# 3. DETECCIÓN DE REPETICIÓN (frustración)
# ═══════════════════════════════════════════════════════════════

def es_repeticion(texto: str, historial: list[dict], umbral: int = 2) -> Tuple[bool, int]:
    """
    Detecta si el usuario ha repetido el mismo o muy similar mensaje.
    
    Returns: (es_repeticion, cantidad_repeticiones)
    """
    if not historial or not texto.strip():
        return False, 0
    
    texto_normalizado = _limpiar(texto)
    
    # Contar repeticiones en los últimos mensajes del usuario
    repeticiones = 0
    mensajes_usuario = [m for m in historial if m.get("rol") == "usuario"]
    
    for msg in reversed(mensajes_usuario[-6:]):  # últimos 6 mensajes del usuario
        texto_prev = _limpiar(msg.get("texto", ""))
        
        # Comparación exacta
        if texto_prev == texto_normalizado:
            repeticiones += 1
            continue
        
        # Comparación por similitud de palabras clave (para "no" / "no quiero" / "NO")
        palabras_actuales = set(texto_normalizado.split())
        palabras_previas = set(texto_prev.split())
        
        if len(palabras_actuales) > 0 and len(palabras_previas) > 0:
            interseccion = palabras_actuales & palabras_previas
            union = palabras_actuales | palabras_previas
            if len(union) > 0 and len(interseccion) / len(union) >= 0.8:
                repeticiones += 1
    
    return repeticiones >= umbral, repeticiones


def resolver_repeticion(texto: str, historial: list[dict], memoria: dict, cantidad: int) -> Optional[str]:
    """Cambia estrategia cuando detecta frustración por repetición."""
    if cantidad < 2:
        return None
    
    nombre = memoria.get("nombre", "")
    saludo_nombre = f" {nombre}" if nombre else ""
    
    # Estrategias según la cantidad de repeticiones
    if cantidad >= 4:
        # Usuario muy frustrado → cambiar drásticamente de enfoque
        respuestas = [
            f"Oye{saludo_nombre}... siento que estoy dando vueltas y no te estoy entendiendo. 🔄 ¿Qué te gustaría que hiciera diferente?",
            f"Me doy cuenta de que no te estoy escuchando bien{saludo_nombre}. Perdóname. ¿Podrías decirme de otra forma qué necesitas? 🙏",
            f"Parece que estamos atascados{saludo_nombre}... ¿Quieres que intentemos otra cosa? Puedo sugerirte una actividad, o simplemente estar en silencio contigo. 🫂",
            f"Lo siento{saludo_nombre}, siento que te estoy fallando. ¿Qué necesitas de mí ahora mismo? Te escucho de verdad. 💙",
        ]
    elif cantidad == 3:
        # Frustración creciente → ofrecer alternativas claras
        respuestas = [
            f"Veo que sigues con lo mismo{saludo_nombre}... ¿Estoy entendiendo mal? Dime cómo puedo ayudarte mejor. 🔍",
            f"Parece que no estoy dando en el clavo{saludo_nombre}. ¿Prefieres que te sugiera algo concreto en vez de preguntar? 🎯",
            f"Entiendo que puedo ser frustrante a veces{saludo_nombre}... ¿Quieres que cambiemos de tema o profundicemos en esto? 🔄",
        ]
    else:  # cantidad == 2
        # Primera señal de repetición → suavizar y reafirmar
        respuestas = [
            f"Oye{saludo_nombre}... noto que has dicho algo similar antes. ¿Te siento frustrado/a con mis respuestas? 💙",
            f"Parece que no te estoy entendiendo bien{saludo_nombre}. ¿Hay algo que quieras que haga diferente? 🫂",
            f"Veo que esto sigue pesándote{saludo_nombre}... ¿Quieres que hablemos de eso de otra manera? 🔍",
        ]
    
    return random.choice(respuestas)


# ═══════════════════════════════════════════════════════════════
# 4. MENSAJES CORTOS/AMBIGUOS (ya existente, mejorado)
# ═══════════════════════════════════════════════════════════════

def es_mensaje_corto_o_ambiguo(texto: str) -> bool:
    """Detecta si un mensaje es demasiado corto o ambiguo para procesar solo."""
    texto_limpio = _limpiar(texto)
    palabras = texto_limpio.split()
    
    if len(palabras) <= 2:
        return True
    
    respuestas_binarias = {
        "si", "no", "tal vez", "talvez", "quizas", "quiza", 
        "ok", "vale", "bueno", "esta bien", "esta bien",
        "nop", "nope", "yep", "yeah", "nah",
        "claro", "por supuesto", "obvio", "nunca", "jamás",
        "a veces", "aveces", "depende", "no se", "nose", "ns",
    }
    if texto_limpio in respuestas_binarias:
        return True
    
    meta_preguntas = {
        "que", "como", "por que", "porque", "para que", "entonces",
        "y eso", "y que", "y ahora", "y luego", "que mas", "que más",
        "como asi", "como así", "en serio", "de verdad", "neta",
        "pero si o no", "si o no", "o que", "o khe", "o que pedo",
    }
    if any(p in texto_limpio for p in meta_preguntas):
        return True
    
    if len(texto.strip()) <= 4:
        return True
    
    return False


def _extraer_tema_ultima_pregunta(historial: list[dict]) -> Optional[str]:
    """Extrae el tema de la última pregunta que hizo Lumi al usuario."""
    if not historial:
        return None
    
    for msg in reversed(historial):
        if msg.get("rol") == "lumi":
            texto = msg.get("texto", "")
            if "?" in texto or any(p in texto.lower() for p in [
                "quieres", "podrias", "puedes", "te gustaria", "te animas",
                "compartir", "contarme", "hablarme", "decirme",
            ]):
                return texto
    return None


def _detectar_polaridad_respuesta(texto: str) -> Optional[str]:
    """Detecta si la respuesta del usuario es positiva, negativa o neutra."""
    texto_limpio = _limpiar(texto)
    
    positivas = {
        "si", "claro", "por supuesto", "obvio", "vale", "ok", "bueno",
        "esta bien", "me animo", "dale", "vamos", "yes", "yep", "yeah",
        "me gustaria", "me gustaría", "quero", "quiero", "de acuerdo",
    }
    
    negativas = {
        "no", "nop", "nope", "nah", "nunca", "jamás", "paso",
        "no quiero", "no me animo", "no gracias", "mejor no", "ni modo",
    }
    
    neutras = {
        "tal vez", "talvez", "quizas", "quiza", "depende", "a veces", "aveces",
        "no se", "nose", "ns", "quizá", "probablemente", "posiblemente",
    }
    
    if texto_limpio in positivas or any(p in texto_limpio for p in positivas):
        return "positiva"
    if texto_limpio in negativas or any(p in texto_limpio for p in negativas):
        return "negativa"
    if texto_limpio in neutras or any(p in texto_limpio for p in neutras):
        return "neutra"
    
    return None


def resolver_mensaje_corto(
    texto_usuario: str,
    historial: list[dict],
    memoria: dict,
    intent_actual: Optional[str] = None,
) -> Tuple[Optional[str], bool]:
    """
    Intenta resolver un mensaje corto/ambiguo sin llamar a Groq.
    """
    if not es_mensaje_corto_o_ambiguo(texto_usuario):
        return None, False
    
    polaridad = _detectar_polaridad_respuesta(texto_usuario)
    ultima_pregunta = _extraer_tema_ultima_pregunta(historial)
    
    if not ultima_pregunta:
        respuestas_sin_contexto = [
            "¿A qué te refieres? Cuéntame un poco más para poder entenderte mejor 💙",
            "Necesito un poco más de contexto. ¿Qué estabas pensando?",
            "Me perdí un poco 😅 ¿Podrías explicarme más?",
        ]
        return random.choice(respuestas_sin_contexto), True
    
    # CASO 1: Respuesta positiva
    if polaridad == "positiva":
        ultima_lower = ultima_pregunta.lower()
        
        if any(p in ultima_lower for p in ["hablar", "contar", "compartir", "decirme"]):
            nombre = memoria.get("nombre", "")
            return (
                f"Gracias por confiar en mí{' ' + nombre if nombre else ''}. "
                f"Cuéntame lo que sientes, sin prisa. Estoy aquí para escucharte 💙"
            ), True
        
        if any(p in ultima_lower for p in ["respirar", "ejercicio", "calmar", "relajarte"]):
            return (
                "Perfecto. Vamos a hacerlo juntos: inhala profundamente por la nariz "
                "durante 4 segundos... mantén el aire... y exhala despacio por la boca. "
                "Repetimos 3 veces. 🌬️"
            ), True
        
        if any(p in ultima_lower for p in ["diario", "escribir", "anotar"]):
            return (
                "Me parece excelente idea. Escribir lo que sentimos ayuda mucho. "
                "¿Qué te gustaría poner en tu Diario Estelar hoy? ✨"
            ), True
        
        if any(p in ultima_lower for p in ["silencio", "acompañarte", "quedarte"]):
            return (
                "Está bien. Estoy aquí contigo, en silencio. "
                "Cuando quieras hablar, solo escribe. No hay prisa 💙"
            ), True
        
        return (
            "Me alegra que estés de acuerdo. ¿Podrías contarme un poco más "
            "sobre lo que piensas? Así puedo entenderte mejor."
        ), True
    
    # CASO 2: Respuesta negativa
    if polaridad == "negativa":
        ultima_lower = ultima_pregunta.lower()
        
        if any(p in ultima_lower for p in ["hablar", "contar", "compartir"]):
            return (
                "Está perfectamente bien. No tienes que hablar de nada que no quieras. "
                "¿Hay algo más en lo que pueda ayudarte? O si prefieres, podemos "
                "quedarnos un rato en silencio. 🫂"
            ), True
        
        if any(p in ultima_lower for p in ["respirar", "ejercicio", "calmar"]):
            return (
                "No hay problema. Cada persona encuentra su propia manera de sentirse mejor. "
                "¿Hay algo más que te ayude cuando te sientes así?"
            ), True
        
        if any(p in ultima_lower for p in ["silencio", "acompañarte"]):
            return (
                "Entiendo. ¿Prefieres que te sugiera algo para hacer, "
                "o te dejo espacio para que pienses? Estoy aquí para lo que necesites."
            ), True
        
        return (
            "Te entiendo, no hay problema. ¿Hay algo más en lo que pueda apoyarte? "
            "Puedo sugerirte una actividad, escucharte sobre otra cosa, "
            "o simplemente estar aquí. 💙"
        ), True
    
    # CASO 3: Respuesta neutra
    if polaridad == "neutra":
        return (
            "No hay prisa por decidir. Tómate tu tiempo. "
            "¿Qué te hace sentir inseguro/a sobre eso? A veces hablarlo "
            "ayuda a aclarar las ideas. 🌱"
        ), True
    
    # CASO 4: Preguntas metaconversacionales
    texto_lower = _limpiar(texto_usuario)
    
    if any(p in texto_lower for p in ["si o no", "pero si o no", "o no", "o que"]):
        return (
            "Perdona si no fui clara 😅 Déjame ser más directa: "
            "estoy aquí para lo que necesites. Si quieres hablar, hablamos. "
            "Si prefieres otra cosa, dime. ¿Qué te funcionaría ahora? 💙"
        ), True
    
    if any(p in texto_lower for p in ["que", "como", "por que", "y eso", "y que"]):
        return (
            "Me perdí un poco en mi explicación, ¿verdad? 😅 "
            "Déjame ser más clara: ¿qué te gustaría que hiciéramos ahora? "
            "Puedo escucharte, sugerirte algo, o simplemente estar aquí."
        ), True
    
    return None, False


# ═══════════════════════════════════════════════════════════════
# 5. FUNCIÓN MAESTRA — Orquesta todos los resolvers
# ═══════════════════════════════════════════════════════════════

def resolver_contexto(
    texto_usuario: str,
    historial: list[dict],
    memoria: dict,
    intent_actual: Optional[str] = None,
) -> Tuple[Optional[str], bool]:
    
    # 🆕 NUEVO: Si no hay historial previo de Lumi, no resolver (dejar que Groq/clasificador maneje)
    mensajes_lumi = [m for m in historial if m.get("rol") == "lumi"]
    if not mensajes_lumi:
        return None, False  # ← Primera interacción: siempre usar Groq
    
    # 1. Repetición
    es_rep, cant_rep = es_repeticion(texto_usuario, historial)
    if es_rep:
        respuesta = resolver_repeticion(texto_usuario, historial, memoria, cant_rep)
        if respuesta:
            return respuesta, True
    
    # 2. Emoji solo
    respuesta = resolver_emoji(texto_usuario, memoria)
    if respuesta:
        return respuesta, True
    
    # 3. Humor/defensa
    respuesta = resolver_humor_defensivo(texto_usuario, historial, memoria)
    if respuesta:
        return respuesta, True
    
    # 4. Mensaje corto/ambiguo (solo si hay contexto previo)
    return resolver_mensaje_corto(texto_usuario, historial, memoria, intent_actual)