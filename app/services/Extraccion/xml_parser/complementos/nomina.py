from __future__ import annotations

import xml.etree.ElementTree as ET


def _float_or_none(valor: str | None) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def _extraer_emisor(nomina: ET.Element) -> dict | None:
    emisor = nomina.find("./{*}Emisor")
    if emisor is None:
        return None
    entidad_snc = emisor.find("./{*}EntidadSNCF")
    return {
        "curp":                emisor.get("Curp"),
        "registro_patronal":   emisor.get("RegistroPatronal"),
        "rfc_patron_origen":   emisor.get("RfcPatronOrigen"),
        "entidad_sncf":        ({
            "origen_recurso":       entidad_snc.get("OrigenRecurso"),
            "monto_recurso_propio": _float_or_none(entidad_snc.get("MontoRecursoPropio")),
        } if entidad_snc is not None else None),
    }


def _extraer_subcontratacion(receptor: ET.Element) -> list[dict]:
    subcontrataciones: list[dict] = []
    for s in receptor.findall("./{*}SubContratacion"):
        subcontrataciones.append({
            "rfc_labora":        s.get("RfcLabora"),
            "porcentaje_tiempo": _float_or_none(s.get("PorcentajeTiempo")),
        })
    return subcontrataciones


def _extraer_receptor(nomina: ET.Element) -> dict | None:
    receptor = nomina.find("./{*}Receptor")
    if receptor is None:
        return None
    return {
        "curp":                       receptor.get("Curp"),
        "tipo_contrato":              receptor.get("TipoContrato"),
        "tipo_regimen":               receptor.get("TipoRegimen"),
        "num_empleado":               receptor.get("NumEmpleado"),
        "departamento":               receptor.get("Departamento"),
        "puesto":                     receptor.get("Puesto"),
        "tipo_jornada":               receptor.get("TipoJornada"),
        "periodicidad_pago":          receptor.get("PeriodicidadPago"),
        "banco":                      receptor.get("Banco"),
        "cuenta_bancaria":            receptor.get("CuentaBancaria"),
        "salario_base_cot_apor":      _float_or_none(receptor.get("SalarioBaseCotApor")),
        "salario_diario_integrado":   _float_or_none(receptor.get("SalarioDiarioIntegrado")),
        "clave_ent_fed":              receptor.get("ClaveEntFed"),
        "num_seguridad_social":       receptor.get("NumSeguridadSocial"),
        "fecha_inicio_rel_laboral":   receptor.get("FechaInicioRelLaboral"),
        "antiguedad":                 receptor.get("Antig\u00fcedad"),
        "riesgo_puesto":              receptor.get("RiesgoPuesto"),
        "sindicalizado":              receptor.get("Sindicalizado"),
        "sub_contratacion":           _extraer_subcontratacion(receptor),
    }


def _extraer_horas_extra(percepcion: ET.Element) -> list[dict]:
    horas: list[dict] = []
    for h in percepcion.findall("./{*}HorasExtra"):
        horas.append({
            "dias":           _float_or_none(h.get("Dias")),
            "tipo_horas":     h.get("TipoHoras"),
            "horas_extra":    _float_or_none(h.get("HorasExtra")),
            "importe_pagado": _float_or_none(h.get("ImportePagado")),
        })
    return horas


def _extraer_jubilacion_pension_retiro(percepcion: ET.Element) -> dict | None:
    nodo = percepcion.find("./{*}JubilacionPensionRetiro")
    if nodo is None:
        return None
    return {
        "total_una_exhibicion":      _float_or_none(nodo.get("TotalUnaExhibicion")),
        "total_parcialidad":         _float_or_none(nodo.get("TotalParcialidad")),
        "monto_diario":              _float_or_none(nodo.get("MontoDiario")),
        "ingreso_acumulable":        _float_or_none(nodo.get("IngresoAcumulable")),
        "ingreso_no_acumulable":     _float_or_none(nodo.get("IngresoNoAcumulable")),
    }


def _extraer_separacion_indemnizacion(percepcion: ET.Element) -> dict | None:
    nodo = percepcion.find("./{*}SeparacionIndemnizacion")
    if nodo is None:
        return None
    return {
        "total_pagado":           _float_or_none(nodo.get("TotalPagado")),
        "num_anios_servicio":     _float_or_none(nodo.get("NumA\u00f1osServicio")),
        "ultimo_sueldo_mens_ord": _float_or_none(nodo.get("UltimoSueldoMensOrd")),
        "ingreso_acumulable":     _float_or_none(nodo.get("IngresoAcumulable")),
        "ingreso_no_acumulable":  _float_or_none(nodo.get("IngresoNoAcumulable")),
    }


