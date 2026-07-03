from __future__ import annotations

import xml.etree.ElementTree as ET


def _float_or_none(valor: str | None) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def _extraer_totales(pagos: ET.Element) -> dict | None:
    totales = pagos.find("./{*}Totales")
    if totales is None:
        return None
    return {
        "total_retenciones_iva":            _float_or_none(
            totales.get("TotalRetencionesIVA")
        ),
        "total_retenciones_isr":             _float_or_none(
            totales.get("TotalRetencionesISR")
        ),
        "total_retenciones_ieps":            _float_or_none(
            totales.get("TotalRetencionesIEPS")
        ),
        "total_traslados_base_iva16":        _float_or_none(
            totales.get("TotalTrasladosBaseIVA16")
        ),
        "total_traslados_impuesto_iva16": _float_or_none(
            totales.get("TotalTrasladosImpuestoIVA16")
        ),
        "total_traslados_base_iva8":         _float_or_none(
            totales.get("TotalTrasladosBaseIVA8")
        ),
        "total_traslados_impuesto_iva8":     _float_or_none(
            totales.get("TotalTrasladosImpuestoIVA8")
        ),
        "total_traslados_base_iva0":         _float_or_none(
            totales.get("TotalTrasladosBaseIVA0")
        ),
        "total_traslados_impuesto_iva0":     _float_or_none(
            totales.get("TotalTrasladosImpuestoIVA0")
        ),
        "total_traslados_base_iva_exento":   _float_or_none(
            totales.get("TotalTrasladosBaseIVAExento")
        ),
        "monto_total_pagos":                 _float_or_none(
            totales.get("MontoTotalPagos")
        ),
    }


def _extraer_impuestos_dr(docto: ET.Element) -> dict:
    nodo = docto.find("./{*}ImpuestosDR")
    traslados: list[dict] = []
    retenciones: list[dict] = []
    if nodo is not None:
        for t in nodo.findall("./{*}TrasladosDR/{*}TrasladoDR"):
            traslados.append({
                "base_dr":         _float_or_none(t.get("BaseDR")),
                "impuesto_dr":     t.get("ImpuestoDR"),
                "tipo_factor_dr":  t.get("TipoFactorDR"),
                "tasa_o_cuota_dr": _float_or_none(t.get("TasaOCuotaDR")),
                "importe_dr":      _float_or_none(t.get("ImporteDR")),
            })
        for r in nodo.findall("./{*}RetencionesDR/{*}RetencionDR"):
            retenciones.append({
                "base_dr":         _float_or_none(r.get("BaseDR")),
                "impuesto_dr":     r.get("ImpuestoDR"),
                "tipo_factor_dr":  r.get("TipoFactorDR"),
                "tasa_o_cuota_dr": _float_or_none(r.get("TasaOCuotaDR")),
                "importe_dr":      _float_or_none(r.get("ImporteDR")),
            })
    return {"traslados": traslados, "retenciones": retenciones}


def _extraer_doctos_relacionados(pago: ET.Element) -> list[dict]:
    doctos: list[dict] = []
    for docto in pago.findall("./{*}DoctoRelacionado"):
        doctos.append({
            "id_documento":         docto.get("IdDocumento"),
            "serie":                docto.get("Serie"),
            "folio":                docto.get("Folio"),
            "moneda_dr":            docto.get("MonedaDR"),
            "equivalencia_dr":      _float_or_none(docto.get("EquivalenciaDR")),
            "num_parcialidad":      _float_or_none(docto.get("NumParcialidad")),
            "imp_saldo_ant":        _float_or_none(docto.get("ImpSaldoAnt")),
            "imp_pagado":           _float_or_none(docto.get("ImpPagado")),
            "imp_saldo_insoluto":   _float_or_none(docto.get("ImpSaldoInsoluto")),
            "objeto_imp_dr":        docto.get("ObjetoImpDR"),
            "impuestos_dr":         _extraer_impuestos_dr(docto),
        })
    return doctos


def _extraer_impuestos_p(pago: ET.Element) -> dict:
    nodo = pago.find("./{*}ImpuestosP")
    traslados: list[dict] = []
    retenciones: list[dict] = []
    if nodo is not None:
        for t in nodo.findall("./{*}TrasladosP/{*}TrasladoP"):
            traslados.append({
                "base_p":         _float_or_none(t.get("BaseP")),
                "impuesto_p":     t.get("ImpuestoP"),
                "tipo_factor_p":  t.get("TipoFactorP"),
                "tasa_o_cuota_p": _float_or_none(t.get("TasaOCuotaP")),
                "importe_p":      _float_or_none(t.get("ImporteP")),
            })
        for r in nodo.findall("./{*}RetencionesP/{*}RetencionP"):
            retenciones.append({
                "base_p":         _float_or_none(r.get("BaseP")),
                "impuesto_p":     r.get("ImpuestoP"),
                "tipo_factor_p":  r.get("TipoFactorP"),
                "tasa_o_cuota_p": _float_or_none(r.get("TasaOCuotaP")),
                "importe_p":      _float_or_none(r.get("ImporteP")),
            })
    return {"traslados": traslados, "retenciones": retenciones}


def _extraer_pagos(nodo_pagos: ET.Element) -> list[dict]:
    pagos: list[dict] = []
    for pago in nodo_pagos.findall("./{*}Pago"):
        pagos.append({
            "fecha_pago":            pago.get("FechaPago"),
            "forma_de_pago_p":       pago.get("FormaDePagoP"),
            "moneda_p":              pago.get("MonedaP"),
            "tipo_cambio_p":         _float_or_none(pago.get("TipoCambioP")),
            "monto":                 _float_or_none(pago.get("Monto")),
            "num_operacion":         pago.get("NumOperacion"),
            "rfc_emisor_cta_ord":    pago.get("RfcEmisorCtaOrd"),
            "nom_banco_ord_ext":     pago.get("NomBancoOrdExt"),
            "cta_ordenante":         pago.get("CtaOrdenante"),
            "rfc_emisor_cta_ben":    pago.get("RfcEmisorCtaBen"),
            "cta_beneficiario":      pago.get("CtaBeneficiario"),
            "tipo_cad_pago":         pago.get("TipoCadPago"),
            "doctos_relacionados":   _extraer_doctos_relacionados(pago),
            "impuestos_p":           _extraer_impuestos_p(pago),
        })
    return pagos


def parse(root: ET.Element) -> dict | None:
    pagos = root.find(".//{*}Pagos")
    if pagos is None:
        return None

    return {
        "version":  pagos.get("Version"),
        "totales":  _extraer_totales(pagos),
        "pagos":    _extraer_pagos(pagos),
    }
