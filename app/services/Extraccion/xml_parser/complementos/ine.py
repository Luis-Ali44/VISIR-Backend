from __future__ import annotations

import xml.etree.ElementTree as ET


def _float_or_none(valor: str | None) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (ValueError, TypeError):
        return None


def _extraer_contabilidades(entidad: ET.Element) -> list[dict]:
    contabilidades: list[dict] = []
    for c in entidad.findall("./{*}Contabilidad"):
        contabilidades.append({"id_contabilidad": c.get("IdContabilidad")})
    return contabilidades


def _extraer_entidad(ine: ET.Element) -> dict | None:
    entidad = ine.find("./{*}Entidad")
    if entidad is None:
        return None
    return {
        "clave_entidad":   entidad.get("ClaveEntidad"),
        "ambito":          entidad.get("Ambito"),
        "contabilidades":  _extraer_contabilidades(entidad),
    }


def parse(root: ET.Element) -> dict | None:
    ine = root.find(".//{*}INE")
    if ine is None:
        return None

    return {
        "version":      ine.get("Version"),
        "tipo_proceso": ine.get("TipoProceso"),
        "tipo_comite":  ine.get("TipoComite"),
        "entidad":      _extraer_entidad(ine),
    }
