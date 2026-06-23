import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers.auth_router import router as auth_router
from app.routers.documents_router import router as documents_router
from app.routers.ia_router import router as ia_router
from app.routers.ingest_router import router as ingest_router
from app.services.rag_service import RAGServiceLangGraph
from rag.config import load_config_from_env
from rag.retriever import FiscalRAGRetriever
from rag.chain import FiscalRAGChain


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Inicializa el RAGService una sola vez al arrancar el servidor y lo
    expone en app.state.rag_service, que es lo que ia_router.get_rag_service
    espera encontrar en cada request.

    Usa el mismo patrón que ya existe en rag/config.py (load_config_from_env)
    y los constructores reales de FiscalRAGRetriever/FiscalRAGChain, en vez
    de la clase Settings de app/core/config.py (que no tiene estos campos
    y no expone get_settings()).
    """
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

    yield

    app.state.rag_service = None


app = FastAPI(title="VISIR API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
def welcome() -> str:
    return "Oli desde visir"


app.include_router(documents_router)
app.include_router(auth_router)
app.include_router(ia_router)
app.include_router(ingest_router)
