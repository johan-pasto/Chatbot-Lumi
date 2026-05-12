# core/lumi_engine.py — Lumi como clase reutilizable para el servidor

import re
import random
import unicodedata
import time

from core.clasificador import cargar_clasificador, cargar_embeddings, obtener_intent
from core.memoria import (
    cargar_memoria, guardar_memoria, agregar_intencion,
    registrar_emocion, registrar_tema, registrar_pregunta,
    es_primera_vez_hoy, ha_pasado_mucho_tiempo, emocion_predominante,
)
from core.responder import (
    detectar_crisis, respuesta_crisis, respuesta_linea_ayuda,
    construir_respuesta, detectar_palabra_desconocida, es_emocion_general,
)
from core.ollama import responder, humanizar
from core.crypto import encrypt_message, decrypt_message  # 🔒 Encriptación
from config.settings import PALABRAS_PROHIBIDAS


def _limpiar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    return texto


def _viola_reglas(texto):
    return any(p in _limpiar(texto) for p in PALABRAS_PROHIBIDAS)


def _extraer_nombre(texto):
    """
    Extrae el nombre del USUARIO cuando se presenta explícitamente.
    NO extrae nombres de terceros mencionados en contexto.
    """
    patrones = [
        (r'\bme llamo\s+([a-záéíóúñü]{2,20})\b', 1),
        (r'\bmi nombre es\s+([a-záéíóúñü]{2,20})\b', 1),
        (r'\bsoy\s+([a-záéíóúñü]{2,20})\b', 1),
    ]
    blacklist = {
        "un", "falso", "feliz", "triste", "ansioso", "amigo", "amiga",
        "solo", "nueva", "nuevo", "muy", "bien", "mal", "una", "el", "la",
        "que", "por", "con", "para", "del", "al", "lo", "le", "te", "me",
        "se", "es", "en", "su", "tu", "mi", "yo", "nos", "les",
    }
    
    for patron, grupo in patrones:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            nombre = match.group(grupo).lower()
            if nombre not in blacklist:
                return nombre.capitalize()
    return None


def _detectar_abuso(texto):
    """
    Detecta menciones de abuso, violencia o acoso.
    """
    texto_limpio = _limpiar(texto)
    indicadores_abuso = [
        "me metio mano", "me metió mano", "me toco", "me tocó",
        "me golpeo", "me golpeó", "me obligo", "me obligó",
        "me violo", "me violó", "me acosa", "me acosan",
        "me maltrata", "me pega", "me amenaza", "me forzo", "me forzó",
        "abuso de mi", "abusó de mí", "abusaron de mi",
        "me tocaron", "me manoseo", "me manoseó",
        "me encerraron", "me quitaron", "me robaron",
    ]
    return any(ind in texto_limpio for ind in indicadores_abuso)


