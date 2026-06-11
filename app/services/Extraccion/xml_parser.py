from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


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

    emisor = root.find(".//{*}Emisor")
    receptor = root.find(".//{*}Receptor")

    fecha_str = root.get("Fecha")
    try:
        fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00")).date().isoformat()
    except Exception:
        fecha = None

    tfd = root.find(".//{*}TimbreFiscalDigital")
    folio_fiscal = tfd.get("UUID") if tfd is not None else None

    subtotal = float(root.get("SubTotal", 0) or 0)
    total = float(root.get("Total", 0) or 0)

    impuestos = root.find("./{*}Impuestos")
    total_iva = None
    if impuestos is not None:
        iva_str = impuestos.get("TotalImpuestosTrasladados")
        if iva_str:
            total_iva = float(iva_str)

    conceptos = []
    for con in root.findall(".//{*}Concepto"):
        conceptos.append(
            {
                "descripcion": con.get("Descripcion"),
                "clave_prod_serv": con.get("ClaveProdServ"),
                "unidad": con.get("ClaveUnidad"),
                "cantidad": float(con.get("Cantidad", 0) or 0),
                "valor_unitario": float(con.get("ValorUnitario", 0) or 0),
                "importe": float(con.get("Importe", 0) or 0),
                "iva": None,
            }
        )

    return {
        "version": version,
        "emisor_rfc": emisor.get("Rfc") if emisor is not None else None,
        "emisor_nombre": emisor.get("Nombre") if emisor is not None else None,
        "receptor_rfc": receptor.get("Rfc") if receptor is not None else None,
        "receptor_nombre": receptor.get("Nombre") if receptor is not None else None,
        "folio_fiscal": folio_fiscal,
        "fecha_emision": fecha,
        "metodo_pago": root.get("MetodoPago"),
        "forma_pago": root.get("FormaPago"),
        "moneda": root.get("Moneda"),
        "subtotal": subtotal,
        "iva": total_iva,
        "total": total,
        "conceptos": conceptos,
    }