def _extraer_percepciones(nomina: ET.Element) -> dict:
    nodo = nomina.find("./{*}Percepciones")
    if nodo is None:
        return {
            "total_sueldos":             None,
            "total_separacion_indemniz": None,
            "total_jubilacion_pen_ret":  None,
            "total_gravado":             None,
            "total_exento":              None,
            "percepciones":              [],
        }

    lista_percepciones: list[dict] = []
    for p in nodo.findall("./{*}Percepcion"):
        lista_percepciones.append({
            "tipo_percepcion":           p.get("TipoPercepcion"),
            "clave":                     p.get("Clave"),
            "concepto":                  p.get("Concepto"),
            "importe_gravado":           _float_or_none(p.get("ImporteGravado")),
            "importe_exento":            _float_or_none(p.get("ImporteExento")),
            "horas_extra":               _extraer_horas_extra(p),
            "jubilacion_pension_retiro": _extraer_jubilacion_pension_retiro(p),
            "separacion_indemnizacion":  _extraer_separacion_indemnizacion(p),
        })

    return {
        "total_sueldos":             _float_or_none(nodo.get("TotalSueldos")),
        "total_separacion_indemniz": _float_or_none(nodo.get("TotalSeparacionIndemnizacion")),
        "total_jubilacion_pen_ret":  _float_or_none(nodo.get("TotalJubilacionPensionRetiro")),
        "total_gravado":             _float_or_none(nodo.get("TotalGravado")),
        "total_exento":              _float_or_none(nodo.get("TotalExento")),
        "percepciones":              lista_percepciones,
    }


def _extraer_deducciones(nomina: ET.Element) -> dict:
    nodo = nomina.find("./{*}Deducciones")
    if nodo is None:
        return {
            "total_otras_deducciones":   None,
            "total_impuestos_retenidos": None,
            "deducciones":               [],
        }

    lista_deducciones: list[dict] = []
    for d in nodo.findall("./{*}Deduccion"):
        lista_deducciones.append({
            "tipo_deduccion": d.get("TipoDeduccion"),
            "clave":          d.get("Clave"),
            "concepto":       d.get("Concepto"),
            "importe":        _float_or_none(d.get("Importe")),
        })

    return {
        "total_otras_deducciones":   _float_or_none(nodo.get("TotalOtrasDeducciones")),
        "total_impuestos_retenidos": _float_or_none(nodo.get("TotalImpuestosRetenidos")),
        "deducciones":               lista_deducciones,
    }


def _extraer_subsidio_al_empleo(otro_pago: ET.Element) -> dict | None:
    nodo = otro_pago.find("./{*}SubsidioAlEmpleo")
    if nodo is None:
        return None
    return {"subsidio_causado": _float_or_none(nodo.get("SubsidioCausado"))}


def _extraer_compensacion_saldos_a_favor(otro_pago: ET.Element) -> dict | None:
    nodo = otro_pago.find("./{*}CompensacionSaldosAFavor")
    if nodo is None:
        return None
    return {
        "saldo_a_favor":     _float_or_none(nodo.get("SaldoAFavor")),
        "anio":              nodo.get("A\u00f1o"),
        "remanente_sal_fav": _float_or_none(nodo.get("RemanenteSalFav")),
    }


def _extraer_otros_pagos(nomina: ET.Element) -> list[dict]:
    nodo = nomina.find("./{*}OtrosPagos")
    if nodo is None:
        return []

    otros_pagos: list[dict] = []
    for op in nodo.findall("./{*}OtroPago"):
        otros_pagos.append({
            "tipo_otro_pago":              op.get("TipoOtroPago"),
            "clave":                       op.get("Clave"),
            "concepto":                    op.get("Concepto"),
            "importe":                     _float_or_none(op.get("Importe")),
            "subsidio_al_empleo":          _extraer_subsidio_al_empleo(op),
            "compensacion_saldos_a_favor": _extraer_compensacion_saldos_a_favor(op),
        })
    return otros_pagos


def _extraer_incapacidades(nomina: ET.Element) -> list[dict]:
    nodo = nomina.find("./{*}Incapacidades")
    if nodo is None:
        return []

    incapacidades: list[dict] = []
    for inc in nodo.findall("./{*}Incapacidad"):
        incapacidades.append({
            "dias_incapacidad":  _float_or_none(inc.get("DiasIncapacidad")),
            "tipo_incapacidad":  inc.get("TipoIncapacidad"),
            "importe_monetario": _float_or_none(inc.get("ImporteMonetario")),
        })
    return incapacidades


def parse(root: ET.Element) -> dict | None:
    nomina = root.find(".//{*}Nomina")
    if nomina is None:
        return None

    return {
        "version":            nomina.get("Version"),
        "tipo_nomina":        nomina.get("TipoNomina"),
        "fecha_pago":         nomina.get("FechaPago"),
        "fecha_inicial_pago": nomina.get("FechaInicialPago"),
        "fecha_final_pago":   nomina.get("FechaFinalPago"),
        "num_dias_pagados":   _float_or_none(nomina.get("NumDiasPagados")),
        "total_percepciones": _float_or_none(nomina.get("TotalPercepciones")),
        "total_deducciones":  _float_or_none(nomina.get("TotalDeducciones")),
        "total_otros_pagos":  _float_or_none(nomina.get("TotalOtrosPagos")),
        "emisor":             _extraer_emisor(nomina),
        "receptor":           _extraer_receptor(nomina),
        "percepciones":       _extraer_percepciones(nomina),
        "deducciones":        _extraer_deducciones(nomina),
        "otros_pagos":        _extraer_otros_pagos(nomina),
        "incapacidades":      _extraer_incapacidades(nomina),
    }
