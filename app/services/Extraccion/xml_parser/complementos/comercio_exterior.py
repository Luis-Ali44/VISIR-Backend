from __future__ import annotations

import xml.etree.ElementTree as ET


def _float_or_none(valor: str | None) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def _extraer_domicilio(dom: ET.Element | None) -> dict | None:
    if dom is None:
        return None
    return {
        "calle":            dom.get("Calle"),
        "numero_exterior":  dom.get("NumeroExterior"),
        "numero_interior":  dom.get("NumeroInterior"),
        "colonia":          dom.get("Colonia"),
        "localidad":        dom.get("Localidad"),
        "municipio":        dom.get("Municipio"),
        "estado":           dom.get("Estado"),
        "pais":             dom.get("Pais"),
        "codigo_postal":    dom.get("CodigoPostal"),
        "referencia":       dom.get("Referencia"),
    }


def _extraer_emisor(ce: ET.Element) -> dict | None:
    emisor = ce.find("./{*}Emisor")
    if emisor is None:
        return None
    return {
        "curp":       emisor.get("Curp"),
        "domicilio":  _extraer_domicilio(emisor.find("./{*}Domicilio")),
    }


def _extraer_propietarios(ce: ET.Element) -> list[dict]:
    propietarios: list[dict] = []
    for p in ce.findall("./{*}Propietario"):
        propietarios.append({
            "num_reg_id_trib":   p.get("NumRegIdTrib"),
            "residencia_fiscal": p.get("ResidenciaFiscal"),
        })
    return propietarios


def _extraer_receptor(ce: ET.Element) -> dict | None:
    receptor = ce.find("./{*}Receptor")
    if receptor is None:
        return None
    return {
        "num_reg_id_trib":  receptor.get("NumRegIdTrib"),
        "domicilio":        _extraer_domicilio(receptor.find("./{*}Domicilio")),
    }


def _extraer_destinatarios(ce: ET.Element) -> list[dict]:
    destinatarios: list[dict] = []
    for d in ce.findall("./{*}Destinatario"):
        domicilios = [_extraer_domicilio(dom) for dom in d.findall("./{*}Domicilio")]
        destinatarios.append({
            "num_reg_id_trib":  d.get("NumRegIdTrib"),
            "nombre":           d.get("Nombre"),
            "domicilios":       domicilios,
        })
    return destinatarios


def _extraer_descripciones_especificas(merc: ET.Element) -> list[dict]:
    descripciones: list[dict] = []
    for de in merc.findall("./{*}DescripcionesEspecificas"):
        descripciones.append({
            "marca":        de.get("Marca"),
            "modelo":       de.get("Modelo"),
            "sub_modelo":   de.get("SubModelo"),
            "numero_serie": de.get("NumeroSerie"),
        })
    return descripciones


def _extraer_mercancias(ce: ET.Element) -> list[dict]:
    mercancias: list[dict] = []
    nodo_mercancias = ce.find("./{*}Mercancias")
    if nodo_mercancias is None:
        return mercancias

    for merc in nodo_mercancias.findall("./{*}Mercancia"):
        mercancias.append({
            "no_identificacion":         merc.get("NoIdentificacion"),
            "fraccion_arancelaria":      merc.get("FraccionArancelaria"),
            "cantidad_aduana":           _float_or_none(merc.get("CantidadAduana")),
            "unidad_aduana":             merc.get("UnidadAduana"),
            "valor_unitario_aduana":     _float_or_none(merc.get("ValorUnitarioAduana")),
            "valor_dolares":             _float_or_none(merc.get("ValorDolares")),
            "descripciones_especificas": _extraer_descripciones_especificas(merc),
        })
    return mercancias


def parse(root: ET.Element) -> dict | None:
    ce = root.find(".//{*}ComercioExterior")
    if ce is None:
        return None

    return {
        "version":                      ce.get("Version"),
        "motivo_traslado":              ce.get("MotivoTraslado"),
        "clave_de_pedimento":           ce.get("ClaveDePedimento"),
        "certificado_origen":           ce.get("CertificadoOrigen"),
        "num_certificado_origen":       ce.get("NumCertificadoOrigen"),
        "numero_exportador_confiable":  ce.get("NumeroExportadorConfiable"),
        "incoterm":                     ce.get("Incoterm"),
        "observaciones":                ce.get("Observaciones"),
        "tipo_cambio_usd":              _float_or_none(ce.get("TipoCambioUSD")),
        "total_usd":                    _float_or_none(ce.get("TotalUSD")),
        "emisor":                       _extraer_emisor(ce),
        "propietarios":                 _extraer_propietarios(ce),
        "receptor":                     _extraer_receptor(ce),
        "destinatarios":                _extraer_destinatarios(ce),
        "mercancias":                   _extraer_mercancias(ce),
    }
