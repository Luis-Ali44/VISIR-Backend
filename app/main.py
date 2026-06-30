import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import setup_logging
from app.routers.auth_router import router as auth_router
from app.routers.documents_router import router as documents_router
from app.routers.extracciones_router import router as extracciones_router
from app.routers.ia_router import router as ia_router
from app.routers.ingest_router import router as ingest_router
from app.services.rag_service import RAGServiceLangGraph
from rag.config import load_config_from_env
from rag.retriever import FiscalRAGRetriever
from rag.chain import FiscalRAGChain

# setup_logging() agrega un handler al root logger de Python con salida
# a stdout. Sin esto, get_logger("rag_fiscal") (usado en ingest_router,
# org_ingestion_service, etc.) devuelve un logger que NO tiene ningún
# handler propio ni heredado — Python cae al "handler de último
# recurso", que solo imprime WARNING/ERROR a stderr y descarta los
# logger.info(...) en silencio. Por eso "ingesta_iniciada" /
# "ingesta_completada" / "ingesta_fallida" nunca aparecían en
# `docker compose logs`, aunque el código sí los emitía.
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:

    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    rag_config = load_config_from_env(chroma_path=chroma_path)

    retriever = FiscalRAGRetriever(rag_config)
    chain = FiscalRAGChain(
        api_key=rag_config.llm_api_key,
        model=rag_config.llm_model,
        base_url=rag_config.llm_base_url,
        temperature=rag_config.llm_temperature,
        max_tokens=rag_config.llm_max_tokens,
    )

    app.state.rag_service = RAGServiceLangGraph(
        chain=chain,
        retriever=retriever,
        llm_api_key=rag_config.llm_api_key,
        llm_base_url=rag_config.llm_base_url,
        llm_model=rag_config.llm_model,
    )

    from app.services.Extraccion.ocr_paddle import _get_paddle_ocr

    _get_paddle_ocr()

    yield

    app.state.rag_service = None


app = FastAPI(title="VISIR API", version="0.2.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.2.0"}


@app.get("/")
def welcome() -> str:
    return "Oli desde visir"


app.include_router(documents_router)
app.include_router(auth_router)
app.include_router(ia_router)
app.include_router(ingest_router)
app.include_router(extracciones_router)