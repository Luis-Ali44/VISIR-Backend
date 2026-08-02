from typing import Any

import redis
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import ExecCtx, cliente_for

router = APIRouter(prefix="/health", tags=["Monitoreo"])


@router.get("/v1")
async def health_check() -> JSONResponse:
    health_status: dict[str, Any] = {"status": "healthy", "services": {"api": "online"}}

    try:
        ctx = ExecCtx(actor="system", id_organizacion="health-check-org")
        db = cliente_for(ctx)
        db.table("extracciones").select("id").limit(1).execute()
        health_status["services"]["supabase"] = "online"
    except Exception as e:
        health_status["status"] = "con_falla"
        health_status["services"]["supabase"] = f"offline: {e!s}"

    try:
        redis_url = settings.REDIS_URL
        print(f"{redis_url}")
        r = redis.Redis.from_url(redis_url, socket_timeout=2)
        if r.ping():
            health_status["services"]["redis_broker"] = "online"
    except Exception as e:
        health_status["status"] = "con_falla"
        health_status["services"]["redis_broker"] = f"offline: {e!s}"

    if health_status["status"] == "con_falla":
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=health_status)

    codigo = (
        status.HTTP_503_SERVICE_UNAVAILABLE
        if health_status["status"] == "con_falla"
        else status.HTTP_200_OK
    )

    return JSONResponse(status_code=codigo, content=health_status)
