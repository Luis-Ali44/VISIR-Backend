from datetime import datetime
from pathlib import Path

from lxml import etree

from app.repositories.documents_repository import DocumentRepository #nombre_forma_pago, tipo_comprobante


def parse_fecha(date_str: str) -> datetime:
    if not date_str:
        raise ValueError("La fecha no puede estar vacía")

    texto = str(date_str).strip()
    texto = texto.replace(",", "")
    texto = texto.replace("a.m.", "AM").replace("p.m.", "PM")
    texto = texto.replace("a. m.", "AM").replace("p. m.", "PM")
    texto = texto.replace("am", "AM").replace("pm", "PM")

    formatos = (
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y %I:%M:%S %p",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
    )

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue

    raise ValueError(f"Formato de fecha no soportado: {date_str!r}")


def map_tipo_comprobante(tipo: str, repo: DocumentRepository) -> str | None:
    return repo.tipo_comprobante(tipo)


def get_nombre_forma_pago(forma_pago: str, repo:DocumentRepository) -> str | None:
    return repo.nombre_forma_pago(forma_pago)


base__dir = Path(__file__).resolve().parent.parent.parent

RUTA_XSD_CFDI = base__dir / "resources" / "sat" / "cfdi_combinado.xsd"


if not RUTA_XSD_CFDI.exists():
    raise FileNotFoundError(f"No se encontró el archivo XSD en la ruta absoluta: {RUTA_XSD_CFDI}")

schema_cfdi = etree.XMLSchema(etree.parse(RUTA_XSD_CFDI))


def verificar_xml(xml_bytes: bytes) -> tuple[bool, list[str]]:
    try:
        xml_doc = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        return False, [f"XML mal formado: {e}"]

    es_valido = schema_cfdi.validate(xml_doc)

    errores = []
    if not es_valido:
        for error in schema_cfdi.error_log:
            errores.append(str(error))

    return es_valido, errores
