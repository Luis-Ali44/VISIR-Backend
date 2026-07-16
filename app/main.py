import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import configurar_logging
from app.core.sentry import configurar_sentry
from app.routers.auth_router import router as auth_router
from app.routers.conversaciones_router import router as conversaciones_router
from app.routers.documents_router import router as documents_router
from app.routers.extracciones_router import router as extracciones_router
from app.routers.health_router import router as health_router
from app.routers.ia_router import router as ia_router
from app.routers.ingest_router import router as ingest_router
from app.services.rag_service import RAGServiceLangGraph
from rag.chain import FiscalRAGChain
from rag.config import load_config_from_env
from rag.retriever import FiscalRAGRetriever

configurar_sentry()
configurar_logging()


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
        rag_config=rag_config,
    )

    from app.services.Extraccion.ocr_paddle import _get_paddle_ocr

    _get_paddle_ocr()

    yield

    app.state.rag_service = None


app = FastAPI(title="VISIR API", version="0.2.0", lifespan=lifespan)

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
app.include_router(ia_router)
app.include_router(ingest_router)
app.include_router(extracciones_router)
# app.include_router(consultas_router)
app.include_router(health_router)
app.include_router(conversaciones_router)
