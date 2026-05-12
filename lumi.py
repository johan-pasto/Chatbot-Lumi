# lumi.py — Punto de entrada del chatbot

import re
import random
import unicodedata
import time

from core.clasificador import cargar_clasificador, cargar_embeddings, obtener_intent, corregir_tipeos
from core.memoria import (
    cargar_memoria, guardar_memoria, agregar_intencion,
    registrar_emocion, registrar_tema,
    ha_pasado_mucho_tiempo, es_primera_vez_hoy, emocion_predominante,
)
from core.responder import (
    detectar_crisis, respuesta_crisis, respuesta_linea_ayuda,
    construir_respuesta, detectar_palabra_desconocida, es_emocion_general,
)
from core.ollama import responder, humanizar
from config.settings import PALABRAS_PROHIBIDAS

# Palabras que solas indican muerte/pérdida
_PALABRAS_MUERTE = {
    "murio", "fallecio", "muerto", "muerta", "alfombra", "aplastado",
    "aplastada", "atropellaron", "enterramos", "2d", "chato", "frito",
}
# Frases completas de muerte/pérdida
_FRASES_PERDIDA = {
    "se murio", "se fue", "lo perdi", "la perdi", "ya no esta",
    "en un lugar mejor", "estiro la pata", "se nos fue", "lo perdimos",
    "la perdimos", "ya no respira", "no aguanto", "no resistio",
    "se fue al otro lado", "ya no esta con nosotros", "descanse en paz",
    "perdi a mi", "perdi mi",
}


def limpiar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def es_perdida(texto_lower):
    palabras = set(texto_lower.split())
    if palabras & _PALABRAS_MUERTE:
        return True
    return any(f in texto_lower for f in _FRASES_PERDIDA)


def viola_reglas(texto):
    return any(p in limpiar(texto) for p in PALABRAS_PROHIBIDAS)


def extraer_nombre(texto):
    patrones = [
        r'\bme llamo\s+([a-záéíóúñü]{2,20})\b',
        r'\bmi nombre es\s+([a-záéíóúñü]{2,20})\b',
        r'\bsoy\s+([A-ZÁÉÍÓÚÑÜ][a-záéíóúñü]{2,20})\b',
    ]
    blacklist = {
        "un", "falso", "feliz", "triste", "ansioso", "amigo", "amiga",
        "solo", "nueva", "nuevo", "muy", "bien", "mal", "una",
    }
    for patron in patrones:
        match = re.search(patron, texto)
        if match:
            nombre = match.group(1)
            if nombre.lower() not in blacklist:
                return nombre.capitalize()
    return None


def agregar_al_historial(historial, rol, texto):
    historial.append({"rol": rol, "texto": texto})
    if len(historial) > 20:
        historial.pop(0)


def mostrar_bienvenida(memoria):
    nombre = memoria.get("nombre")
    sesiones = memoria.get("sesiones", 0)

    print("\n" + "─" * 48)
    print("      💙  LUMI  —  Tu espacio seguro  💙")
    print("─" * 48)

    if nombre and sesiones > 1:
        if not es_primera_vez_hoy(memoria):
            print(f"\nHola de nuevo, {nombre}. ¿Cómo sigues?")
        elif ha_pasado_mucho_tiempo(memoria):
            print(f"\n{nombre}, hacía tiempo que no hablábamos. ¿Cómo estuviste?")
        else:
            print(f"\nHola, {nombre}. ¿Cómo estás hoy?")
    elif nombre:
        print(f"\nHola, {nombre}. ¿Cómo estás?")
    else:
        print("\nHola, soy Lumi. 💙")
        print("Estoy aquí para escucharte. ¿Cómo te llamas?")

    emocion = emocion_predominante(memoria)
    if emocion in ["tristeza", "ansiedad", "soledad"] and sesiones > 1:
        print(f"\n(Últimamente hemos hablado de {emocion}. Aquí estoy si quieres seguir.)")

    print("\n(Escribe 'salir' para terminar)")
    print("─" * 48 + "\n")


