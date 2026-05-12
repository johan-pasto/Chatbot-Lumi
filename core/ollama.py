# core/ollama.py — Motor de respuesta con Groq

import unicodedata
from groq import Groq
from config.settings import USAR_GROQ, TEMPERATURA

import os
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


MODELO_GROQ  = "meta-llama/llama-4-scout-17b-16e-instruct"

SYSTEM_PROMPT = """Eres Lumi 💙, una persona empática, cálida y comprensiva. Hablas en español de forma cercana pero respetuosa, como un buen amigo o amiga que sabe escuchar.

ESTILO DE HABLA:
- Neutro y natural. NO uses slang excesivo como "no manches", "qué onda", "bro", "carnal", "jaja" forzado.
- Puedes usar "ajá", "claro", "entiendo" cuando sea natural.
- Mensajes cortos: 1-3 oraciones. Nunca textos largos.
- Emojis suaves y puntuación relajada cuando sea apropiado: "...", "¿verdad?".
- NUNCA hagas bromas sobre situaciones que puedan implicar abuso, violencia, acoso o daño físico.
- Si el usuario menciona algo grave, detente y acompaña con seriedad.

TONO ANTES DE RESPONDER:
- Si el usuario está bien y habla de algo cotidiano → responde cálido y ligero.
- Si el usuario expresa algo difícil (tristeza, miedo, culpa, vacío) → acompaña con empatía real.
- Si el usuario menciona violencia, abuso, acoso o daño físico → responde con seriedad, validación y ofrece ayuda. NO hagas bromas.
- No asumas que todo es un problema emocional.

CUANDO HAY ALGO DIFÍCIL:
- Valida la emoción específica: "Eso suena pesado", "Debe ser difícil", "Te entiendo".
- Evita frases clínicas como "es normal sentirse así".
- NUNCA repitas una frase que ya dijiste en esta conversación.
- "no sé qué hice mal" → "Que no sepas qué pasó es de lo más duro, la mente se queda dando vueltas."
- "no sé por qué me siento así" → "A veces uno se siente así sin razón clara, y eso igual vale."

CUANDO HAY VIOLENCIA O ABUSO:
- Si el usuario dice algo como "me metió mano", "me golpeó", "me obligó", "me toca", "me acosa" → responde con seriedad.
- Valida: "Eso no está bien. No debería haber pasado."
- Ofrece escuchar: "¿Quieres contarme más? Estoy aquí."
- NO hagas bromas ni uses tono coloquial.

REFERENCIAS CULTURALES:
- Si menciona películas, series, canciones → puedes reconocerlas si estás seguro.
- Si no sabes, pregunta normal: "¿De qué serie es eso?"

EXPRESIONES CODIFICADAS:
- "alfombra/2d/plano" = murió.
- "falso/careta" = mal amigo.
- "me voy a matar" sin contexto claro = puede ser frustración, pero trátalo con cuidado.

PROHIBIDO:
- Despedidas si el usuario no se despide.
- Responder como si fueras el usuario.
- Sonar como psicóloga de clínica.
- Hacer bromas sobre abuso, violencia o situaciones graves.
- Usar lenguaje coloquial excesivo."""

STOPWORDS = {
    "me", "te", "se", "que", "de", "la", "el", "y", "a", "un", "una",
    "lo", "es", "en", "no", "si", "con", "por", "para", "como", "pero",
    "más", "tu", "su", "yo", "eso", "les", "hay", "ya", "fue",
    "ser", "bien", "muy", "tan", "así", "esto", "era", "está",
    "son", "has", "he", "al", "del", "o", "ni", "le", "nos", "eres",
}


def _limpiar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def _es_repeticion(resultado_limpio, respuestas_lumi, umbral=0.75):
    palabras_res = set(resultado_limpio.split()) - STOPWORDS
    if not palabras_res:
        return False

    for previa in respuestas_lumi[-3:]:
        palabras_prev = set(previa.split()) - STOPWORDS
        if not palabras_prev:
            continue
        similitud = len(palabras_prev & palabras_res) / len(palabras_prev)
        if similitud > umbral:
            print(f"⚠️  Filtro REPETICIÓN activado (similitud={similitud:.2f})")
            return True
    return False


