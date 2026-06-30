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


def _extraer_ubicaciones(cp: ET.Element) -> list[dict]:
    ubicaciones: list[dict] = []
    nodo_ubicaciones = cp.find("./{*}Ubicaciones")
    if nodo_ubicaciones is None:
        return ubicaciones

    for ub in nodo_ubicaciones.findall("./{*}Ubicacion"):
        domicilio = _extraer_domicilio(ub.find("./{*}Domicilio"))
        ubicaciones.append({
            "tipo_ubicacion":                 ub.get("TipoUbicacion"),
            "id_ubicacion":                   ub.get("IDUbicacion"),
            "rfc_remitente_destinatario":     ub.get("RFCRemitenteDestinatario"),
            "nombre_remitente_destinatario":  ub.get("NombreRemitenteDestinatario"),
            "num_reg_id_trib":                ub.get("NumRegIdTrib"),
            "residencia_fiscal":              ub.get("ResidenciaFiscal"),
            "fecha_hora_salida_llegada":      ub.get("FechaHoraSalidaLlegada"),
            "distancia_recorrida":            _float_or_none(ub.get("DistanciaRecorrida")),
            "domicilio":                      domicilio,
        })
    return ubicaciones


def _extraer_documentacion_aduanera(merc: ET.Element) -> list[dict]:
    docs: list[dict] = []
    for doc in merc.findall("./{*}DocumentacionAduanera"):
        docs.append({
            "tipo_documento":      doc.get("TipoDocumento"),
            "num_pedimento":       doc.get("NumPedimento"),
            "ident_doc_aduanero":  doc.get("IdentDocAduanero"),
            "rfc_impo":            doc.get("RFCImpo"),
        })
    return docs


def _extraer_guias_identificacion(merc: ET.Element) -> list[dict]:
    guias: list[dict] = []
    for g in merc.findall("./{*}GuiasIdentificacion"):
        guias.append({
            "numero_guia":   g.get("NumeroGuiaIdentificacion"),
            "descripcion":   g.get("DescripGuiaIdentificacion"),
            "peso":          _float_or_none(g.get("PesoGuiaIdentificacion")),
        })
    return guias


def _extraer_cantidad_transporta(merc: ET.Element) -> list[dict]:
    cantidades: list[dict] = []
    for ct in merc.findall("./{*}CantidadTransporta"):
        cantidades.append({
            "cantidad":         _float_or_none(ct.get("Cantidad")),
            "id_origen":        ct.get("IDOrigen"),
            "id_destino":       ct.get("IDDestino"),
            "cves_transporte":  ct.get("CvesTransporte"),
        })
    return cantidades


def _extraer_detalle_mercancia(merc: ET.Element) -> dict | None:
    dm = merc.find("./{*}DetalleMercancia")
    if dm is None:
        return None
    return {
        "unidad_peso_merc":  dm.get("UnidadPesoMerc"),
        "peso_bruto":        _float_or_none(dm.get("PesoBruto")),
        "peso_neto":         _float_or_none(dm.get("PesoNeto")),
        "peso_tara":         _float_or_none(dm.get("PesoTara")),
        "num_piezas":        _float_or_none(dm.get("NumPiezas")),
    }


def _extraer_regimenes_aduaneros(cp: ET.Element) -> list[str]:
    nodo = cp.find("./{*}RegimenesAduaneros")
    if nodo is None:
        return []
    return [r.get("RegimenAduanero") for r in nodo.findall("./{*}RegimenAduaneroCCP")]


def _extraer_remolques(autotransporte: ET.Element) -> list[dict]:
    remolques: list[dict] = []
    nodo_remolques = autotransporte.find("./{*}Remolques")
    if nodo_remolques is None:
        return remolques

    for r in nodo_remolques.findall("./{*}Remolque"):
        remolques.append({
            "sub_tipo_rem": r.get("SubTipoRem"),
            "placa":        r.get("Placa"),
        })
    return remolques