def verificar_groq():
    """Verifica si Groq está disponible. Se puede llamar en cada mensaje."""
    try:
        import requests
        from config.settings import MODELO_OLLAMA
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": MODELO_OLLAMA, "prompt": "hola", "stream": False,
                  "options": {"num_predict": 1}},
            timeout=5,  # Timeout corto para no bloquear
        )
        return r.status_code == 200
    except Exception:
        return False


def _respuesta_post_crisis(entrada_lower):
    no_hay_nadie = any(p in entrada_lower for p in ["no", "nadie", "solo", "sola"])
    hay_alguien = any(p in entrada_lower for p in ["si", "mama", "papa", "amigo", "pareja", "hermano", "hermana"])
    if no_hay_nadie:
        return random.choice([
            "Aquí estoy yo. ¿Qué está pasando?",
            "Entiendo. ¿Cómo estás en este momento?",
            "Okey. ¿Me cuentas qué pasó?",
        ])
    if hay_alguien:
        return random.choice(["Bien. ¿Cómo estás ahora?", "Me alegra. ¿Cómo te sientes?"])
    return "¿Cómo estás ahora mismo?"


def main():
    usuario_id = "usuario_1"  # o algo dinámico luego
    
    # Cargar memoria UNA VEZ al inicio
    memoria = cargar_memoria(usuario_id)
    memoria["sesiones"] = memoria.get("sesiones", 0) + 1
    
    # Guardar inmediatamente la sesión incrementada
    guardar_memoria(usuario_id, memoria)

    modelo, vectorizer = cargar_clasificador()
    sentence_model, embeddings, etiquetas_emb = cargar_embeddings()

    mostrar_bienvenida(memoria)

    print("[Groq] ✅ Usando modelo en la nube")
    
    historial_chat = []
    turnos_sin_pregunta = 0
    crisis_activa = False

    while True:
        try:
            entrada = input("Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nLumi: Cuídate. 💙")
            guardar_memoria(usuario_id, memoria)
            break

        if not entrada:
            print("Lumi: ¿Estás ahí? Toma tu tiempo.\n")
            continue

        # 1. Crisis
        if detectar_crisis(entrada):
            respuesta = respuesta_crisis(entrada)
            print(f"Lumi: {respuesta}\n")
            agregar_al_historial(historial_chat, "usuario", entrada)
            agregar_al_historial(historial_chat, "lumi", respuesta)
            
            # Modificar memoria en RAM y guardar
            memoria = agregar_intencion(memoria, "crisis")
            guardar_memoria(usuario_id, memoria)
            crisis_activa = True
            continue

        # 2. Post-crisis
        if crisis_activa:
            entrada_lower = limpiar(entrada)
            if any(p in entrada_lower for p in ["mal", "triste", "solo", "vacío", "peor"]):
                respuesta = _respuesta_post_crisis(entrada_lower)
                print(f"Lumi: {respuesta}\n")
                agregar_al_historial(historial_chat, "usuario", entrada)
                agregar_al_historial(historial_chat, "lumi", respuesta)
                guardar_memoria(usuario_id, memoria)
                continue
            crisis_activa = False

        # 3. Línea de ayuda
        linea = respuesta_linea_ayuda(entrada)
        if linea:
            print(f"Lumi: {linea}\n")
            agregar_al_historial(historial_chat, "usuario", entrada)
            agregar_al_historial(historial_chat, "lumi", linea)
            continue

        # 4. Salida
        if limpiar(entrada) in {"salir", "exit", "quit", "bye", "adios", "chau"}:
            from data.respuestas import respuestas
            print(f"Lumi: {random.choice(respuestas['despedida'])}")
            guardar_memoria(usuario_id, memoria)
            break

        # 5. Filtro
        if viola_reglas(entrada):
            print("Lumi: Prefiero mantener la conversación en un espacio seguro. ¿De qué más quieres hablar?\n")
            continue

        # 6. Nombre
        if not memoria.get("nombre"):
            nombre_detectado = extraer_nombre(entrada)
            if nombre_detectado:
                memoria["nombre"] = nombre_detectado
                guardar_memoria(usuario_id, memoria)
                print(f"[Sistema: Nombre '{nombre_detectado}' registrado]")

        # 7. Clasificar intent
        entrada_lower = limpiar(corregir_tipeos(entrada))
        intent, _ = obtener_intent(
            entrada, modelo, vectorizer,
            sentence_model, embeddings, etiquetas_emb,
        )

        # Correcciones de intent
        if intent == "cuerpo_salud" and es_emocion_general(entrada):
            intent = "tristeza" if entrada_lower.strip() in {
                "mal", "muy mal", "bastante mal", "fatal", "horrible", "pesimo", "no muy bien",
            } else "felicidad"

        if es_perdida(entrada_lower):
            intent = "perdida"
        elif any(a in entrada_lower for a in ["gato", "perro", "mascota", "pajaro", "conejo"]):
            if any(c in entrada_lower for c in ["cayo", "se cayo", "se me cayo", "tiro", "salto", "cayo del", "piso"]):
                intent = "perdida"

        # 8. Memoria — Modificar en RAM, guardar al final del turno
        memoria = agregar_intencion(memoria, intent)
        if intent in {"tristeza", "ansiedad", "soledad", "autoestima", "felicidad"}:
            memoria = registrar_emocion(memoria, intent)
        if intent in {"dormir", "trabajo_estudio", "relaciones", "cuerpo_salud"}:
            memoria = registrar_tema(memoria, intent)

        # 9. Historial
        agregar_al_historial(historial_chat, "usuario", entrada)

        # 10. Generar respuesta
        aclaracion = None
        respuesta_final = None
        
        # Intentar Groq con reintentos, NO desactivar permanentemente
        intentos_groq = 0
        max_intentos = 2
        
        while intentos_groq < max_intentos and respuesta_final is None:
            try:
                respuesta_final = responder(
                    texto_usuario=entrada,
                    historial_chat=historial_chat,
                    nombre=memoria.get("nombre", ""),
                    intent=intent,
                )
                
                # Validar que no sea una despedida falsa
                if respuesta_final:
                    resp_lower = limpiar(respuesta_final)
                    if intent != "despedida" and any(p in resp_lower for p in [
                        "hasta pronto", "hasta luego", "cuidate", "nos vemos", "adios", "chau",
                    ]):
                        respuesta_final = None  # Reintentar
                        
            except Exception as e:
                print(f"[Groq] Error en intento {intentos_groq + 1}: {e}")
                respuesta_final = None
            
            if respuesta_final is None:
                intentos_groq += 1
                if intentos_groq < max_intentos:
                    time.sleep(1)  # Esperar antes de reintentar

        # Fallback a respuestas locales SOLO si Groq falló después de reintentos
        if respuesta_final is None:
            aclaracion = detectar_palabra_desconocida(entrada, memoria)
            if aclaracion:
                respuesta_final = aclaracion
            else:
                respuesta_base, hizo_pregunta = construir_respuesta(
                    entrada, intent, memoria, turnos_sin_pregunta, historial_chat,
                )
                turnos_sin_pregunta = 0 if hizo_pregunta else turnos_sin_pregunta + 1
                respuesta_final = humanizar(respuesta_base, entrada, nombre=memoria.get("nombre", ""))

        # 11. Seguridad y mostrar
        if viola_reglas(respuesta_final):
            respuesta_final = "Prefiero mantener una conversación segura. ¿De qué más quieres hablar?"

        agregar_al_historial(historial_chat, "lumi", respuesta_final)
        guardar_memoria(usuario_id, memoria)
        print(f"Lumi: {respuesta_final}\n")


if __name__ == "__main__":
    main()