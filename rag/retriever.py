from dataclasses import dataclass

from rag.config import DEFAULT_CONFIG, RAGConfig
from rag.embeddings import build_query_embed_model
from rag.store import FiscalChromaStore, QueryResult


@dataclass
class RetrievalContext:
    rank: int
    chunk_id: str
    text: str
    similarity: float
    doc_id: str
    source: str
    filename: str
    section: str
    page_number: int | None = None
    importance: int = 3
    importance_weight: float = 0.6


class FiscalRAGRetriever:

    def __init__(self, config: RAGConfig = DEFAULT_CONFIG):
        self.config = config

        self.query_embed_model = build_query_embed_model(
            base_url=config.embedding_base_url,
            model_name=config.embedding_model_name,
            api_key=config.embedding_api_key,
            timeout=config.embedding_timeout,
            max_retries=config.embedding_max_retries,
        )

        self.store = FiscalChromaStore(
            chroma_path=config.chroma_path,
            collection_name=config.collection_name,
        )

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        min_importance: int | None = None,
        doc_id_filter: str | None = None,
        rerank_by_importance: bool = True,
        importance_weight: float = 0.2,
    ) -> list[RetrievalContext]:
        k = top_k or self.config.default_top_k

        query_embedding = self.query_embed_model.get_query_embedding(query)

        where_filter = {}
        if doc_id_filter:
            where_filter["doc_id"] = {"$eq": doc_id_filter}

        fetch_k = k * 5 if rerank_by_importance else k

        raw_results: list[QueryResult] = self.store.query(
            query_embedding=query_embedding,
            top_k=fetch_k,
            where_filter=where_filter or None,
            min_importance=min_importance,
        )

        if not raw_results:
            return []

        contexts = []
        for r in raw_results:
            m = r.metadata
            contexts.append(RetrievalContext(
                rank=0,
                chunk_id=r.chunk_id,
                text=r.text,
                similarity=r.similarity,
                doc_id=m.get("doc_id", ""),
                source=m.get("source", ""),
                filename=m.get("filename", ""),
                section=m.get("section", "sin_sección"),
                page_number=m.get("page_number"),
                importance=int(m.get("importance", 3)),
                importance_weight=float(m.get("importance_weight", 0.6)),
            ))

        if rerank_by_importance:
            contexts = self._rerank(contexts, importance_weight)

        contexts = contexts[:k]
        for i, ctx in enumerate(contexts):
            ctx.rank = i + 1

        return contexts

    def _rerank(
        self,
        contexts: list[RetrievalContext],
        importance_weight: float,
    ) -> list[RetrievalContext]:
        w = importance_weight
        for ctx in contexts:
            importance_norm = ctx.importance / 5.0
            ctx._combined_score = (1 - w) * ctx.similarity + w * importance_norm
        return sorted(contexts, key=lambda c: c._combined_score, reverse=True)


class OrgRAGRetriever:
    """
    Retriever para la colección compartida de documentos de organización
    (CFDIs propios + documentos generales subidos por cada org).

    A diferencia de FiscalRAGRetriever (normativa SAT, sin filtro, de
    solo lectura para todos), este retriever EXIGE id_organizacion en
    cada consulta y lo inyecta como filtro obligatorio de Chroma. Sin
    este filtro, una organización podría recibir fragmentos de otra —
    el mismo principio de aislamiento que ya aplica
    extracciones_repository.get_extracciones_by_org a nivel SQL.
    """

    def __init__(self, config: RAGConfig = DEFAULT_CONFIG):
        self.config = config

        self.query_embed_model = build_query_embed_model(
            base_url=config.embedding_base_url,
            model_name=config.embedding_model_name,
            api_key=config.embedding_api_key,
            timeout=config.embedding_timeout,
            max_retries=config.embedding_max_retries,
        )

        self.store = FiscalChromaStore(
            chroma_path=config.chroma_path,
            collection_name=config.org_collection_name,
        )

    def retrieve(
        self,
        query: str,
        id_organizacion: str,
        top_k: int | None = None,
        tipo_documento: str | None = None,
    ) -> list[RetrievalContext]:
        if not id_organizacion:
            # Defensivo: jamás se debe poder llamar a este retriever sin
            # organización — preferimos fallar explícito a devolver
            # resultados de otra org por un None/"" silencioso.
            raise ValueError("id_organizacion es obligatorio para OrgRAGRetriever.retrieve")

        k = top_k or self.config.default_top_k

        query_embedding = self.query_embed_model.get_query_embedding(query)

        where_filter: dict = {"id_organizacion": {"$eq": id_organizacion}}
        if tipo_documento:
            where_filter = {
                "$and": [
                    where_filter,
                    {"tipo_documento": {"$eq": tipo_documento}},
                ]
            }

        raw_results: list[QueryResult] = self.store.query(
            query_embedding=query_embedding,
            top_k=k,
            where_filter=where_filter,
        )

        if not raw_results:
            return []

        contexts = []
        for r in raw_results:
            m = r.metadata
            contexts.append(RetrievalContext(
                rank=0,
                chunk_id=r.chunk_id,
                text=r.text,
                similarity=r.similarity,
                doc_id=m.get("doc_id", ""),
                source=m.get("source", ""),
                filename=m.get("filename", ""),
                section=m.get("section", "sin_sección"),
                page_number=m.get("page_number"),
                importance=int(m.get("importance", 3)),
                importance_weight=float(m.get("importance_weight", 0.6)),
            ))

        for i, ctx in enumerate(contexts):
            ctx.rank = i + 1

        return contexts
