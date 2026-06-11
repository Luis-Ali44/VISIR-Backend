import argparse
import datetime
import glob
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_DIR   = ROOT_DIR / "chroma_db"
VAL_DIR  = ROOT_DIR / "validation_results"

load_dotenv(ROOT_DIR / ".env")


from rag.config import RAGConfig, load_config_from_env  # noqa: E402
from rag.retriever import FiscalRAGRetriever             # noqa: E402
from ingestion.pipeline import RAGIngestionPipeline      # noqa: E402

def discover_documents(config: RAGConfig) -> list[dict]:
    pdf_paths = sorted(glob.glob(str(DATA_DIR / "*.pdf")))
    md_paths  = sorted(glob.glob(str(DATA_DIR / "*.md")))
    paths = pdf_paths + md_paths

    if not paths:
        return []

    docs = []
    for path in paths:
        if not Path(path).is_file():
            print(f"   [WARN] Archivo no disponible, se omite: {Path(path).name}")
            continue
        docs.append({
            "path": path,
            "importance": config.default_importance,
        })
    return docs

def run_ingestion(config: RAGConfig, preview: bool = False) -> None:
    documents = discover_documents(config)
    if not documents:
        print(f"\n[WARN] No se encontraron documentos en {DATA_DIR}")
        print("       Coloca PDFs en la carpeta data/ e intenta de nuevo.")
        return

    print(f"\n[INFO] {len(documents)} documentos encontrados en {DATA_DIR}")
    pipeline = RAGIngestionPipeline(config)
    pipeline.ingest_batch(documents, preview_sections=preview)



VALIDATION_QUERIES = [
    "¿Qué es el CFDI y para qué se usa?",
    "¿Cuáles son los campos obligatorios del CFDI 4.0?",
    "¿Cómo se cancela un CFDI?",
    "¿Qué es el complemento de pago?",
    "¿Cuáles son los regímenes fiscales disponibles en México?",
]


def run_queries(config: RAGConfig, custom_query: str | None = None) -> None:
    retriever = FiscalRAGRetriever(config)

    queries = [custom_query] if custom_query else VALIDATION_QUERIES
    VAL_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = VAL_DIR / f"validation_{ts}.json"

    validation_log: dict = {
        "timestamp": ts,
        "modelo_embedding": config.embedding_model_name,
        "collection": config.collection_name,
        "queries": [],
        "all_passed": True,
    }

    all_passed = True
    for query in queries:
        print(f"\n[QUERY] {query}")
        results = retriever.retrieve(query, top_k=config.default_top_k)

        if not results:
            print("   [WARN] Sin resultados")
            all_passed = False
        else:
            for ctx in results:
                print(f"\n  [{ctx.rank}] Similitud: {ctx.similarity:.4f} | Importancia: {ctx.importance}/5")
                print(f"       Fuente:  {ctx.filename}")
                print(f"       Sección: {ctx.section[:60]}")
                if ctx.page_number:
                    print(f"       Página:  {ctx.page_number}")
                print(f"       ID:      {ctx.chunk_id[:16]}...")
                print(f"       Texto:   {ctx.text[:200]}...")
            print(f"\n{'═'*65}\n")

        missing: set[str] = set()
        for r in results:
            for field in ("chunk_id", "source", "section", "doc_id"):
                if not getattr(r, field, None):
                    missing.add(field)

        query_ok = len(missing) == 0
        if not query_ok:
            print(f"[WARN] Campos faltantes: {missing}")
            all_passed = False
        else:
            print(f"[OK] Trazabilidad completa en {len(results)} fragmentos")

        validation_log["queries"].append({
            "query": query,
            "fragments_found": len(results),
            "trazabilidad_ok": query_ok,
            "results": [
                {
                    "rank": r.rank,
                    "chunk_id": r.chunk_id,
                    "similarity": round(r.similarity, 4),
                    "doc_id": r.doc_id,
                    "source": r.source,
                    "filename": r.filename,
                    "section": r.section,
                    "page_number": r.page_number,
                    "importance": r.importance,
                    "text_preview": r.text[:300] + "..." if len(r.text) > 300 else r.text,
                }
                for r in results
            ],
        })

    validation_log["all_passed"] = all_passed
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(validation_log, f, ensure_ascii=False, indent=2)

    status = "[OK]" if all_passed else "[WARN]"
    print(f"\n{status} Resultados guardados en: {output_path}")


def show_stats(config: RAGConfig) -> None:
    from rag.store import FiscalChromaStore
    store = FiscalChromaStore(
        chroma_path=config.chroma_path,
        collection_name=config.collection_name,
    )
    stats = store.stats()
    hashes = store.get_indexed_doc_hashes()
    print(f"\n[INFO] ChromaDB — {stats['collection']}")
    print(f"   Total chunks:  {stats['total_chunks']}")
    print(f"   Docs únicos:   {len(hashes)}")
    for h in hashes:
        print(f"   · {h[:20]}...")


def reset_db(config: RAGConfig) -> None:
    from rag.store import FiscalChromaStore
    confirm = input("[WARN] Eliminar toda la colección ChromaDB? (escribe 'si'): ")
    if confirm.strip().lower() == "si":
        store = FiscalChromaStore(
            chroma_path=config.chroma_path,
            collection_name=config.collection_name,
        )
        store.reset()
        print("[OK] Colección eliminada.")
    else:
        print("[CANCEL] Operación cancelada.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline RAG Fiscal")
    parser.add_argument("--preview",     action="store_true", help="Mostrar secciones antes de indexar")
    parser.add_argument("--query",       type=str, default=None, help="Consulta personalizada")
    parser.add_argument("--only-query",  action="store_true", help="Solo consultar, sin ingestar")
    parser.add_argument("--stats",       action="store_true", help="Estadísticas de ChromaDB")
    parser.add_argument("--reset",       action="store_true", help="Limpiar ChromaDB (desarrollo)")
    parser.add_argument(
        "--chroma-path", type=str, default=str(DB_DIR),
        help="Ruta a ChromaDB (default: ./chroma_db)",
    )
    parser.add_argument(
        "--collection", type=str, default=None,
        help="Nombre de colección ChromaDB (sobreescribe .env)",
    )
    args = parser.parse_args()

    config = load_config_from_env(chroma_path=args.chroma_path)
    if args.collection:
        config.collection_name = args.collection

    print("\n[INICIO] Pipeline RAG Fiscal")
    print(f"   Modelo embeddings : {config.embedding_model_name}")
    print(f"   Timeout           : {config.embedding_timeout}s | Reintentos: {config.embedding_max_retries}")
    print(f"   ChromaDB          : {config.chroma_path}")
    print(f"   Data dir          : {DATA_DIR}")

    if args.reset:
        reset_db(config)
    elif args.stats:
        show_stats(config)
    elif args.only_query:
        run_queries(config, args.query)
    else:
        run_ingestion(config, preview=args.preview)
        run_queries(config, args.query)


if __name__ == "__main__":
    main()
