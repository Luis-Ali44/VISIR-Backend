import logging

from app.core.database import supabase

logger = logging.getLogger(__name__)


def registrar_uso(
    id_organizacion: str | None,
    tier_solicitado: str,
    tier_usado: str,
    motivo_fallback: str | None,
    complejidad_score: float,
    tokens_entrada: int,
    tokens_salida: int,
    latencia_ms: int,
    exito: bool,
) -> None:
    payload = {
        "id_organizacion": id_organizacion,
        "tier_solicitado": tier_solicitado,
        "tier_usado": tier_usado,
        "motivo_fallback": motivo_fallback,
        "complejidad_score": complejidad_score,
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "latencia_ms": latencia_ms,
        "exito": exito,
    }
    try:
        supabase.table("llm_router_log").insert(payload).execute()
    except Exception as exc:
        logger.error("Error al registrar uso de llm_router_log: %s", exc)
