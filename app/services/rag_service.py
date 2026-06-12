from __future__ import annotations
from rag.chain import ChainResult
from rag.chain import FiscalRAGChain
from rag.retriever import FiscalRAGRetriever, RetrievalContext
from app.schemas.consulta import ChunkInfo, ConsultaResponse


class RAGService:
    def __init__(self, chain: FiscalRAGChain, retriever: FiscalRAGRetriever) -> None:
        self.chain = chain
        self.retriever = retriever

    def preguntar(self, pregunta: str, top_k: int = 5) -> tuple[ChainResult, list[RetrievalContext]]:
        fragmentos = self.retriever.retrieve(
            query=pregunta, top_k=top_k, rerank_by_importance=True,
    )
        resultado = self.chain.invoke(pregunta=pregunta, fragmentos=fragmentos)
        return resultado, fragmentos
