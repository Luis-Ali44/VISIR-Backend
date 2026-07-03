from __future__ import annotations

import re
import unicodedata
from typing import Literal

RutaEnrutamiento = Literal["NORMATIVA", "CFDI_PROPIOS", "HIBRIDO"]

PALABRAS_NORMATIVA: set[str] = {
    "regimen",
    "obligacion",
    "impuesto",
    "deduccion",
    "ley",
    "sat",
    "articulo",
    "norma",
    "addenda",
}
PALABRAS_NUMERICA: set[str] = {
    "gasto",
    "total",
    "mes",
    "cuanto",
    "ingreso",
    "reporte",
    "factura",
    "proveedor",
}


def _normalizar_token(token: str) -> str:
    token = token.lower().strip()
    token = unicodedata.normalize("NFKD", token)
    token = "".join(ch for ch in token if not unicodedata.combining(ch))
    token = re.sub(r"^[^\w]+|[^\w]+$", "", token)
    if len(token) > 5 and token.endswith("es"):
        token = token[:-2]
    elif len(token) > 4 and token.endswith("s"):
        token = token[:-1]
    return token


def analizar_lexico(pregunta: str) -> dict[str, object]:
    palabras_usuario = {_normalizar_token(token) for token in pregunta.split()}
    palabras_usuario.discard("")
    match_normativa = len(palabras_usuario & PALABRAS_NORMATIVA)
    match_numerica = len(palabras_usuario & PALABRAS_NUMERICA)
    detectadas = list(palabras_usuario & (PALABRAS_NORMATIVA | PALABRAS_NUMERICA))

    if match_normativa > 0 and match_numerica > 0:
        return {"ruta_seleccionada": "HIBRIDO", "confianza_lexica": 0.85, "palabras_clave_detectadas": detectadas}
    if match_numerica > match_normativa:
        return {"ruta_seleccionada": "CFDI_PROPIOS", "confianza_lexica": 0.90, "palabras_clave_detectadas": detectadas}
    if match_normativa > 0:
        return {"ruta_seleccionada": "NORMATIVA", "confianza_lexica": 0.90, "palabras_clave_detectadas": detectadas}

    return {"ruta_seleccionada": "NORMATIVA", "confianza_lexica": 0.0, "palabras_clave_detectadas": detectadas}