
import logging
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from ingestion.pipeline import RAGIngestionPipeline
from rag.config import RAGConfig, load_config_from_env

logger = logging.getLogger(__name__)

_org_pipeline: RAGIngestionPipeline | None = None


def get_org_ingestion_pipeline() -> RAGIngestionPipeline:
    global _org_pipeline
    if _org_pipeline is None:
        base_config = load_config_from_env()
        org_config: RAGConfig = replace(
            base_config,
            collection_name=base_config.org_collection_name,
        )
        _org_pipeline = RAGIngestionPipeline(org_config)
    return _org_pipeline


def _cfdi_a_texto(extraccion: dict[str, Any]) -> str:
    emisor = extraccion.get("emisor") or {}
    receptor = extraccion.get("receptor") or {}
    conceptos = extraccion.get("conceptos") or []

    lineas = [
        f"Comprobante Fiscal Digital (CFDI) folio fiscal {extraccion.get('folio_fiscal', 'N/D')}",
        f"Fecha de emisión: {extraccion.get('fecha_emision', 'N/D')}",
        f"Emisor: {emisor.get('nombre', 'N/D')} (RFC {emisor.get('RFC', 'N/D')})",
        f"Receptor: {receptor.get('nombre', 'N/D')} (RFC {receptor.get('RFC', 'N/D')})",
        f"Método de pago: {extraccion.get('metodo_pago', 'N/D')} | "
        f"Forma de pago: {extraccion.get('forma_pago', 'N/D')} | "
        f"Moneda: {extraccion.get('moneda', 'N/D')}",
        f"Subtotal: {extraccion.get('subtotal', 'N/D')} | "
        f"IVA: {extraccion.get('iva', 'N/D')} | "
        f"Retenciones: {extraccion.get('retenciones', 'N/D')} | "
        f"Total: {extraccion.get('total', 'N/D')}",
        "",
        "Conceptos facturados:",
    ]
    for c in conceptos:
        lineas.append(
            f"- {c.get('descripcion', 'N/D')} | clave SAT {c.get('clave_prod_serv', 'N/D')} | "
            f"cantidad {c.get('cantidad', 'N/D')} | importe {c.get('importe', 'N/D')}"
        )

    return "\n".join(lineas)


def ingestar_cfdi_organizacion(
    extraccion: dict[str, Any],
    id_organizacion: str,
    id_documento: str,
    id_usuario: str,
    extra_metadata: dict[str, Any] | None = None,
) -> None:
    folio = extraccion.get("folio_fiscal") or id_documento
    filename_canonical = f"{folio}.md"

    texto = _cfdi_a_texto(extraccion)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(texto)
        tmp_path = tmp.name

    try:
        pipeline = get_org_ingestion_pipeline()
        metadata = {
            "filename": filename_canonical,
            "id_organizacion": id_organizacion,
            "id_documento": id_documento,
            "id_usuario": id_usuario,
            "tipo_documento": "cfdi",
            "folio_fiscal": folio,
        }
        if extra_metadata:
            metadata.update(extra_metadata)
        metadata["filename"] = metadata.get("filename") or filename_canonical

        pipeline.ingest(
            pdf_path=tmp_path,
            importance=pipeline.config.default_importance,
            extra_metadata=metadata,
            force_reingest=True,
        )
    except Exception:
        logger.exception(
            "Fallo al ingestar CFDI al RAG de organización",
            extra={"id_organizacion": id_organizacion, "id_documento": id_documento},
        )
        raise
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def ingestar_documento_general_organizacion(
    ruta_local: str,
    id_organizacion: str,
    id_documento: str,
    id_usuario: str,
) -> None:
    try:
        pipeline = get_org_ingestion_pipeline()
        pipeline.ingest(
            pdf_path=ruta_local,
            importance=pipeline.config.default_importance,
            extra_metadata={
                "id_organizacion": id_organizacion,
                "id_documento": id_documento,
                "id_usuario": id_usuario,
                "tipo_documento": "general",
            },
            force_reingest=False,  
        )
    except Exception:
        logger.exception(
            "Fallo al ingestar documento general al RAG de organización",
            extra={"id_organizacion": id_organizacion, "id_documento": id_documento},
        )
