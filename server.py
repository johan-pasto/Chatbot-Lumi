# server.py — API REST de Lumi para conectar con app móvil

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client

# =========================
# CONFIGURACIÓN APP
# =========================

app = FastAPI(title="Lumi API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: cambiar por dominios específicos en producción final
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# SUPABASE (desde variables de entorno)
# =========================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "❌ Faltan variables de entorno: SUPABASE_URL y/o SUPABASE_KEY. "
        "Configúralas en el panel de tu hosting antes de iniciar la app."
    )

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# SESIONES
# =========================

sesiones: dict[str, "LumiChatbot"] = {}

# =========================
# MODELO DE DATOS
# =========================

class Mensaje(BaseModel):
    texto: str = Field(..., max_length=1000, description="Texto del mensaje")
    usuario_id: str = Field(default="default", min_length=1, description="ID del usuario")

# =========================
# INICIO
# =========================

@app.get("/")
def inicio():
    return {"mensaje": "Lumi API activa 💙", "status": "ok"}

# =========================
# UTILIDADES
# =========================

def log(mensaje: str):
    print(f"[LOG] {mensaje}")

# =========================
# BASE DE DATOS
# =========================

def ejecutar_query(func):
    """Ejecuta una función lambda y maneja errores."""
    try:
        return func()
    except Exception as e:
        print(f"[DB Error] {e}")
        return None

def guardar_mensaje(usuario_id: str, rol: str, texto: str):
    data = {
        "usuario_id": usuario_id,
        "rol": rol,
        "texto": texto
    }

    resultado = ejecutar_query(
        lambda: supabase.table("historial_chat").insert(data).execute()
    )
    
    if resultado is None:
        log(f"⚠️ No se pudo guardar mensaje de {rol}")
    
    return resultado

def cargar_historial(usuario_id: str, limite: int = 20):
    res = ejecutar_query(
        lambda: supabase.table("historial_chat")
        .select("rol, texto, timestamp")
        .eq("usuario_id", usuario_id)
        .order("timestamp", desc=True)
        .limit(limite)
        .execute()
    )

    if not res or not res.data:
        return []

    return list(reversed(res.data))

# =========================
# FORMATO PARA EL BOT
# =========================

def formatear_historial(historial):
    return [
        {
            "role": m["rol"],
            "content": m["texto"]
        }
        for m in historial
    ]

# =========================
# SESIONES BOT
# =========================

def obtener_bot(usuario_id: str):
    """Obtiene o crea una instancia del chatbot para el usuario."""
    if usuario_id not in sesiones:
        # Importación diferida para evitar circular imports
        from core.lumi_engine import LumiChatbot
        sesiones[usuario_id] = LumiChatbot(user_id=usuario_id)
    return sesiones[usuario_id]

# =========================
# LÓGICA PRINCIPAL
# =========================

def procesar_mensaje(usuario_id: str, texto: str):
    log(f"{usuario_id} → {texto}")

    # Guardar mensaje usuario
    guardar_mensaje(usuario_id, "usuario", texto)

    # Cargar y formatear historial
    historial = cargar_historial(usuario_id)
    historial_formateado = formatear_historial(historial)

    # Obtener bot
    bot = obtener_bot(usuario_id)

    # Generar respuesta (pasar historial si el bot lo necesita)
    respuesta = bot.responder_usuario(texto)

    # Guardar respuesta
    guardar_mensaje(usuario_id, "lumi", respuesta)

    log(f"Lumi → {respuesta}")

    return respuesta

# =========================
# ENDPOINTS
# =========================

@app.post("/chat")
def chat(msg: Mensaje):
    # Validación de usuario_id
    if not msg.usuario_id or msg.usuario_id.strip() == "":
        return {"error": "usuario_id es requerido"}
    
    # Validación de texto
    if not msg.texto or msg.texto.strip() == "":
        return {"error": "El mensaje no puede estar vacío"}

    respuesta = procesar_mensaje(msg.usuario_id, msg.texto)

    return {"respuesta": respuesta, "usuario_id": msg.usuario_id}


@app.get("/health")
def health_check():
    """Endpoint para verificar que la API está funcionando."""
    return {"status": "ok", "sesiones_activas": len(sesiones)}


@app.delete("/sesiones/{usuario_id}")
def limpiar_sesion(usuario_id: str):
    """Limpia la sesión de un usuario (útil para testing)."""
    if usuario_id in sesiones:
        del sesiones[usuario_id]
        return {"mensaje": f"Sesión de {usuario_id} eliminada"}
    return {"mensaje": "Sesión no encontrada"}


# =========================
# EJECUCIÓN
# =========================

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)