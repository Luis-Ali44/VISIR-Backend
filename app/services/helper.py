from datetime import datetime

from app.repositories.documents_repository import nombre_forma_pago, tipo_comprobante


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


def map_tipo_comprobante(tipo: str) -> str:
    return tipo_comprobante(tipo)


def get_nombre_forma_pago(forma_pago: str) -> str:
    return nombre_forma_pago(forma_pago)
