import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from tqdm import tqdm

from ingestion.chunker import FiscalDocumentChunker
from ingestion.loader import load_document
from rag.config import DEFAULT_CONFIG, RAGConfig
from rag.embeddings import build_index_embed_model
from rag.hasher import compute_chunk_hash, compute_doc_id, compute_file_hash
from rag.store import ChunkRecord, FiscalChromaStore


@dataclass
class TopicSeedProfile:
    title: str
    text: str
    priority: int = 3
    embedding: list[float] | None = None


@dataclass
class IngestionResult:
    doc_id: str
    source: str
    doc_hash: str
    total_sections: int
    total_chunks: int
    new_chunks: int
    skipped_chunks: int
    was_skipped: bool
    elapsed_seconds: float

    def summary(self) -> str:
        status = "⏭  SKIP (sin cambios)" if self.was_skipped else "✅ Indexado"
        return (
            f"{status} | {self.doc_id}\n"
            f"   Secciones: {self.total_sections} | "
            f"Chunks: {self.total_chunks} (new={self.new_chunks}, skip={self.skipped_chunks}) | "
            f"{self.elapsed_seconds:.1f}s"
        )


@dataclass
class BatchIngestionReport:
    results: list[IngestionResult] = field(default_factory=list)

    @property
    def total_docs(self) -> int:
        return len(self.results)

    @property
    def docs_indexed(self) -> int:
        return sum(1 for r in self.results if not r.was_skipped)

    @property
    def docs_skipped(self) -> int:
        return sum(1 for r in self.results if r.was_skipped)

    @property
    def total_new_chunks(self) -> int:
        return sum(r.new_chunks for r in self.results)

    def print_report(self) -> None:
        print(f"\n{'═'*65}")
        print("  REPORTE DE INGESTA RAG")
        print(f"{'═'*65}")
        for r in self.results:
            print(f"  {r.summary()}")
        print(f"{'─'*65}")
        print(
            f"  Documentos: {self.total_docs} total | "
            f"{self.docs_indexed} indexados | {self.docs_skipped} sin cambios"
        )
        print(f"  Chunks nuevos: {self.total_new_chunks}")
        print(f"{'═'*65}\n")


