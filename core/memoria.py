# core/memoria.py — Gestión de memoria persistente de Lumi en Supabase

from datetime import datetime, date
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLA_PERFILES = "profiles"


def _memoria_vacia():
    return {
        "nombre": None,
        "historial_intenciones": [],
        "ultima_conversacion": None,
        "sesiones": 0,
        "emociones_registradas": [],
        "temas_hablados": [],
        "preguntas_hechas": [],
    }


def es_primera_vez_hoy(memoria: dict) -> bool:
    """Acepta el dict directamente, no hace query a Supabase."""
    ultima = memoria.get("ultima_conversacion")
    if not ultima:
        return True
    try:
        ultima_dt = datetime.fromisoformat(ultima)
        return ultima_dt.date() < date.today()
    except Exception:
        return True


def cargar_memoria(usuario_id: str) -> dict:
    try:
        res = (
            supabase.table(TABLA_PERFILES)
            .select("memoria")
            .eq("id", usuario_id)
            .single()
            .execute()
        )
        if res.data and res.data.get("memoria"):
            return res.data["memoria"]
    except Exception as e:
        print(f"[Memoria] Error al cargar usuario {usuario_id}: {e}")
    return _memoria_vacia()


def guardar_memoria(usuario_id: str, memoria: dict):
    try:
        memoria["ultima_conversacion"] = datetime.now().isoformat()
        
        # Upsert: inserta si no existe, actualiza si existe
        existe = (
            supabase.table(TABLA_PERFILES)
            .select("id")
            .eq("id", usuario_id)
            .execute()
        )
        
        if existe.data:
            supabase.table(TABLA_PERFILES).update({
                "memoria": memoria,
            }).eq("id", usuario_id).execute()
        else:
            supabase.table(TABLA_PERFILES).insert({
                "id": usuario_id,
                "memoria": memoria,
            }).execute()
            
    except Exception as e:
        print(f"[Memoria] Error al guardar usuario {usuario_id}: {e}")


# -------------------------
# FUNCIONES QUE MODIFICAN MEMORIA (sin guardar en Supabase)
# -------------------------

def agregar_intencion(memoria: dict, intencion: str) -> dict:
    """Modifica el dict en memoria. Retorna el dict modificado."""
    historial = memoria.setdefault("historial_intenciones", [])
    historial.append(intencion)
    memoria["historial_intenciones"] = historial[-10:]
    return memoria


def registrar_emocion(memoria: dict, emocion: str) -> dict:
    """Modifica el dict en memoria. Retorna el dict modificado."""
    memoria.setdefault("emociones_registradas", []).append({
        "emocion": emocion,
        "fecha": str(date.today()),
    })
    return memoria


def registrar_tema(memoria: dict, tema: str) -> dict:
    """Modifica el dict en memoria. Retorna el dict modificado."""
    temas = memoria.setdefault("temas_hablados", [])
    if tema not in temas:
        temas.append(tema)
    return memoria


def registrar_pregunta(memoria: dict, pregunta: str) -> dict:
    memoria.setdefault("preguntas_hechas", []).append({
        "pregunta": pregunta,
        "fecha": str(date.today()),
    })
    return memoria


# -------------------------
# FUNCIONES DE CONTEXTO
# -------------------------

def ha_pasado_mucho_tiempo(memoria: dict) -> bool:
    """Acepta el dict directamente."""
    ultima = memoria.get("ultima_conversacion")
    if not ultima:
        return True
    try:
        ultima_dt = datetime.fromisoformat(ultima)
        return (datetime.now() - ultima_dt).total_seconds() > 12 * 3600
    except Exception:
        return True


def emocion_predominante(memoria: dict, ultimas: int = 5):
    """Acepta el dict directamente. Analiza emociones_registradas."""
    emociones_reg = memoria.get("emociones_registradas", [])[-ultimas:]
    if not emociones_reg:
        return None

    emociones = ["tristeza", "ansiedad", "soledad", "autoestima", "felicidad"]
    nombres = [e.get("emocion") for e in emociones_reg if isinstance(e, dict)]
    
    conteo = {e: nombres.count(e) for e in emociones}
    max_emocion = max(conteo, key=conteo.get)
    
    return max_emocion if conteo[max_emocion] > 0 else None


def obtener_resumen_memoria(memoria: dict) -> str:
    """Acepta el dict directamente."""
    nombre = memoria.get("nombre")
    emocion = emocion_predominante(memoria)
    temas = memoria.get("temas_hablados", [])[-3:]

    resumen = []
    if nombre:
        resumen.append(f"Usuario: {nombre}")
    if emocion:
        resumen.append(f"Emoción reciente: {emocion}")
    if temas:
        resumen.append(f"Temas recientes: {', '.join(temas)}")

    return " | ".join(resumen) if resumen else "Sin contexto previo"