def _extraer_autotransporte(nodo_mercancias: ET.Element) -> dict | None:
    at = nodo_mercancias.find("./{*}Autotransporte")
    if at is None:
        return None

    iv = at.find("./{*}IdentificacionVehicular")
    identificacion_vehicular = None
    if iv is not None:
        identificacion_vehicular = {
            "config_vehicular":       iv.get("ConfigVehicular"),
            "peso_bruto_vehicular":   _float_or_none(iv.get("PesoBrutoVehicular")),
            "placa_vm":               iv.get("PlacaVM"),
            "anio_modelo_vm":         _float_or_none(iv.get("AnioModeloVM")),
        }

    seg = at.find("./{*}Seguros")
    seguros = None
    if seg is not None:
        seguros = {
            "asegura_resp_civil":     seg.get("AseguraRespCivil"),
            "poliza_resp_civil":      seg.get("PolizaRespCivil"),
            "asegura_med_ambiente":   seg.get("AseguraMedAmbiente"),
            "poliza_med_ambiente":    seg.get("PolizaMedAmbiente"),
            "asegura_carga":          seg.get("AseguraCarga"),
            "poliza_carga":           seg.get("PolizaCarga"),
            "prima_seguro":           _float_or_none(seg.get("PrimaSeguro")),
        }

    return {
        "perm_sct":                  at.get("PermSCT"),
        "num_permiso_sct":           at.get("NumPermisoSCT"),
        "identificacion_vehicular":  identificacion_vehicular,
        "seguros":                   seguros,
        "remolques":                 _extraer_remolques(at),
    }


def _extraer_transporte_maritimo(nodo_mercancias: ET.Element) -> dict | None:
    if nodo_mercancias.find("./{*}TransporteMaritimo") is None:
        return None
    raise NotImplementedError("TransporteMaritimo aun no implementado")


def _extraer_transporte_aereo(nodo_mercancias: ET.Element) -> dict | None:
    if nodo_mercancias.find("./{*}TransporteAereo") is None:
        return None
    raise NotImplementedError("TransporteAereo aun no implementado")


def _extraer_transporte_ferroviario(nodo_mercancias: ET.Element) -> dict | None:
    if nodo_mercancias.find("./{*}TransporteFerroviario") is None:
        return None
    raise NotImplementedError("TransporteFerroviario aun no implementado")


def _extraer_partes_transporte(figura: ET.Element) -> list[str]:
    return [pt.get("ParteTransporte") for pt in figura.findall("./{*}PartesTransporte")]


def _extraer_figura_transporte(cp: ET.Element) -> list[dict]:
    figuras: list[dict] = []
    nodo_figura_transporte = cp.find("./{*}FiguraTransporte")
    if nodo_figura_transporte is None:
        return figuras

    for figura in nodo_figura_transporte.findall("./{*}TiposFigura"):
        domicilio = _extraer_domicilio(figura.find("./{*}Domicilio"))
        figuras.append({
            "tipo_figura":              figura.get("TipoFigura"),
            "rfc_figura":               figura.get("RFCFigura"),
            "num_licencia":             figura.get("NumLicencia"),
            "nombre_figura":            figura.get("NombreFigura"),
            "num_reg_id_trib_figura":   figura.get("NumRegIdTribFigura"),
            "residencia_fiscal_figura": figura.get("ResidenciaFiscalFigura"),
            "partes_transporte":        _extraer_partes_transporte(figura),
            "domicilio":                domicilio,
        })
    return figuras


