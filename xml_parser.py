from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


def _float_or_none(valor: str | None) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def _normalizar_fecha(fecha_str: str | None) -> str | None:
    if not fecha_str:
        return None
    fecha_str = fecha_str.split("+")[0].split("Z")[0].strip()
    if "." in fecha_str:
        fecha_str = fecha_str.split(".")[0]
    if len(fecha_str) == 10:
        fecha_str = fecha_str + "T00:00:00"
    try:
        datetime.fromisoformat(fecha_str)
        return fecha_str
    except ValueError:
        return None


def extraer_desde_xml(ruta_xml: str | Path) -> dict:
    tree = ET.parse(str(ruta_xml))
    root = tree.getroot()

    version_raw = root.get("Version")
    if not version_raw:
        tag = root.tag
        if "/cfd/4" in tag:
            version_raw = "4.0"
        elif "/cfd/3" in tag:
            version_raw = "3.3"
        else:
            version_raw = "4.0"
    try:
        version = f"{float(version_raw):.1f}"
    except (ValueError, TypeError):
        version = str(version_raw)

    emisor   = root.find(".//{*}Emisor")
    receptor = root.find(".//{*}Receptor")
    tfd      = root.find(".//{*}TimbreFiscalDigital")

    folio_fiscal  = tfd.get("UUID") if tfd is not None else None
    fecha_emision = _normalizar_fecha(root.get("Fecha"))

    emisor_datos: dict = {
        "nombre": emisor.get("Nombre") if emisor is not None else None,
        "RFC":    emisor.get("Rfc")    if emisor is not None else None,
    }

    receptor_datos: dict = {
        "nombre": receptor.get("Nombre") if receptor is not None else None,
        "RFC":    receptor.get("Rfc")    if receptor is not None else None,
    }

    moneda    = root.get("Moneda")
    subtotal  = _float_or_none(root.get("SubTotal"))
    total     = _float_or_none(root.get("Total"))
    descuento = _float_or_none(root.get("Descuento"))

    impuestos   = root.find("./{*}Impuestos")
    total_iva   = None
    retenciones = None
    if impuestos is not None:
        total_iva   = _float_or_none(impuestos.get("TotalImpuestosTrasladados"))
        retenciones = _float_or_none(impuestos.get("TotalImpuestosRetenidos"))

    conceptos: list[dict] = []
    for con in root.findall(".//{*}Concepto"):
        iva_concepto = None
        for traslado in con.findall(".//{*}Traslado"):
            if traslado.get("Impuesto") == "002":
                iva_concepto = _float_or_none(traslado.get("Importe"))
                break

        conceptos.append({
            "descripcion":     con.get("Descripcion"),
            "clave_prod_serv": con.get("ClaveProdServ"),
            "unidad":          con.get("ClaveUnidad"),
            "cantidad":        _float_or_none(con.get("Cantidad")),
            "valor_unitario":  _float_or_none(con.get("ValorUnitario")),
            "descuento":       _float_or_none(con.get("Descuento")),
            "importe":         _float_or_none(con.get("Importe")),
            "iva":             iva_concepto,
        })

    return {
        "version":       version,
        "folio_fiscal":  folio_fiscal,
        "fecha_emision": fecha_emision,
        "metodo_pago":   root.get("MetodoPago"),
        "forma_pago":    root.get("FormaPago"),
        "moneda":        moneda,
        "emisor":        emisor_datos,
        "receptor":      receptor_datos,
        "conceptos":     conceptos,
        "subtotal":      subtotal,
        "descuento":     descuento,
        "iva":           total_iva,
        "retenciones":   retenciones,
        "total":         total,
    }