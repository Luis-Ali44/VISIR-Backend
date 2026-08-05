from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, cast

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env")

import os  # noqa: E402

from app.services.org_ingestion_service import ingestar_cfdi_organizacion  # noqa: E402
from rag.config import load_config_from_env  # noqa: E402
from rag.store import FiscalChromaStore  # noqa: E402

ID_ORG_PRUEBA = "org-test-visir-001"
ID_USUARIO_PRUEBA = "user-test-visir-001"
CFDIS_SINTETICOS: list[dict] = [
    {
        "folio_fiscal": "cfdi_sintetico_proveedor_cloud",
        "fecha_emision": "2025-01-15",
        "tipo_de_comprobante": "I",
        "metodo_pago": "PUE",
        "forma_pago": "03",
        "moneda": "MXN",
        "subtotal": 18965.52,
        "iva": 3034.48,
        "retenciones": 0.0,
        "total": 22000.00,
        "emisor": {"RFC": "XAMA900101ABC", "nombre": "Servicios Cloud MX SA de CV"},
        "receptor": {"RFC": "DEMO010101AA1", "nombre": "Empresa Demo VISIR SA de CV"},
        "conceptos": [
            {
                "descripcion": "Infraestructura en la nube enero 2025",
                "clave_prod_serv": "81112501",
                "cantidad": 1,
                "importe": 18965.52,
            }
        ],
    },
    {
        "folio_fiscal": "cfdi_sintetico_mayo_2025",
        "fecha_emision": "2025-05-15",
        "tipo_de_comprobante": "I",
        "metodo_pago": "PUE",
        "forma_pago": "03",
        "moneda": "MXN",
        "subtotal": 18965.52,
        "iva": 3034.48,
        "retenciones": 0.0,
        "total": 22000.00,
        "emisor": {"RFC": "XAMA900101ABC", "nombre": "Servicios Cloud MX SA de CV"},
        "receptor": {"RFC": "DEMO010101AA1", "nombre": "Empresa Demo VISIR SA de CV"},
        "conceptos": [
            {
                "descripcion": "Infraestructura en la nube mayo 2025",
                "clave_prod_serv": "81112501",
                "cantidad": 1,
                "importe": 18965.52,
            }
        ],
    },
    {
        "folio_fiscal": "cfdi_sintetico_junio_2025",
        "fecha_emision": "2025-06-15",
        "tipo_de_comprobante": "I",
        "metodo_pago": "PUE",
        "forma_pago": "03",
        "moneda": "MXN",
        "subtotal": 18965.52,
        "iva": 3034.48,
        "retenciones": 0.0,
        "total": 22000.00,
        "emisor": {"RFC": "XAMA900101ABC", "nombre": "Servicios Cloud MX SA de CV"},
        "receptor": {"RFC": "DEMO010101AA1", "nombre": "Empresa Demo VISIR SA de CV"},
        "conceptos": [
            {
                "descripcion": "Infraestructura en la nube junio 2025",
                "clave_prod_serv": "81112501",
                "cantidad": 1,
                "importe": 18965.52,
            }
        ],
    },
    {
        "folio_fiscal": "cfdi_sintetico_resumen_semestral",
        "fecha_emision": "2025-03-10",
        "tipo_de_comprobante": "I",
        "metodo_pago": "PUE",
        "forma_pago": "03",
        "moneda": "MXN",
        "subtotal": 34310.34,
        "iva": 5489.66,
        "retenciones": 0.0,
        "total": 39800.00,
        "emisor": {"RFC": "SOFT980201LMN", "nombre": "Software Empresarial del Norte SA de CV"},
        "receptor": {"RFC": "DEMO010101AA1", "nombre": "Empresa Demo VISIR SA de CV"},
        "conceptos": [
            {
                "descripcion": "Renovacion anual licencias software contable",
                "clave_prod_serv": "43231513",
                "cantidad": 5,
                "importe": 34310.34,
            }
        ],
    },
    {
        "folio_fiscal": "cfdi_sintetico_papeleria",
        "fecha_emision": "2025-05-22",
        "tipo_de_comprobante": "I",
        "metodo_pago": "PUE",
        "forma_pago": "28",
        "moneda": "MXN",
        "subtotal": 3000.00,
        "iva": 480.00,
        "retenciones": 0.0,
        "total": 3480.00,
        "emisor": {"RFC": "PACS810312XYZ", "nombre": "Papeleria Central SA"},
        "receptor": {"RFC": "DEMO010101AA1", "nombre": "Empresa Demo VISIR SA de CV"},
        "conceptos": [
            {
                "descripcion": "Resmas papel bond carta 500 hojas",
                "clave_prod_serv": "44121500",
                "cantidad": 10,
                "importe": 1500.00,
            },
            {
                "descripcion": "Toner HP LaserJet negro",
                "clave_prod_serv": "44101803",
                "cantidad": 2,
                "importe": 1200.00,
            },
            {
                "descripcion": "Articulos de oficina varios",
                "clave_prod_serv": "44121500",
                "cantidad": 1,
                "importe": 300.00,
            },
        ],
    },
    {
        "folio_fiscal": "cfdi_sintetico_consultoria_q2",
        "fecha_emision": "2025-06-28",
        "tipo_de_comprobante": "I",
        "metodo_pago": "PUE",
        "forma_pago": "28",
        "moneda": "MXN",
        "subtotal": 31379.31,
        "iva": 5020.69,
        "retenciones": 0.0,
        "total": 36400.00,
        "emisor": {"RFC": "CONS760405PQR", "nombre": "Consultoria Fiscal Avanzada SC"},
        "receptor": {"RFC": "DEMO010101AA1", "nombre": "Empresa Demo VISIR SA de CV"},
        "conceptos": [
            {
                "descripcion": "Consultoria fiscal y contable Q2 2025",
                "clave_prod_serv": "80101500",
                "cantidad": 1,
                "importe": 31379.31,
            }
        ],
    },
]