def _extraer_mercancias(cp: ET.Element) -> dict:
    nodo_mercancias = cp.find("./{*}Mercancias")
    if nodo_mercancias is None:
        return {
            "peso_bruto_total":          None,
            "unidad_peso":               None,
            "peso_neto_total":           None,
            "num_total_mercancias":      None,
            "cargo_por_tasacion":        None,
            "logistica_inversa":         None,
            "mercancias":                [],
            "autotransporte":            None,
            "transporte_maritimo":       None,
            "transporte_aereo":          None,
            "transporte_ferroviario":    None,
        }

    lista_mercancias: list[dict] = []
    for merc in nodo_mercancias.findall("./{*}Mercancia"):
        lista_mercancias.append({
            "bienes_transp":             merc.get("BienesTransp"),
            "clave_stcc":                merc.get("ClaveSTCC"),
            "descripcion":               merc.get("Descripcion"),
            "cantidad":                  _float_or_none(merc.get("Cantidad")),
            "clave_unidad":              merc.get("ClaveUnidad"),
            "unidad":                    merc.get("Unidad"),
            "dimensiones":               merc.get("Dimensiones"),
            "material_peligroso":        merc.get("MaterialPeligroso"),
            "cve_material_peligroso":    merc.get("CveMaterialPeligroso"),
            "embalaje":                  merc.get("Embalaje"),
            "descrip_embalaje":          merc.get("DescripEmbalaje"),
            "sector_cofepris":           merc.get("SectorCOFEPRIS"),
            "peso_en_kg":                _float_or_none(merc.get("PesoEnKg")),
            "valor_mercancia":           _float_or_none(merc.get("ValorMercancia")),
            "moneda":                    merc.get("Moneda"),
            "fraccion_arancelaria":      merc.get("FraccionArancelaria"),
            "uuid_comercio_ext":         merc.get("UUIDComercioExt"),
            "tipo_materia":              merc.get("TipoMateria"),
            "descripcion_materia":       merc.get("DescripcionMateria"),
            "documentacion_aduanera":    _extraer_documentacion_aduanera(merc),
            "guias_identificacion":      _extraer_guias_identificacion(merc),
            "cantidad_transporta":       _extraer_cantidad_transporta(merc),
            "detalle_mercancia":         _extraer_detalle_mercancia(merc),
        })

    return {
        "peso_bruto_total":          _float_or_none(nodo_mercancias.get("PesoBrutoTotal")),
        "unidad_peso":               nodo_mercancias.get("UnidadPeso"),
        "peso_neto_total":           _float_or_none(nodo_mercancias.get("PesoNetoTotal")),
        "num_total_mercancias":      _float_or_none(nodo_mercancias.get("NumTotalMercancias")),
        "cargo_por_tasacion":        _float_or_none(nodo_mercancias.get("CargoPorTasacion")),
        "logistica_inversa":         nodo_mercancias.get("LogisticaInversaRecoleccionDevolucion"),
        "mercancias":                lista_mercancias,
        "autotransporte":            _extraer_autotransporte(nodo_mercancias),
        "transporte_maritimo":       _extraer_transporte_maritimo(nodo_mercancias),
        "transporte_aereo":          _extraer_transporte_aereo(nodo_mercancias),
        "transporte_ferroviario":    _extraer_transporte_ferroviario(nodo_mercancias),
    }


def parse(root: ET.Element) -> dict | None:
    cp = root.find(".//{*}CartaPorte")
    if cp is None:
        return None

    return {
        "version":                  cp.get("Version"),
        "id_ccp":                   cp.get("IdCCP"),
        "transporte_internacional": cp.get("TranspInternac"),
        "pais_origen_destino":      cp.get("PaisOrigenDestino"),
        "via_entrada_salida":       cp.get("ViaEntradaSalida"),
        "entrada_salida_merc":      cp.get("EntradaSalidaMerc"),
        "registro_istmo":           cp.get("RegistroISTMO"),
        "ubicacion_polo_origen":    cp.get("UbicacionPoloOrigen"),
        "ubicacion_polo_destino":   cp.get("UbicacionPoloDestino"),
        "total_dist_recorrida":     _float_or_none(cp.get("TotalDistRec")),
        "regimenes_aduaneros":      _extraer_regimenes_aduaneros(cp),
        "ubicaciones":              _extraer_ubicaciones(cp),
        "mercancias":               _extraer_mercancias(cp),
        "figura_transporte":        _extraer_figura_transporte(cp),
    }
