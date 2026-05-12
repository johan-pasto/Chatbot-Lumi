# data/respuestas.py — Banco de respuestas de Lumi
# Solo datos: sin imports, sin lógica, sin funciones.

respuestas = {
    "saludo": [
        "Hola, ¿cómo estás?",
        "Hey, ¿qué tal?",
        "Hola. ¿Cómo va todo?",
        "Hey. ¿Qué hay?",
        "Hola, ¿cómo te va?",
    ],
    "despedida": [
        "Cuídate. 💙",
        "Hasta luego. Espero que el resto del día vaya bien.",
        "Nos vemos. Cuídate.",
        "Dale, cuídate. Si necesitas algo, aquí estoy.",
        "Hasta pronto.",
    ],
    "como_estas": [
        "Bien, ¿y tú?",
        "Por aquí bien. ¿Qué tal tú?",
        "Bien. ¿Cómo te va?",
        "Todo bien por acá. ¿Y a ti?",
    ],
    "agradecimiento": [
        "Para eso estoy.",
        "No hay de qué.",
        "Con gusto.",
        "Claro que sí.",
    ],
    "tristeza": [
        "Qué bajón. ¿Qué pasó?",
        "¿Qué anda mal?",
        "Ay, ¿qué pasó?",
        "¿Qué te tiene así?",
        "Cuéntame.",
    ],
    "ansiedad": [
        "Uf, ¿qué te está generando eso?",
        "¿Qué es lo que no te deja tranquilo/a?",
        "¿Hay algo concreto que lo disparó?",
        "¿Qué está pasando?",
    ],
    "soledad": [
        "¿Qué está pasando?",
        "¿Cómo así?",
        "Cuéntame un poco.",
        "¿Desde cuándo te sentís así?",
    ],
    "autoestima": [
        "¿Qué pasó?",
        "¿Por qué dices eso?",
        "Cuéntame más.",
        "¿Qué te hizo sentir así?",
    ],
    "felicidad": [
        "Qué bueno. ¿Qué pasó?",
        "Me alegra. ¿Qué fue?",
        "Buenísimo. Cuéntame.",
        "Eso está bien. ¿Qué pasó?",
    ],
    "motivacion": [
        "¿Qué está costando arrancar?",
        "¿Qué es lo que se siente pesado?",
        "¿Qué está pasando?",
    ],
    "consejos": [
        "Depende de lo que estés viviendo. ¿Qué está pasando?",
        "Cuéntame más.",
        "¿Qué está pasando exactamente?",
    ],
    "dormir": [
        "Dormir mal es un fastidio. ¿Qué pasa cuando intentas dormirte?",
        "¿No puedes conciliar el sueño o te despiertas en la madrugada?",
        "¿Cuánto tiempo llevas así?",
    ],
    "trabajo_estudio": [
        "¿Qué está pasando ahí?",
        "¿Qué es lo que más está pesando?",
        "Eso suena agotador. ¿Qué pasó?",
    ],
    "relaciones": [
        "¿Qué pasó?",
        "Cuéntame.",
        "¿Cómo así?",
        "¿Qué fue lo que dijo o hizo?",
    ],
    "perdida": [
        "Uf, qué bajón. ¿Qué pasó exactamente?",
        "Ay no. ¿Cuándo fue?",
        "Qué difícil eso.",
        "Lo siento. ¿Cómo fue?",
    ],
    "cuerpo_salud": [
        "¿Qué te está pasando?",
        "¿Hace cuánto tienes eso?",
        "¿Y cómo te sientes en general?",
    ],
    "respuesta_corta": [
        "Cuéntame más.",
        "¿Qué pasó?",
        "¿Cómo así?",
        "Dale, te escucho.",
    ],
    "no_entendido": [
        "No te seguí bien. ¿Qué quisiste decir?",
        "¿Me explicas un poco más?",
        "No entendí. ¿Qué pasó?",
        "Mmm, ¿cómo es eso?",
    ],
    "crisis": [
        (
            "Lo que me dices es importante y me preocupa. No tienes que cargarlo solo/a.\n\n"
            "Por favor habla con alguien de confianza o llama a una línea de crisis. "
            "Son gratuitas y confidenciales. Si me dices desde qué país escribes, "
            "te puedo dar el número exacto.\n\n"
            "¿Hay alguien cerca de ti ahora mismo?"
        ),
        (
            "Gracias por decirme esto. No tienes que cargarlo solo/a.\n\n"
            "Hay personas entrenadas para acompañarte en esto. "
            "Si me dices tu país, te doy el número de crisis de ahí. "
            "Son gratuitas y confidenciales.\n\n"
            "¿Quieres contarme cómo llegaste a sentirte así?"
        ),
    ],
}