FILENAMES_ESPERADOS = {cfdi["folio_fiscal"] + ".md" for cfdi in CFDIS_SINTETICOS}


def indexar_fixtures(verbose: bool = True) -> None:
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    config = load_config_from_env(chroma_path=chroma_path)

    store = FiscalChromaStore(
        chroma_path=chroma_path,
        collection_name=config.org_collection_name,
    )

    chunks_antes = store.stats_by_org(ID_ORG_PRUEBA)["total_chunks"]

    if verbose:
        print(f"\n{'=' * 60}")
        print("  FIXTURES ORG RAG -- indexando CFDIs sinteticos")
        print(f"  Coleccion : {config.org_collection_name}")
        print(f"  ChromaDB  : {chroma_path}")
        print(f"  Org ID    : {ID_ORG_PRUEBA}")
        print(f"  CFDIs     : {len(CFDIS_SINTETICOS)}")
        print(f"  Chunks ya existentes para esta org: {chunks_antes}")
        print(f"{'=' * 60}\n")

    errores: list[str] = []

    for i, cfdi in enumerate(CFDIS_SINTETICOS, 1):
        folio = cfdi.get("folio_fiscal", f"cfdi-{i}")
        doc_id = f"fixture-doc-{folio}"
        if verbose:
            print(f"  [{i:02d}/{len(CFDIS_SINTETICOS)}] Indexando folio {folio}...")
        try:
            ingestar_cfdi_organizacion(
                extraccion=cfdi,
                id_organizacion=ID_ORG_PRUEBA,
                id_documento=doc_id,
                id_usuario=ID_USUARIO_PRUEBA,
                extra_metadata={"filename": f"{folio}.md"},
            )
            if verbose:
                print(f"         OK -> filename: {folio}.md")
        except Exception as exc:
            msg = f"{folio}: {exc}"
            errores.append(msg)
            print(f"         ERROR: {exc}")

    chunks_despues = store.stats_by_org(ID_ORG_PRUEBA)["total_chunks"]
    chunks_nuevos = chunks_despues - chunks_antes

    if verbose:
        print(f"\n  Chunks antes : {chunks_antes}")
        print(f"  Chunks despues: {chunks_despues}")
        print(f"  Chunks nuevos : {chunks_nuevos}")
        stats_fin = store.stats_by_org(ID_ORG_PRUEBA)
        print(f"  Documentos unicos para la org: {stats_fin['documentos_unicos']}")
        print(f"{'=' * 60}\n")

    results_meta = store.collection.get(
        where=cast(Any, {"id_organizacion": {"$eq": ID_ORG_PRUEBA}}),
        include=["metadatas"],
    )
    metadatas_meta = results_meta["metadatas"] or []
    filenames_indexados = {m.get("filename", "") for m in metadatas_meta}
    faltantes = FILENAMES_ESPERADOS - filenames_indexados
    if faltantes:
        raise RuntimeError(
            "Los siguientes filenames esperados no quedaron indexados en ChromaDB: "
            + ", ".join(sorted(faltantes))
        )

    if errores:
        raise RuntimeError(
            f"{len(errores)} CFDI(s) fallaron durante la ingesta:\n"
            + "\n".join(f"  - {e}" for e in errores)
        )

    if chunks_nuevos == 0 and chunks_despues < chunks_antes:
        raise RuntimeError(
            f"La ingesta redujo el conteo de chunks para org={ID_ORG_PRUEBA}. "
            "Revisa la configuracion de embeddings o ChromaDB."
        )

    if verbose:
        print(
            "  Verificación OK: filenames y conteo de chunks "
            "coinciden con el dataset de evaluación.\n"
        )


def limpiar_fixtures(verbose: bool = True) -> None:
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    config = load_config_from_env(chroma_path=chroma_path)

    store = FiscalChromaStore(
        chroma_path=chroma_path,
        collection_name=config.org_collection_name,
    )

    results = store.collection.get(
        where=cast(Any, {"id_organizacion": {"$eq": ID_ORG_PRUEBA}}),
        include=[],
    )
    ids_a_borrar = results["ids"]

    if not ids_a_borrar:
        if verbose:
            print(f"  No se encontraron chunks para org={ID_ORG_PRUEBA}. Nada que limpiar.")
        return

    store.collection.delete(ids=ids_a_borrar)

    if verbose:
        print(f"  Eliminados {len(ids_a_borrar)} chunks de la org de prueba.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fixtures de CFDIs sinteticos para evaluaciones de OrgRAGRetriever."
    )
    parser.add_argument(
        "--limpiar",
        action="store_true",
        help="Elimina los chunks de la org de prueba en lugar de indexarlos.",
    )
    parser.add_argument(
        "--silencioso",
        action="store_true",
        help="Suprime la salida por consola.",
    )
    args = parser.parse_args()

    if args.limpiar:
        limpiar_fixtures(verbose=not args.silencioso)
    else:
        indexar_fixtures(verbose=not args.silencioso)


if __name__ == "__main__":
    main()
