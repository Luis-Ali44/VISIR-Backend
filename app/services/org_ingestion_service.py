# app/services/org_ingestion_service.py
"""
Ingesta documentos subidos por una organización (CFDIs parseados o
documentos generales en PDF/MD/TXT) hacia la colección compartida de
Chroma `documentos_organizacion`, usando el mismo pipeline de chunking
y embeddings que ya existe para la normativa SAT (ingestion/pipeline.py),
pero apuntando a una RAGConfig con collection_name distinto y agregando
id_organizacion / id_documento / id_usuario / tipo_documento como
metadata obligatoria de cada chunk.

Se ejecuta en background tras subir_documento_service (ver
documents_service.py), para no bloquear la respuesta HTTP de /cargar
con el tiempo de embeddings.
"""
import logging
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from ingestion.pipeline import RAGIngestionPipeline
from rag.config import RAGConfig, load_config_from_env

logger = logging.getLogger(__name__)

# Caché simple del pipeline de ingesta de organización: construirlo de
# nuevo en cada subida recargaría el modelo de embeddings y reabriría
# Chroma en cada request, lo cual es costoso. Se construye una sola vez
# por proceso, igual que rag_service en app.state.
_org_pipeline: RAGIngestionPipeline | None = None


def get_org_ingestion_pipeline() -> RAGIngestionPipeline:
    global _org_pipeline
    if _org_pipeline is None:
        base_config = load_config_from_env()
        # Mismo embedding/chunking que la normativa SAT, pero apuntando
        # a la colección de organización en vez de documentos_fiscales.
        org_config: RAGConfig = replace(
            base_config,
            collection_name=base_config.org_collection_name,
        )
        _org_pipeline = RAGIngestionPipeline(org_config)
    return _org_pipeline


def _cfdi_a_texto(extraccion: dict[str, Any]) -> str:
    """
    Convierte los datos ya parseados de un CFDI (el dict que produce
    app/services/Extraccion/xml_parser.py + pipeline.py) en un texto
    legible para embeddings. No se le pasa el XML crudo al chunker:
    un texto estructurado en español da mejor similitud semántica
    contra preguntas en lenguaje natural ("¿cuánto le pagué a tal
    proveedor por tal concepto?") que las etiquetas XML originales.
    """
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
) -> None:
    """
    Ingesta el contenido textual de un CFDI ya parseado hacia la
    colección de organización. Se llama desde documents_service tras
    guardar la fila en `extracciones`.
    """
    texto = _cfdi_a_texto(extraccion)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(texto)
        tmp_path = tmp.name

    try:
        pipeline = get_org_ingestion_pipeline()
        pipeline.ingest(
            pdf_path=tmp_path,  # nombre del parámetro heredado; acepta .md también
            importance=pipeline.config.default_importance,
            extra_metadata={
                "id_organizacion": id_organizacion,
                "id_documento": id_documento,
                "id_usuario": id_usuario,
                "tipo_documento": "cfdi",
                "folio_fiscal": extraccion.get("folio_fiscal") or "",
            },
            force_reingest=True,  # cada CFDI es un archivo temporal nuevo; nunca está "ya indexado" por hash
        )
    except Exception:
        logger.exception(
            "Fallo al ingestar CFDI al RAG de organización",
            extra={"id_organizacion": id_organizacion, "id_documento": id_documento},
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def ingestar_documento_general_organizacion(
    ruta_local: str,
    id_organizacion: str,
    id_documento: str,
    id_usuario: str,
) -> None:
    """
    Ingesta un documento general (PDF/MD/TXT) subido por la organización
    —no un CFDI— hacia la colección de organización. `ruta_local` debe
    ser una ruta en disco accesible (p. ej. un archivo temporal donde se
    volcó el contenido recibido en el UploadFile antes de subirlo a
    Storage), ya que ingestion/pipeline.py trabaja sobre archivos, no
    sobre bytes en memoria.
    """
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
            force_reingest=False,  # aquí sí vale el dedupe por hash de archivo real
        )
    except Exception:
        logger.exception(
            "Fallo al ingestar documento general al RAG de organización",
            extra={"id_organizacion": id_organizacion, "id_documento": id_documento},
        )