class LumiChatbot:
    def __init__(self, user_id="default"):
        self.user_id = user_id
        self.memoria = cargar_memoria(user_id)

        if es_primera_vez_hoy(self.memoria) or ha_pasado_mucho_tiempo(self.memoria):
            self.memoria["sesiones"] = self.memoria.get("sesiones", 0) + 1

        guardar_memoria(self.user_id, self.memoria)

        self.modelo, self.vectorizer = cargar_clasificador()
        self.sentence_model, self.embeddings, self.etiquetas_emb = cargar_embeddings()

        from config.settings import USAR_GROQ
        self.usar_groq = USAR_GROQ

        self.historial_chat = []
        self.turnos_sin_pregunta = 0
        self.crisis_activa = False
        self.crisis_pais_solicitado = False
        self.crisis_pais_dado = False

    def _agregar_historial(self, rol, texto):
        # 🔒 Encriptar antes de guardar
        texto_encriptado = encrypt_message(texto)
        self.historial_chat.append({"rol": rol, "texto": texto_encriptado})
        if len(self.historial_chat) > 20:
            self.historial_chat.pop(0)

    def _leer_historial_para_contexto(self) -> list[dict]:
        """
        Desencripta el historial para usarlo como contexto en el modelo.
        """
        historial_desencriptado = []
        for msg in self.historial_chat:
            try:
                historial_desencriptado.append({
                    "rol": msg["rol"],
                    "texto": decrypt_message(msg["texto"])
                })
            except Exception:
                continue
        return historial_desencriptado

    def saludo_inicial(self):
        nombre = self.memoria.get("nombre")
        sesiones = self.memoria.get("sesiones", 0)

        if nombre and sesiones > 1:
            if not es_primera_vez_hoy(self.memoria):
                msg = f"Hola de nuevo, {nombre}. ¿Cómo sigues?"
            elif ha_pasado_mucho_tiempo(self.memoria):
                msg = f"{nombre}, hacía tiempo que no hablábamos. ¿Cómo estuviste?"
            else:
                msg = f"Hola, {nombre}. ¿Cómo estás hoy?"
        elif nombre:
            msg = f"Hola, {nombre}. ¿Cómo estás?"
        else:
            msg = "Hola, soy Lumi 💙 Estoy aquí para escucharte. ¿Cómo te llamas?"

        emocion = emocion_predominante(self.memoria)
        extra = ""
        if emocion in ["tristeza", "ansiedad", "soledad"] and sesiones > 1:
            extra = f" Últimamente hemos hablado de {emocion}. Aquí estoy si quieres seguir."

        return msg + extra

    def responder_usuario(self, entrada: str) -> str:
        entrada = entrada.strip()
        if not entrada:
            return "¿Estás ahí? Toma tu tiempo."

        # 0. DETECCIÓN DE ABUSO/VIOLENCIA (antes que todo)
        if _detectar_abuso(entrada):
            self._agregar_historial("usuario", entrada)
            respuesta = random.choice([
                "Eso que me cuentas no está bien. No debería haber pasado.",
                "Lamento mucho escuchar eso. Eso es algo grave y no es tu culpa.",
                "Gracias por confiarme esto. Eso suena muy difícil.",
            ])
            self._agregar_historial("lumi", respuesta)
            self.memoria = agregar_intencion(self.memoria, "abuso")
            self.memoria = registrar_emocion(self.memoria, "ansiedad")
            guardar_memoria(self.user_id, self.memoria)
            return respuesta

        # 1. Crisis suicida
        if detectar_crisis(entrada):
            from data.respuestas import respuestas
            respuesta = random.choice(respuestas["crisis"])
            self._agregar_historial("usuario", entrada)
            self._agregar_historial("lumi", respuesta)
            self.memoria = agregar_intencion(self.memoria, "crisis")
            guardar_memoria(self.user_id, self.memoria)
            self.crisis_activa = True
            self.crisis_pais_solicitado = True
            self.crisis_pais_dado = False
            return respuesta

        # 2. Post-crisis
        if self.crisis_activa:
            entrada_lower = _limpiar(entrada)

            from data.respuestas import lineas_crisis, paises_keywords

            # 2a. Si el usuario dice un país → dar número de línea de ayuda
            pais_detectado = None
            numero_crisis = None

            for pais, keywords in paises_keywords.items():
                if any(kw in entrada_lower for kw in keywords):
                    if pais in lineas_crisis:
                        info = lineas_crisis[pais]
                        numero_crisis = (
                            f"{info['nombre']}: {info['numero']}. "
                            f"{info['detalle']}"
                        )
                        pais_detectado = pais
                        break

            if numero_crisis:
                respuesta = (
                    f"Acá tienes el número para {pais_detectado.capitalize()}: "
                    f"{numero_crisis}\n\n"
                    f"No estás solo/a en esto 💙"
                )
                self._agregar_historial("usuario", entrada)
                self._agregar_historial("lumi", respuesta)
                self.crisis_pais_dado = True
                guardar_memoria(self.user_id, self.memoria)
                return respuesta

            # 2b. Si ya dio el número y el usuario habla de algo más → salir de crisis
            if self.crisis_pais_dado:
                self.crisis_activa = False
                self.crisis_pais_solicitado = False
                self.crisis_pais_dado = False

            # 2c. Si dice "no", "no quiero", rechazo → empatía y mantener crisis
            elif any(p in entrada_lower for p in ["no", "nadie", "no quiero", "no se", "paso", "despues"]):
                if not self.crisis_pais_dado:
                    respuesta = random.choice([
                        "Está bien, no tienes que hacerlo ahora. Pero acuérdate: no estás solo/a. ¿Hay alguien cerca con quien puedas hablar?",
                        "Te entiendo. A veces uno no quiere hablar. Pero si cambias de opinión, aquí estoy.",
                    ])
                    self._agregar_historial("usuario", entrada)
                    self._agregar_historial("lumi", respuesta)
                    guardar_memoria(self.user_id, self.memoria)
                    return respuesta

            # 2d. Si está emocionalmente mal → seguir en crisis
            elif any(p in entrada_lower for p in ["mal", "triste", "solo", "sola", "vacio", "peor", "no aguanto", "desesperado", "odio", "miedo"]):
                respuesta = random.choice([
                    "Aquí estoy yo. ¿Qué está pasando?",
                    "Entiendo. ¿Cómo estás en este momento?",
                    "Eso suena pesado. ¿Desde cuándo te sientes así?",
                ])
                self._agregar_historial("usuario", entrada)
                self._agregar_historial("lumi", respuesta)
                guardar_memoria(self.user_id, self.memoria)
                return respuesta

            # 2e. Si parece que ya está mejor → desactivar crisis
            elif any(p in entrada_lower for p in ["mejor", "bien", "gracias", "ok", "vale", "tranquilo", "calma"]):
                self.crisis_activa = False
                self.crisis_pais_solicitado = False
                self.crisis_pais_dado = False
                respuesta = random.choice([
                    "Me alegra escuchar eso. 💙",
                    "Bueno, eso me deja más tranquila. ¿De qué quieres hablar?",
                ])
                self._agregar_historial("usuario", entrada)
                self._agregar_historial("lumi", respuesta)
                guardar_memoria(self.user_id, self.memoria)
                return respuesta

            # 2f. Default: salir de crisis y dejar que flujo normal maneje
            else:
                self.crisis_activa = False
                self.crisis_pais_solicitado = False
                self.crisis_pais_dado = False

        # 3. Línea de ayuda
        linea = respuesta_linea_ayuda(entrada)
        if linea:
            self._agregar_historial("usuario", entrada)
            self._agregar_historial("lumi", linea)
            return linea

        # 4. Salida
        if _limpiar(entrada) in {"salir", "exit", "quit", "bye", "adios", "chau"}:
            from data.respuestas import respuestas
            respuesta = random.choice(respuestas['despedida'])
            self._agregar_historial("usuario", entrada)
            self._agregar_historial("lumi", respuesta)
            guardar_memoria(self.user_id, self.memoria)
            return respuesta

        # 5. Filtro
        if _viola_reglas(entrada):
            return "Prefiero mantener la conversación en un espacio seguro. ¿De qué más quieres hablar?"

        # 6. Nombre (solo si el usuario se presenta explícitamente)
        if not self.memoria.get("nombre"):
            nombre = _extraer_nombre(entrada)
            if nombre:
                self.memoria["nombre"] = nombre
                guardar_memoria(self.user_id, self.memoria)
                respuesta = random.choice([
                    f"Hola, {nombre}. ¿Cómo estás?",
                    f"Qué tal, {nombre}. ¿Cómo te encuentras?",
                    f"Hola, {nombre}. ¿Cómo va el día?",
                ])
                self._agregar_historial("usuario", entrada)
                self._agregar_historial("lumi", respuesta)
                return respuesta

        # 7. Clasificar intent
        intent, _ = obtener_intent(
            entrada, self.modelo, self.vectorizer,
            self.sentence_model, self.embeddings, self.etiquetas_emb,
        )

        entrada_lower = _limpiar(entrada)

        if intent in {"saludo", "como_estas"}:
            if any(p in entrada_lower for p in ["mal", "triste", "decaido", "no bien", "pesimo", "horrible", "fatal", "deprimido"]):
                intent = "tristeza"
            elif any(p in entrada_lower for p in ["bien", "feliz", "contento", "genial", "excelente", "mejor", "animado"]):
                intent = "felicidad"
            elif any(p in entrada_lower for p in ["ansioso", "nervioso", "estresado", "agobiado", "preocupado", "angustiado"]):
                intent = "ansiedad"
            elif any(p in entrada_lower for p in ["solo", "sola", "abandonado", "aislado", "desconectado"]):
                intent = "soledad"

        if intent == "cuerpo_salud" and es_emocion_general(entrada):
            intent = "tristeza" if entrada_lower.strip() in {
                "mal", "muy mal", "bastante mal", "fatal", "horrible", "pesimo", "no muy bien",
            } else "felicidad"

        if any(p in entrada_lower for p in [
            "murio", "fallecio", "se murio", "lo perdi", "la perdi",
            "quedo plano", "quedo tieso", "ya no esta", "en un lugar mejor",
            "lo atropellaron", "la atropellaron", "muerto", "muerta",
            "lo enterramos", "la enterramos", "descanse en paz",
        ]):
            intent = "perdida"

        # 8. Memoria
        self.memoria = agregar_intencion(self.memoria, intent)
        if intent in {"tristeza", "ansiedad", "soledad", "autoestima", "felicidad"}:
            self.memoria = registrar_emocion(self.memoria, intent)
        if intent in {"dormir", "trabajo_estudio", "relaciones", "cuerpo_salud"}:
            self.memoria = registrar_tema(self.memoria, intent)

        # 9. Historial (encriptado)
        self._agregar_historial("usuario", entrada)

        # 🔥 NUEVO: Resolver contexto antes de Groq (emojis, humor, repetición, cortos)
        from core.context_resolver import resolver_contexto
        
        # Obtener historial desencriptado para el resolver
        historial_contexto = self._leer_historial_para_contexto()
        
        respuesta_resuelta, fue_resuelto = resolver_contexto(
            texto_usuario=entrada,
            historial=historial_contexto,
            memoria=self.memoria,
            intent_actual=intent,
        )
        
        if fue_resuelto and respuesta_resuelta:
            # Validar seguridad
            if _viola_reglas(respuesta_resuelta):
                respuesta_resuelta = "Prefiero mantener una conversación segura. ¿De qué más quieres hablar?"
            
            self._agregar_historial("lumi", respuesta_resuelta)
            guardar_memoria(self.user_id, self.memoria)
            return respuesta_resuelta

        # 10. Generar respuesta con Groq (solo si NO fue resuelto por contexto)
        respuesta_final = None
        intentos_groq = 0
        max_intentos = 2

        # Actualizar historial de contexto para Groq
        historial_contexto = self._leer_historial_para_contexto()

        while intentos_groq < max_intentos and respuesta_final is None:
            try:
                respuesta_final = responder(
                    texto_usuario=entrada,
                    historial_chat=historial_contexto,
                    nombre=self.memoria.get("nombre", ""),
                    intent=intent,
                )

                if respuesta_final:
                    resp_lower = respuesta_final.lower()
                    if intent != "despedida" and any(p in resp_lower for p in [
                        "hasta pronto", "hasta luego", "cuidate", "cuídate",
                        "nos vemos", "adios", "chau", "bye", "hasta mañana",
                    ]):
                        respuesta_final = None

            except Exception as e:
                print(f"[Groq] Error en intento {intentos_groq + 1}: {e}")
                respuesta_final = None

            if respuesta_final is None:
                intentos_groq += 1
                if intentos_groq < max_intentos:
                    time.sleep(1)

        if respuesta_final is None:
            aclaracion = detectar_palabra_desconocida(entrada, self.memoria)
            if aclaracion:
                respuesta_final = aclaracion
            else:
                respuesta_base, hizo_pregunta = construir_respuesta(
                    entrada, intent, self.memoria, self.turnos_sin_pregunta, historial_contexto,
                )
                self.turnos_sin_pregunta = 0 if hizo_pregunta else self.turnos_sin_pregunta + 1

                if hizo_pregunta:
                    self.memoria = registrar_pregunta(self.memoria, respuesta_base)

                respuesta_final = humanizar(
                    respuesta_base, entrada, nombre=self.memoria.get("nombre", "")
                )

        # 11. Seguridad
        if _viola_reglas(respuesta_final):
            respuesta_final = "Prefiero mantener una conversación segura. ¿De qué más quieres hablar?"

        # 12. Guardar respuesta en historial (encriptada)
        self._agregar_historial("lumi", respuesta_final)
        guardar_memoria(self.user_id, self.memoria)

        return respuesta_final