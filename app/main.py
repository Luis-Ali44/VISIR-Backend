from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers.auth_router import router as auth_router
from app.routers.documents_router import router as documents_router
from app.routers.extracciones_router import router as extracciones_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    from app.services.Extraccion.ocr_paddle import _get_paddle_ocr
    _get_paddle_ocr()
    yield


app = FastAPI(title="VISIR API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
def welcome() -> str:
    return "Oli desde visir"


app.include_router(documents_router)
app.include_router(auth_router)
app.include_router(extracciones_router)