from dataclasses import dataclass

import chromadb
from chromadb.config import Settings


@dataclass
class ChunkRecord:
    chunk_hash: str          
    text: str                
    embedding: list[float]   
    metadata: dict           


@dataclass
class QueryResult:
    chunk_id: str
    text: str
    metadata: dict
    distance: float         

    @property
    def similarity(self) -> float:
        return round(1.0 - self.distance, 4)


class FiscalChromaStore:

    def __init__(
        self,
        chroma_path: str = "./chroma_db",
        collection_name: str = "documentos_fiscales",
        embedding_dimensions: int | None = None,
    ):
        
        self.collection_name = collection_name

        
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,          
            ),
        )

        collection_metadata = {"hnsw:space": "cosine"}
        if embedding_dimensions:
            collection_metadata["embedding_dimension"] = str(embedding_dimensions)

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=collection_metadata,
        )

    def document_already_indexed(self, doc_hash: str) -> bool:
        
        results = self.collection.get(
            where={"doc_hash": {"$eq": doc_hash}},
            limit=1,
            include=[],  
        )
        return len(results["ids"]) > 0

    def chunk_already_indexed(self, chunk_hash: str) -> bool:
        
        try:
            results = self.collection.get(ids=[chunk_hash], include=[])
            return len(results["ids"]) > 0
        except Exception:
            return False

    def get_indexed_doc_hashes(self) -> set:
        total = self.collection.count()
        if total == 0:
            return set()

        page_size = 10_000
        hashes: set[str] = set()
        for offset in range(0, total, page_size):
            results = self.collection.get(
                include=["metadatas"],
                limit=page_size,
                offset=offset,
            )
            hashes.update(m.get("doc_hash", "") for m in results["metadatas"])
        return hashes - {""}


    def upsert_chunk(self, record: ChunkRecord) -> bool:
        already_exists = self.chunk_already_indexed(record.chunk_hash)

    
        safe_metadata = self._sanitize_metadata({
            **record.metadata,
            "chunk_hash": record.chunk_hash,
        })

        self.collection.upsert(
            ids=[record.chunk_hash],
            embeddings=[record.embedding],
            documents=[record.text],
            metadatas=[safe_metadata],
        )

        return not already_exists  

    def upsert_chunks_batch(self, records: list[ChunkRecord]) -> dict:
        
        if not records:
            return {"inserted": 0, "skipped": 0}

        unique_records = []
        seen_ids = set()
        for record in records:
            if record.chunk_hash in seen_ids:
                continue
            seen_ids.add(record.chunk_hash)
            unique_records.append(record)

        all_ids = [r.chunk_hash for r in unique_records]
        try:
            existing = self.collection.get(ids=all_ids, include=[])
            existing_ids = set(existing["ids"])
        except Exception:
            existing_ids = set()

        new_records = [r for r in unique_records if r.chunk_hash not in existing_ids]
        skipped = len(records) - len(new_records)

        if new_records:
            self.collection.upsert(
                ids=[r.chunk_hash for r in new_records],
                embeddings=[r.embedding for r in new_records],
                documents=[r.text for r in new_records],
                metadatas=[
                    self._sanitize_metadata({**r.metadata, "chunk_hash": r.chunk_hash})
                    for r in new_records
                ],
            )

        return {"inserted": len(new_records), "skipped": skipped}


    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        where_filter: dict | None = None,
        min_importance: int | None = None,
    ) -> list[QueryResult]:
        
        filters = {}
        if where_filter:
            filters.update(where_filter)
        if min_importance is not None:
            importance_filter = {"importance": {"$gte": min_importance}}
            if filters:
                filters = {"$and": [filters, importance_filter]}
            else:
                filters = importance_filter

        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if filters:
            query_kwargs["where"] = filters

        raw = self.collection.query(**query_kwargs)

        results = []
        for i in range(len(raw["ids"][0])):
            results.append(QueryResult(
                chunk_id=raw["ids"][0][i],
                text=raw["documents"][0][i],
                metadata=raw["metadatas"][0][i],
                distance=raw["distances"][0][i],
            ))

        return results


    def stats(self) -> dict:
        count = self.collection.count()
        return {
            "collection": self.collection_name,
            "total_chunks": count,
            "indexed_doc_hashes": len(self.get_indexed_doc_hashes()),
        }

    def stats_by_org(self, id_organizacion: str) -> dict:
        """
        Igual que stats(), pero acotado a los chunks de una sola
        organización vía filtro de metadata. Pensado para la colección
        compartida `documentos_organizacion`, donde stats() sin filtro
        devolvería el conteo de TODAS las organizaciones mezcladas —
        un dato que un usuario normal no debería poder ver.
        """
        where = {"id_organizacion": {"$eq": id_organizacion}}

        results = self.collection.get(
            where=where,
            include=["metadatas"],
        )
        metadatas = results["metadatas"]

        doc_ids = {m.get("id_documento", "") for m in metadatas} - {""}

        return {
            "collection": self.collection_name,
            "total_chunks": len(metadatas),
            "documentos_unicos": len(doc_ids),
        }

    def reset(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _sanitize_metadata(metadata: dict) -> dict:
    
        safe = {}
        for k, v in metadata.items():
            if isinstance(v, (str, int, float, bool)):
                safe[k] = v
            elif v is None:
                safe[k] = ""
            else:
                safe[k] = str(v)
        return safe