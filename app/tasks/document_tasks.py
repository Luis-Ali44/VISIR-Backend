import tempfile
from pathlib import Path

import structlog
from celery import Celery

from app.core.config import settings
from app.core.logging import configurar_logging
from app.repositories.documents_repository import (
    actualizar_estado_documento,
    delete_document_metadata,
    delete_document_storage,
    descargar_documento_storage,
    save_extracciones_repository,
)
from app.services.Extraccion.pipeline import procesar
from app.services.helper import get_nombre_forma_pago, map_tipo_comprobante, parse_fecha

configurar_logging()


log = structlog.get_logger()

REDIS_URL = settings.REDIS_URL
celery_app = Celery("Extraccion_pipeline", broker=REDIS_URL, backend=REDIS_URL)


@celery_app.task(name="Procesar_documentos")
# EJECUTAMOS EL PIPELINE DE PAO PARA EXTRAER LOS DATOS
def iniciar_procesamiento(
    id_documento: str, id_organizacion: str, ruta_archivo: str, nombre_archivo: str
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
        limpiar_fallo(ruta_storage=ruta_archivo, id_doc=id_documento)
        return {"status": "fallido", "details": "No se pudo procesar el archivo"}

    #   Validamos el resultado de la extracción
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("cfdis"), list)
        or not data.get("cfdis")
    ):
        log.info("No_se_encontraron_cfdis")
        limpiar_fallo(ruta_storage=ruta_archivo, id_doc=id_documento)
        return {"status": "failed", "detail": "No se encontraron CFDIs"}

    log.info("cfdis_extraidos", cantidad=len(data.get("cfdis", [])))

    #   Mapeos y formato de filas
    rows = []
    for item in data.get("cfdis", []):
        datos = item.get("datos", {}) if isinstance(item, dict) else {}

        forma_pago = datos.get("forma_pago")
        fecha_emision_raw = datos.get("fecha_emision")
        tipo_comprobante_raw = datos.get("tipo_de_comprobante")

        rows.append(
            {
                "folio_fiscal": datos.get("folio_fiscal"),
                "total": datos.get("total"),
                "metadatos": datos,
                "fecha_emision": parse_fecha(str(fecha_emision_raw)).isoformat()
                if fecha_emision_raw is not None
                else None,
                "tipo_comprobante": map_tipo_comprobante(str(tipo_comprobante_raw))
                if tipo_comprobante_raw is not None
                else None,
                "metodo_pago": datos.get("metodo_pago"),
                "estado": "procesado",
                "rfc_emisor": datos.get("emisor", {}).get("RFC"),
                "nombre_emisor": datos.get("emisor", {}).get("nombre"),
                "rfc_receptor": datos.get("receptor", {}).get("RFC"),
                "nombre_receptor": datos.get("receptor", {}).get("nombre"),
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
        return {"status": "success", "id_documento": id_documento}

    except Exception as exc:
        log.error("guardado_extracciones_fallido", error=str(exc))
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