class RAGIngestionPipeline:

    def __init__(self, config: RAGConfig = DEFAULT_CONFIG):
        self.config = config

        print(f"[INIT] Modelo de embeddings: {config.embedding_model_name}")
        print(f"[INIT] Timeout: {config.embedding_timeout}s | Reintentos: {config.embedding_max_retries}")

        self.embed_model = build_index_embed_model(
            base_url=config.embedding_base_url,
            model_name=config.embedding_model_name,
            api_key=config.embedding_api_key,
            timeout=config.embedding_timeout,
            max_retries=config.embedding_max_retries,
        )

        self.chunker = FiscalDocumentChunker(
            embed_model=self.embed_model,
            breakpoint_threshold=config.semantic_breakpoint_threshold,
            buffer_size=config.semantic_buffer_size,
            min_section_length=config.min_section_length_for_semantic,
        )

        self.store = FiscalChromaStore(
            chroma_path=config.chroma_path,
            collection_name=config.collection_name,
            embedding_dimensions=config.embedding_dimensions,
        )

        self.topic_seed_profiles = self._load_topic_seed_profiles(
            Path(config.topic_seed_path)
        )
        if self.topic_seed_profiles:
            print(f"[INIT] Topic seed cargado: {len(self.topic_seed_profiles)} perfiles")
        else:
            print(f"[INIT] Topic seed no disponible en {config.topic_seed_path}")

        stats = self.store.stats()
        print(f"[INIT] ChromaDB '{stats['collection']}' — {stats['total_chunks']} chunks existentes")

    def _load_topic_seed_profiles(self, seed_path: Path) -> list[TopicSeedProfile]:
        if not seed_path.exists():
            return []
        raw_text = seed_path.read_text(encoding="utf-8").strip()
        if not raw_text:
            return []

        profiles: list[TopicSeedProfile] = []
        current_title: str | None = None
        current_priority = 3
        current_lines: list[str] = []

        def flush_current() -> None:
            nonlocal current_title, current_priority, current_lines
            if not current_title:
                return
            body = "\n".join(current_lines).strip()
            if not body:
                return
            profiles.append(TopicSeedProfile(title=current_title, text=body, priority=current_priority))

        for line in raw_text.splitlines():
            if line.startswith("## "):
                flush_current()
                current_lines = []
                heading = line[3:].strip()
                priority_match = re.search(r"Prioridad\s*(\d)", heading, re.IGNORECASE)
                current_priority = int(priority_match.group(1)) if priority_match else 3
                current_title = re.sub(
                    r"^Prioridad\s*\d+\s*[-–—:]\s*", "", heading, flags=re.IGNORECASE
                ).strip() or heading
                continue
            if current_title is not None:
                current_lines.append(line)

        flush_current()

        for profile in profiles:
            profile.embedding = self.embed_model.get_text_embedding(
                self._compress_text_for_embedding(profile.text)
            )
        return profiles

    @staticmethod
    def _compress_text_for_embedding(text: str, max_chars: int = 12000) -> str:
        clean_text = text.strip()
        if len(clean_text) <= max_chars:
            return clean_text
        half = max_chars // 2
        return f"{clean_text[:half]}\n\n...\n\n{clean_text[-half:]}"

    @staticmethod
    def _cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
        dot = sum(a * b for a, b in zip(vector_a, vector_b))
        norm_a = sum(a * a for a in vector_a) ** 0.5
        norm_b = sum(b * b for b in vector_b) ** 0.5
        if not norm_a or not norm_b:
            return 0.0
        return dot / (norm_a * norm_b)

    def _score_topic_importance(self, text: str) -> tuple[int, str, float, int]:
        if not self.topic_seed_profiles:
            return 3, "sin_topic_seed", 0.0, 3

        doc_embedding = self.embed_model.get_text_embedding(
            self._compress_text_for_embedding(text)
        )

        best_title = "sin_topic"
        best_priority = 3
        best_similarity = -1.0

        for profile in self.topic_seed_profiles:
            if not profile.embedding:
                continue
            sim = self._cosine_similarity(doc_embedding, profile.embedding)
            weighted = sim * (profile.priority / 5.0)
            if weighted > best_similarity * (best_priority / 5.0):
                best_similarity = sim
                best_title = profile.title
                best_priority = profile.priority

        if best_similarity < 0:
            return 3, best_title, 0.0, best_priority

        weighted_score = best_similarity * (best_priority / 5.0)
        importance = max(1, min(5, int(round(1 + (weighted_score * 4)))))
        return importance, best_title, round(best_similarity, 4), best_priority

    def ingest(
        self,
        pdf_path: str,
        importance: int = 3,
        extra_metadata: dict | None = None,
        force_reingest: bool = False,
        preview_sections: bool = False,
    ) -> IngestionResult:
        t0 = time.time()
        source = str(Path(pdf_path).resolve())
        doc_hash = compute_file_hash(pdf_path)
        doc_id = compute_doc_id(pdf_path)

        print(f"\n[DOC] {Path(pdf_path).name}")
        print(f"      doc_id={doc_id}")

        if not force_reingest and self.store.document_already_indexed(doc_hash):
            print(f"      ⏭  Ya indexado (doc_hash={doc_hash[:12]}...) — SKIP")
            return IngestionResult(
                doc_id=doc_id, source=source, doc_hash=doc_hash,
                total_sections=0, total_chunks=0,
                new_chunks=0, skipped_chunks=0,
                was_skipped=True,
                elapsed_seconds=round(time.time() - t0, 2),
            )

        print("      Cargando documento...")
        page_documents = load_document(
            file_path=pdf_path,
            doc_id=doc_id,
            doc_hash=doc_hash,
            importance=importance,
            extra_metadata=extra_metadata,
        )
        print(f"      {len(page_documents)} páginas cargadas")

        full_text = "\n".join(doc.text for doc in page_documents).strip()
        sem_importance, topic_title, sem_sim, topic_priority = self._score_topic_importance(full_text)

        for doc in page_documents:
            doc.metadata["filename_importance"] = importance
            doc.metadata["importance"] = sem_importance
            doc.metadata["importance_weight"] = round(sem_importance / 5.0, 2)
            doc.metadata["importance_source"] = "topic_seed"
            doc.metadata["topic_seed"] = topic_title
            doc.metadata["topic_priority"] = topic_priority
            doc.metadata["topic_similarity"] = sem_sim

        print(f"      Relevancia semántica: {sem_importance}/5 | tema: {topic_title} | sim={sem_sim:.4f}")

        if preview_sections and page_documents:
            from llama_index.core import Document
            preview_doc = Document(text=full_text, metadata=page_documents[0].metadata)
            self.chunker.describe_sections(preview_doc)

        print("      Fragmentando...")
        all_chunks = []
        section_titles: set[str] = set()

        # Aquí actúa el chunker dinámico (agrupación por párrafos + regex
        # de secciones fiscales). El tamaño de cada chunk sigue siendo
        # variable — decidido por la estructura real del documento, no
        # por un chunk_size fijo. Ver ingestion/chunker.py para el detalle.
        for page_doc in page_documents:
            chunks = self.chunker.chunk(page_doc)
            for chunk in chunks:
                section_titles.add(chunk.metadata.get("section", ""))
                all_chunks.append(chunk)

        print(f"      {len(section_titles)} secciones | {len(all_chunks)} chunks generados dinámicamente")

        # ── Embeddings por lote ──────────────────────────────────────────────
        # get_text_embedding_batch (heredado de BaseEmbedding) agrupa
        # internamente en sub-lotes de tamaño embed_batch_size y delega en
        # _get_text_embeddings, que ahora manda cada sub-lote en UNA SOLA
        # petición HTTP (ver rag/embeddings.py). Ya no es necesario un loop
        # manual de batching en este archivo — get_text_embedding_batch
        # hace el trabajo de agrupación, y el backend HTTP real ya no
        # itera texto por texto.
        print("      Calculando embeddings (batch HTTP real)...")
        texts = [chunk.text for chunk in all_chunks]
        embeddings = self.embed_model.get_text_embedding_batch(texts, show_progress=False)

        records = [
            ChunkRecord(
                chunk_hash=compute_chunk_hash(chunk.text),
                text=chunk.text,
                embedding=embedding,
                metadata=chunk.metadata,
            )
            for chunk, embedding in zip(all_chunks, embeddings)
        ]

        print("      Indexando en ChromaDB...")
        batch_result = self.store.upsert_chunks_batch(records)

        elapsed = round(time.time() - t0, 2)
        print(f"      ✅ new={batch_result['inserted']} | skip={batch_result['skipped']} | {elapsed}s")

        return IngestionResult(
            doc_id=doc_id,
            source=source,
            doc_hash=doc_hash,
            total_sections=len(section_titles),
            total_chunks=len(all_chunks),
            new_chunks=batch_result["inserted"],
            skipped_chunks=batch_result["skipped"],
            was_skipped=False,
            elapsed_seconds=elapsed,
        )

    def ingest_batch(
        self,
        documents: list[dict],
        preview_sections: bool = False,
    ) -> BatchIngestionReport:
        report = BatchIngestionReport()
        print(f"\n{'═'*65}")
        print(f"  INGESTA BATCH — {len(documents)} documentos")
        print(f"  Modelo: {self.config.embedding_model_name}")
        print(f"{'═'*65}")

        for doc_config in tqdm(documents, desc="Indexando", unit="doc"):
            pdf_path = doc_config["path"]
            if not Path(pdf_path).is_file():
                print(f"\n[SKIP] Archivo no encontrado: {Path(pdf_path).name}")
                continue
            try:
                result = self.ingest(
                    pdf_path=pdf_path,
                    importance=doc_config.get("importance", self.config.default_importance),
                    extra_metadata=doc_config.get("extra_metadata"),
                    force_reingest=doc_config.get("force_reingest", False),
                    preview_sections=preview_sections,
                )
                report.results.append(result)
            except FileNotFoundError:
                print(f"\n[SKIP] Archivo no encontrado durante la ingesta: {Path(pdf_path).name}")

        report.print_report()
        return report
