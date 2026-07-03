from __future__ import annotations

import xml.etree.ElementTree as ET


def _extraer_leyendas(lf: ET.Element) -> list[dict]:
    leyendas: list[dict] = []
    for leyenda in lf.findall("./{*}Leyenda"):
        leyendas.append({
            "disposicion_fiscal": leyenda.get("disposicionFiscal"),
            "norma":              leyenda.get("norma"),
            "texto_leyenda":      leyenda.get("textoLeyenda"),
        })
    return leyendas


def parse(root: ET.Element) -> dict | None:
    lf = root.find(".//{*}LeyendasFiscales")
    if lf is None:
        return None

    return {
        "version":   lf.get("version"),
        "leyendas":  _extraer_leyendas(lf),
    }