# Preguntas de seguimiento — solo se usan si no se han hecho antes
preguntas_seguimiento = {
    "tristeza": [
        "¿Desde cuándo estás así?",
        "¿Pudiste hablar con alguien?",
        "¿Qué suele ayudarte cuando estás así?",
        "¿Hay algo que lo esté causando o apareció de la nada?",
    ],
    "ansiedad": [
        "¿Hay algo concreto que lo esté disparando?",
        "¿Cuándo fue la última vez que estuviste tranquilo/a?",
    ],
    "soledad": [
        "¿Hace cuánto te sentís así?",
        "¿Hay alguien con quien normalmente puedas hablar?",
    ],
    "autoestima": [
        "¿Cuándo empezaste a sentirte así?",
        "¿Hay algo que lo haya disparado?",
    ],
    "motivacion": [
        "¿Qué es lo que más te cuesta arrancar?",
        "¿Hay algo que te haya motivado antes y ahora no?",
    ],
    "trabajo_estudio": [
        "¿Hace cuánto estás así?",
        "¿Podés hablar con alguien en ese entorno?",
    ],
    "relaciones": [
        "¿Cómo quedaron las cosas después?",
        "¿Tienes con quién hablar de esto?",
    ],
    "dormir": [
        "¿Qué suele pasarte por la cabeza cuando intentas dormir?",
        "¿Hace cuánto que está pasando esto?",
    ],
}

# Continuaciones cuando el usuario responde algo corto dentro de un hilo emocional
continuaciones_contexto = {
    "tristeza": [
        "¿Qué más pasó?",
        "¿Y cómo estás ahora?",
        "¿Pudiste hablar con alguien?",
    ],
    "ansiedad": [
        "¿Sigue igual o bajó un poco?",
        "¿Qué hiciste para manejarlo?",
    ],
    "soledad": [
        "¿Pudiste hablar con alguien después?",
        "¿Cómo estás ahora?",
    ],
    "trabajo_estudio": [
        "¿Cómo siguió eso?",
        "¿Pudiste hacer algo al respecto?",
    ],
    "relaciones": [
        "¿Cómo quedaron después?",
        "¿Hablaste con esa persona?",
    ],
}

# Preguntas proactivas — solo cuando la conversación pierde hilo completamente
preguntas_proactivas = [
    "¿Hay algo que te haya estado rondando la cabeza?",
    "¿Cómo fue tu semana?",
    "¿Qué hay de nuevo?",
    "¿Qué estás haciendo hoy?",
    "¿Cómo estás durmiendo últimamente?",
    "¿Hay algo que te esté pesando?",
    "¿Qué estás viendo o jugando últimamente?",
    "¿Algo bueno pasó esta semana?",
]

# Líneas de crisis por país
lineas_crisis = {
    "argentina": {
        "nombre": "Centro de Asistencia al Suicida",
        "numero": "135",
        "detalle": "Gratuito, 24 horas.",
    },
    "colombia": {
        "nombre": "Línea 106",
        "numero": "106",
        "detalle": "Gratuita, 24 horas. WhatsApp: 300 754 8933.",
    },
    "mexico": {
        "nombre": "SAPTEL",
        "numero": "55 5259-8121",
        "detalle": "Gratuito, 24 horas.",
    },
    "españa": {
        "nombre": "Teléfono de la Esperanza",
        "numero": "717 003 717",
        "detalle": "24 horas.",
    },
    "chile": {
        "nombre": "Línea de la Vida",
        "numero": "600 360 7777",
        "detalle": "Gratuita, 24 horas.",
    },
    "peru": {
        "nombre": "Línea 113",
        "numero": "113",
        "detalle": "Gratuita, 24 horas. Opción salud mental.",
    },
    "venezuela": {
        "nombre": "AMSA",
        "numero": "0212 862 0511",
        "detalle": "Asistencia en crisis.",
    },
    "ecuador": {
        "nombre": "Línea 171",
        "numero": "171",
        "detalle": "Gratuita, 24 horas.",
    },
    "uruguay": {
        "nombre": "Centro de Asistencia al Suicida",
        "numero": "0800 0767",
        "detalle": "Gratuito, 24 horas.",
    },
    "bolivia": {
        "nombre": "SOS Salud Mental",
        "numero": "800 10 4112",
        "detalle": "Gratuito.",
    },
    "paraguay": {
        "nombre": "SOS Línea de Vida",
        "numero": "117",
        "detalle": "24 horas.",
    },
    "estados unidos": {
        "nombre": "988 Suicide & Crisis Lifeline (en español)",
        "numero": "988",
        "detalle": "Gratuito, 24 horas. Atención en español disponible.",
    },
}

# Keywords por país para detección
paises_keywords = {
    "argentina":      ["argentina", "argentino", "arg"],
    "colombia":       ["colombia", "colombiano", "col"],
    "mexico":         ["mexico", "mexicano", "mex"],
    "españa":         ["españa", "espana", "español"],
    "chile":          ["chile", "chileno"],
    "peru":           ["peru", "peruano"],
    "venezuela":      ["venezuela", "venezolano", "vzla"],
    "ecuador":        ["ecuador", "ecuatoriano"],
    "uruguay":        ["uruguay", "uruguayo"],
    "bolivia":        ["bolivia", "boliviano"],
    "paraguay":       ["paraguay", "paraguayo"],
    "estados unidos": ["estados unidos", "eeuu", "usa"],
}