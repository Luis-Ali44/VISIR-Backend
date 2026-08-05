from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, cast

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env")

import os  # noqa: E402

from app.services.org_ingestion_service import ingestar_cfdi_organizacion  # noqa: E402
from evaluaciones.fixtures_org import CFDIS_SINTETICOS, FILENAMES_ESPERADOS  # noqa: E402
from rag.config import load_config_from_env  # noqa: E402
from rag.store import FiscalChromaStore  # noqa: E402

ID_ORGANIZACION_PRUEBA = "11111111-1111-1111-1111-111111111111"


def indexar_fixtures(verbose: bool = True) -> None:
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    config = load_config_from_env(chroma_path=chroma_path)

    store = FiscalChromaStore(
        chroma_path=chroma_path,
        collection_name=config.org_collection_name,
    )

    chunks_antes = store.stats_by_org(ID_ORGANIZACION_PRUEBA)["total_chunks"]

    if verbose:
        print(f"\n{'=' * 60}")
        print("  INDEXANDO CFDIs SINTÉTICOS bajo UUID")
        print(f"  Org ID  : {ID_ORGANIZACION_PRUEBA}")
        print(f"  CFDIs   : {len(CFDIS_SINTETICOS)}")
        print(f"  Chunks existentes: {chunks_antes}")
        print(f"{'=' * 60}\n")

    errores: list[str] = []
    for i, cfdi in enumerate(CFDIS_SINTETICOS, 1):
        folio = cfdi.get("folio_fiscal", f"cfdi-{i}")
        doc_id = f"fixture-doc-{folio}"
        if verbose:
            print(f"  [{i:02d}/{len(CFDIS_SINTETICOS)}] Indexando {folio}...")
        try:
            ingestar_cfdi_organizacion(
                extraccion=cfdi,
                id_organizacion=ID_ORGANIZACION_PRUEBA,
                id_documento=doc_id,
                id_usuario="eval",
                extra_metadata={"filename": f"{folio}.md"},
            )
            if verbose:
                print(f"         OK -> {folio}.md")
        except Exception as exc:
            msg = f"{folio}: {exc}"
            errores.append(msg)
            print(f"         ERROR: {exc}")

    chunks_despues = store.stats_by_org(ID_ORGANIZACION_PRUEBA)["total_chunks"]
    chunks_nuevos = chunks_despues - chunks_antes

    if verbose:
        print(f"\n  Chunks antes : {chunks_antes}")
        print(f"  Chunks después: {chunks_despues}")
        print(f"  Chunks nuevos : {chunks_nuevos}")
        print(f"{'=' * 60}\n")

    results_meta = store.collection.get(
        where=cast(Any, {"id_organizacion": {"$eq": ID_ORGANIZACION_PRUEBA}}),
        include=["metadatas"],
    )
    metadatas_meta = results_meta["metadatas"] or []
    filenames_indexados = {m.get("filename", "") for m in metadatas_meta}
    faltantes = FILENAMES_ESPERADOS - filenames_indexados
    if faltantes:
        raise RuntimeError("Filenames esperados no indexados: " + ", ".join(sorted(faltantes)))

    if errores:
        raise RuntimeError(
            f"{len(errores)} CFDI(s) fallaron:\n" + "\n".join(f"  - {e}" for e in errores)
        )

    if verbose:
        print("  Verificación OK: todos los sintéticos indexados bajo UUID.\n")


def stats() -> None:
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    config = load_config_from_env(chroma_path=chroma_path)
    store = FiscalChromaStore(
        chroma_path=chroma_path,
        collection_name=config.org_collection_name,
    )
    s = store.stats_by_org(ID_ORGANIZACION_PRUEBA)
    print(
        f"Org {ID_ORGANIZACION_PRUEBA}: {s['total_chunks']} chunks, "
        f"{s['documentos_unicos']} documentos"
    )


if __name__ == "__main__":
    indexar_fixtures()
