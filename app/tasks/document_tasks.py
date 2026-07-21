import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import sentry_sdk
import structlog
from celery import Celery

from app.core.config import settings
from app.core.logging import configurar_logging
from app.core.sentry import configurar_sentry
from app.repositories.documents_repository import (
    actualizar_estado_documento,
    delete_document_metadata,
    delete_document_storage,
    descargar_documento_storage,
    save_extracciones_repository,
)
from app.services.Extraccion.pipeline import procesar
from app.services.helper import get_nombre_forma_pago, map_tipo_comprobante, parse_fecha
from app.services.org_ingestion_service import ingestar_cfdi_organizacion

configurar_sentry()
configurar_logging()


log = structlog.get_logger()

REDIS_URL = settings.REDIS_URL
celery_app = Celery("Extraccion_pipeline", broker=REDIS_URL, backend=REDIS_URL)


def _normalizar_cfdis_extraidos(data: dict) -> list[dict[str, Any]]:

    if not isinstance(data, dict):
        return []

    if data.get("fuente") == "xml":
        datos = data.get("datos")
        return [datos] if isinstance(datos, dict) else []

    cfdis = data.get("cfdis")
    if not isinstance(cfdis, list):
        return []

    resultado = []
    for item in cfdis:
        datos = item.get("datos") if isinstance(item, dict) else None
        if isinstance(datos, dict):
            resultado.append(datos)
    return resultado


@celery_app.task(name="Procesar_documentos")
# EJECUTAMOS EL PIPELINE DE PAOLA PARA EXTRAER LOS DATOS
def iniciar_procesamiento(
    id_documento: str, id_organizacion: str, id_usuario: str, ruta_archivo: str, nombre_archivo: str
) -> dict[str, str]:
    log.info("ocr_iniciado", id_documento=id_documento, id_organizacion=id_organizacion)

    contenido = descargar_documento_storage(ruta_archivo)

    if contenido is None:
        log.error("descarga_storage_fallida", id_documento=id_documento, ruta_archivo=ruta_archivo)
        limpiar_fallo(ruta_archivo, id_documento)
        return {"status": "failed", "detail": "No se pudo descargar el archivo de storage"}

    ext = Path(nombre_archivo or "archivo.pdf").suffix
    tmp_path = None

    #   Archivo temporal
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(contenido)
            tmp_path = Path(tmp.name)

        #   Proceso de paola
        log.info("procesamiento_pipeline_iniciado")
        data = procesar(ruta_archivo=tmp_path, guardar_txt=False)
        log.info("procesamiento_pipeline_completado")

    except Exception as exec:
        log.error(
            "procesamiento_fallido",
            id_documento=id_documento,
            nombre_archivo=nombre_archivo,
            error=str(exec),
        )
        sentry_sdk.capture_exception(exec)
        limpiar_fallo(ruta_storage=ruta_archivo, id_doc=id_documento)
        return {"status": "fallido", "details": "No se pudo procesar el archivo"}
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    cfdis_datos = _normalizar_cfdis_extraidos(data)

    if not cfdis_datos:
        log.error("No_se_encontraron_cfdis", id_documento=id_documento)
        sentry_sdk.capture_message(
            f"No se encontraron cfdis para documento {id_documento}", level="warning"
        )
        limpiar_fallo(ruta_storage=ruta_archivo, id_doc=id_documento)
        return {"status": "failed", "detail": "No se encontraron CFDIs"}

    log.info("cfdis_extraidos", cantidad=len(cfdis_datos))

    #   Mapeos y formato de filas
    rows = []
    for datos in cfdis_datos:
        forma_pago = datos.get("forma_pago")
        fecha_emision_raw = datos.get("fecha_emision")
        tipo_comprobante_raw = datos.get("tipo_comprobante")

        # Parse fecha — fallback a now() si el LLM no extrajo una fecha válida
        try:
            fecha_iso = (
                parse_fecha(str(fecha_emision_raw)).isoformat()
                if fecha_emision_raw is not None
                else None
            )
        except ValueError:
            fecha_iso = None

        emisor = datos.get("emisor") or {}
        receptor = datos.get("receptor") or {}

        rows.append(
            {
                # Columnas NOT NULL — proveer defaults seguros
                "folio_fiscal": datos.get("folio_fiscal") or "SIN-UUID",
                "total": float(datos.get("total") or 0.0),
                "metadatos": datos,
                "fecha_emision": fecha_iso or datetime.now().isoformat(),
                "tipo_comprobante": (
                    map_tipo_comprobante(str(tipo_comprobante_raw))
                    if tipo_comprobante_raw is not None
                    else None
                )
                or "Ingreso",
                "metodo_pago": datos.get("metodo_pago") or "PUE",
                "estado": "procesado",
                "rfc_emisor": emisor.get("RFC") or "XAXX010101000",
                "nombre_emisor": emisor.get("nombre") or "Sin nombre",
                "rfc_receptor": receptor.get("RFC") or "XAXX010101000",
                "nombre_receptor": receptor.get("nombre") or "Sin nombre",
                "uso_cfdi": receptor.get("uso_cfdi"),
                "regimen_fiscal": receptor.get("regimen_fiscal"),
                "id_documento": id_documento,
                "id_organizacion": id_organizacion,
                "forma_pago": get_nombre_forma_pago(str(forma_pago)) if forma_pago else None,
            }
        )

    log.info("filas_mapeadas", cantidad=len(rows))

    # Categoria se mantiene fuera del flujo actual hasta que el OCR la entregue.
    # categoria = get_id_categoria()
    # id_categoria = UUID(categoria) if categoria else None

    # Guardamos las extracciones en la base de datos
    try:
        save_extracciones_repository(rows)
        actualizar_estado_documento(id_documento)
        log.info("documento_procesado_exitosamente")

        for datos in cfdis_datos:
            log.info("ingestando_cfdi_organizacion", id_documento=id_documento)
            ingestar_cfdi_organizacion(
                extraccion=datos,
                id_organizacion=id_organizacion,
                id_documento=str(id_documento),
                id_usuario=id_usuario,
            )

        return {"status": "success", "id_documento": id_documento}

    except Exception as exc:
        log.error("guardado_extracciones_fallido", error=str(exc))
        sentry_sdk.capture_exception(exc)
        limpiar_fallo(ruta_archivo, id_documento)
        return {"status": "failed", "detail": "No se pudieron guardar las extracciones en la BD"}


def limpiar_fallo(ruta_storage: str, id_doc: str) -> None:
    """Función interna para mantener la consistencia si algo truena"""
    try:
        delete_document_storage(ruta_storage)
        delete_document_metadata(id_doc)
        log.warning("limpieza_por_fallo_completada", id_documento=id_doc)

    except Exception as e:
        log.error("limpieza_por_fallo_critica", id_documento=id_doc, error=str(e))
