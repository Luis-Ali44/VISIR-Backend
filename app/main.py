from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import configurar_logging
from app.core.sentry import configurar_sentry
from app.routers.auth_router import router as auth_router
from app.routers.conversacion_router import router as consultas_router
from app.routers.documents_router import router as documents_router
from app.routers.extracciones_router import router as extracciones_router
from app.routers.health_router import router as health_router

configurar_sentry()
configurar_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from app.services.Extraccion.ocr_paddle import _get_paddle_ocr

    _get_paddle_ocr()
    yield


app = FastAPI(title="VISIR API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    # Aqui ira la url del frontend para aceptar sus peticiones
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(documents_router)
app.include_router(auth_router)
app.include_router(extracciones_router)
app.include_router(consultas_router)
app.include_router(health_router)
