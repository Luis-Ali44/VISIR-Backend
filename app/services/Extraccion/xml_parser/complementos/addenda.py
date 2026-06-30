from __future__ import annotations

import xml.etree.ElementTree as ET


def _tag_local(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _elemento_a_dict(elem: ET.Element) -> dict:

    resultado: dict = {}
    if elem.attrib:
        resultado["atributos"] = dict(elem.attrib)
    texto = (elem.text or "").strip()
    if texto:
        resultado["texto"] = texto

    hijos: dict = {}
    for hijo in list(elem):
        nombre = _tag_local(hijo.tag)
        valor = _elemento_a_dict(hijo)
        if nombre in hijos:
            if not isinstance(hijos[nombre], list):
                hijos[nombre] = [hijos[nombre]]
            hijos[nombre].append(valor)
        else:
            hijos[nombre] = valor
    if hijos:
        resultado["hijos"] = hijos

    return resultado


def parse(root: ET.Element) -> dict | None:
    addenda = root.find("./{*}Addenda")
    if addenda is None:
        return None

    contenido = [_elemento_a_dict(hijo) for hijo in list(addenda)]
    return {
        "presente":   True,
        "contenido":  contenido,
    }
