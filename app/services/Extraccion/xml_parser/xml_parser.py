from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from .complementos import (
    addenda,
    carta_porte,
    comercio_exterior,
    ine,
    leyendas_fiscales,
    nomina,
    pagos,
)


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

    emisor = root.find(".//{*}Emisor")
    receptor = root.find(".//{*}Receptor")
    tfd = root.find(".//{*}TimbreFiscalDigital")

    folio_fiscal = tfd.get("UUID") if tfd is not None else None
    fecha_emision = _normalizar_fecha(root.get("Fecha"))
    fecha_timbrado = _normalizar_fecha(tfd.get("FechaTimbrado")) if tfd is not None else None
    rfc_prov_certif = tfd.get("RfcProvCertif") if tfd is not None else None
    no_certificado_sat = tfd.get("NoCertificadoSAT") if tfd is not None else None

    emisor_datos: dict = {
        "nombre": emisor.get("Nombre") if emisor is not None else None,
        "RFC": emisor.get("Rfc") if emisor is not None else None,
        "regimen_fiscal": emisor.get("RegimenFiscal") if emisor is not None else None,
    }

    receptor_datos: dict = {
        "nombre": receptor.get("Nombre") if receptor is not None else None,
        "RFC": receptor.get("Rfc") if receptor is not None else None,
        "uso_cfdi": receptor.get("UsoCFDI") if receptor is not None else None,
        "regimen_fiscal": receptor.get("RegimenFiscalReceptor") if receptor is not None else None,
        "domicilio_fiscal": (
             receptor.get("DomicilioFiscalReceptor") if receptor is not None else None
        ),
    }

    moneda = root.get("Moneda")
    tipo_cambio = _float_or_none(root.get("TipoCambio"))
    subtotal = _float_or_none(root.get("SubTotal"))
    total = _float_or_none(root.get("Total"))
    descuento = _float_or_none(root.get("Descuento"))

    impuestos = root.find("./{*}Impuestos")
    total_iva = None
    retenciones = None
    if impuestos is not None:
        total_iva = _float_or_none(impuestos.get("TotalImpuestosTrasladados"))
        retenciones = _float_or_none(impuestos.get("TotalImpuestosRetenidos"))

    conceptos: list[dict] = []
    for con in root.findall(".//{*}Concepto"):
        iva_concepto = None
        for traslado in con.findall(".//{*}Traslado"):
            if traslado.get("Impuesto") == "002":
                iva_concepto = _float_or_none(traslado.get("Importe"))
                break

        conceptos.append({
            "descripcion": con.get("Descripcion"),
            "clave_prod_serv": con.get("ClaveProdServ"),
            "clave_unidad": con.get("ClaveUnidad"),
            "unidad": con.get("Unidad"),
            "cantidad": _float_or_none(con.get("Cantidad")),
            "valor_unitario": _float_or_none(con.get("ValorUnitario")),
            "descuento": _float_or_none(con.get("Descuento")),
            "importe": _float_or_none(con.get("Importe")),
            "iva": iva_concepto,
            "objeto_imp": con.get("ObjetoImp"),
        })

    carta_porte_datos = carta_porte.parse(root)
    comercio_exterior_datos = comercio_exterior.parse(root)
    nomina_datos = nomina.parse(root)
    pagos_datos = pagos.parse(root)
    ine_datos = ine.parse(root)
    leyendas_fiscales_datos = leyendas_fiscales.parse(root)
    addenda_datos = addenda.parse(root)

    resultado = {
        "version": version,
        "serie": root.get("Serie"),
        "folio": root.get("Folio"),
        "tipo_comprobante": root.get("TipoDeComprobante"),
        "lugar_expedicion": root.get("LugarExpedicion"),
        "exportacion": root.get("Exportacion"),
        "no_certificado": root.get("NoCertificado"),
        "folio_fiscal": folio_fiscal,
        "fecha_emision": fecha_emision,
        "fecha_timbrado": fecha_timbrado,
        "rfc_proveedor_certificacion": rfc_prov_certif,
        "no_certificado_sat": no_certificado_sat,
        "metodo_pago": root.get("MetodoPago"),
        "forma_pago": root.get("FormaPago"),
        "moneda": moneda,
        "tipo_cambio": tipo_cambio,
        "emisor": emisor_datos,
        "receptor": receptor_datos,
        "conceptos": conceptos,
        "subtotal": subtotal,
        "descuento": descuento,
        "iva": total_iva,
        "retenciones": retenciones,
        "total": total,
    }

    if carta_porte_datos is not None:
        resultado["complemento_carta_porte"] = carta_porte_datos
    if comercio_exterior_datos is not None:
        resultado["complemento_comercio_exterior"] = comercio_exterior_datos
    if nomina_datos is not None:
        resultado["complemento_nomina"] = nomina_datos
    if pagos_datos is not None:
        resultado["complemento_pagos"] = pagos_datos
    if ine_datos is not None:
        resultado["complemento_ine"] = ine_datos
    if leyendas_fiscales_datos is not None:
        resultado["complemento_leyendas_fiscales"] = leyendas_fiscales_datos
    if addenda_datos is not None:
        resultado["addenda"] = addenda_datos

    return resultado