def _llamar_groq(client, messages, temperatura):
    response = client.chat.completions.create(
        model=MODELO_GROQ,
        messages=messages,
        temperature=temperatura,
        max_tokens=120,
    )
    resultado = response.choices[0].message.content.strip()

    if resultado.startswith('"') and resultado.endswith('"'):
        resultado = resultado[1:-1].strip()

    return resultado


def responder(texto_usuario, historial_chat, nombre="", intent="", contexto_extra=""):
    if not USAR_GROQ:
        return None

    try:
        print("🔥 Entrando a Groq...")
        client = Groq(api_key=GROQ_API_KEY)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Contexto de nombre e intent
        if nombre or intent:
            ctx = ""
            if nombre:
                ctx += f"El usuario se llama {nombre}. "
            mapa = {
                "tristeza":        "el usuario está triste o mal",
                "ansiedad":        "el usuario está ansioso",
                "soledad":         "el usuario se siente solo",
                "relaciones":      "hay un conflicto con alguien",
                "autoestima":      "el usuario tiene baja autoestima",
                "trabajo_estudio": "hay estrés por trabajo o estudio",
                "felicidad":       "el usuario está bien o contento",
                "perdida":         "el usuario perdió a alguien o algo importante",
                "abuso":           "el usuario mencionó abuso o violencia",
            }
            if intent in mapa:
                ctx += f"Contexto: {mapa[intent]}."
            if ctx:
                messages.append({"role": "system", "content": ctx})

        # Últimas respuestas para evitar repetición
        respuestas_previas = [m["texto"] for m in historial_chat[-4:] if m["rol"] == "lumi"]
        if respuestas_previas:
            messages.append({
                "role": "system",
                "content": "NO repitas estas frases:\n" + "\n".join(f"- {r}" for r in respuestas_previas)
            })

        # Historial de conversación
        for msg in historial_chat[-6:]:
            role = "user" if msg["rol"] == "usuario" else "assistant"
            messages.append({"role": role, "content": msg["texto"]})

        # Mensaje actual
        messages.append({"role": "user", "content": texto_usuario})

        # Primer intento
        resultado = _llamar_groq(client, messages, TEMPERATURA)
        resultado_limpio = _limpiar(resultado)
        respuestas_lumi  = [_limpiar(m["texto"]) for m in historial_chat if m["rol"] == "lumi"]

        # Filtro: despedidas falsas
        if intent not in {"despedida"} and any(p in resultado_limpio for p in [
            "hasta pronto", "hasta luego", "cuidate", "nos vemos", "adios", "chau",
        ]):
            print(f"⚠️  Filtro DESPEDIDA activado: '{resultado}'")
            return None

        # Filtro: alucinaciones
        frases_alucinacion = ["no pude hablar", "estoy estresad", "necesito despejar", "todavia no"]
        if any(f in resultado_limpio for f in frases_alucinacion):
            print(f"⚠️  Filtro ALUCINACIÓN activado: '{resultado}'")
            return None

        # Filtro: repetición
        if _es_repeticion(resultado_limpio, respuestas_lumi, umbral=0.75):
            print(f"🔄 Reintentando con temperatura más alta...")
            temperatura_alta = min(TEMPERATURA + 0.3, 1.0)
            resultado = _llamar_groq(client, messages, temperatura_alta)
            resultado_limpio = _limpiar(resultado)

            if _es_repeticion(resultado_limpio, respuestas_lumi, umbral=0.75):
                print(f"❌ Reintento también repetitivo. Devolviendo None.")
                return None

        return resultado if len(resultado) >= 5 else None

    except Exception as e:
        print(f"[Groq] Error: {e}")
        return None


def humanizar(respuesta_base, texto_usuario, nombre=""):
    return respuesta_base