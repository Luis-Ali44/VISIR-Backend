from __future__ import annotations

import re
import unicodedata

MESES = {
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
}
TERMINOS_PERIODO_RELATIVO = {
    "este mes", "el mes pasado", "esta semana", "este año",
    "el año pasado", "primer semestre", "segundo semestre",
    "primer trimestre", "segundo trimestre", "trimestre",
}
TERMINOS_TIPO = {
    "proveedor", "rfc", "emisor", "iva", "isr", "impuesto",
    "gasto", "gastos", "gasté", "pagué", "compra", "ingreso",
    "ingresos", "cobré", "vendí",
}
REFERENCIAS_SIN_ANTECEDENTE = {"eso", "aquello", "lo anterior", "lo mismo", "esto"}


def _normalizar(texto: str) -> str:
    texto = texto.lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(ch for ch in texto if not unicodedata.combining(ch))


def detectar_periodo(pregunta: str) -> dict:
    texto = _normalizar(pregunta)
    for mes in MESES:
        if mes in texto:
            return {"detectado": True, "tipo": "mes_explicito", "valor": mes}
    for termino in TERMINOS_PERIODO_RELATIVO:
        if termino in texto:
            return {"detectado": True, "tipo": "relativo", "valor": termino}
    match_anio = re.search(r"\b(19|20)\d{2}\b", texto)
    if match_anio:
        return {"detectado": True, "tipo": "anio", "valor": match_anio.group()}
    return {"detectado": False, "tipo": None, "valor": None}


def detectar_tipo_consulta(pregunta: str) -> dict:
    texto = _normalizar(pregunta)
    palabras = set(texto.split())
    encontradas = palabras & TERMINOS_TIPO
    if encontradas:
        return {"detectado": True, "valor": sorted(encontradas)}
    return {"detectado": False, "valor": []}


def routing_certainty(palabras_detectadas: list[str]) -> float:
    n = len(palabras_detectadas)
    if n == 0:
        return 0.3
    if n == 1:
        return 0.55
    return 0.85


def question_clarity(pregunta: str, tiene_contexto_previo: bool = False) -> float:
    texto = _normalizar(pregunta.strip())
    if not tiene_contexto_previo and any(ref in texto for ref in REFERENCIAS_SIN_ANTECEDENTE):
        return 0.3
    if len(texto.split()) <= 3:
        return 0.5
    return 0.9


def data_completeness(fragmentos_encontrados: int, periodo_detectado: bool) -> float:
    if not periodo_detectado:
        return 0.5
    if fragmentos_encontrados == 0:
        return 0.0
    if fragmentos_encontrados < 3:
        return 0.6
    return 1.0


def rag_coverage(fuentes_recuperadas: list[dict]) -> float:
    if not fuentes_recuperadas:
        return 0.0
    similitudes = [f.get("similarity", 0.0) for f in fuentes_recuperadas]
    return sum(similitudes) / len(similitudes)

