from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

_MODELO_ES_LOCAL = False
_MODELO_RUTA = "intfloat/multilingual-e5-small"

_USAR_PREFIJOS_E5 = True
_PREFIJO_PASSAGE = "passage: "
_PREFIJO_QUERY = "query: "

UMBRAL_CONFIANZA = 0.80

_CATALOGO_PATH = Path(__file__).parent.parent.parent.parent / "data" / "catalogo_prodserv_sat.json"
_CODIGOS_PATH = (
    Path(__file__).parent.parent.parent.parent / "models" / "embeddings" / "catalogo_codigos.json"
)
_EMBEDDINGS_CACHE_PATH = (
    Path(__file__).parent.parent.parent.parent / "models" / "embeddings" / "catalogo_embeddings.npy"
)
_CODIGO_PLACEHOLDER = "01010101"


@dataclass(frozen=True)
class SugerenciaCategoria:
    clave_prod_serv: str | None
    descripcion_catalogo: str | None
    confianza: float
    top_k: list[tuple[str, str, float]]
    categorizado: bool


@lru_cache(maxsize=1)
def _cargar_modelo() -> Any:
    from sentence_transformers import SentenceTransformer

    origen = str(_MODELO_RUTA) if _MODELO_ES_LOCAL else _MODELO_RUTA
    return SentenceTransformer(origen)


def _con_prefijo(texto: str, prefijo: str) -> str:
    return (prefijo + texto) if _USAR_PREFIJOS_E5 else texto


@lru_cache(maxsize=1)
def _cargar_catalogo() -> dict[str, dict]:
    with _CATALOGO_PATH.open(encoding="utf-8") as f:
        return dict(json.load(f))


def _construir_contexto(info: dict) -> str:
    partes = [info["descripcion"]]

    grupo_o_respaldo = info.get("grupo") or info.get("clase")
    if grupo_o_respaldo:
        partes.append(grupo_o_respaldo)

    if info.get("division"):
        partes.append(info["division"])

    return " | ".join(partes)


@lru_cache(maxsize=1)
def _cargar_codigos_validos() -> list[str]:
    with _CODIGOS_PATH.open(encoding="utf-8") as f:
        return list(json.load(f))


@lru_cache(maxsize=1)
def _cargar_o_construir_embeddings_catalogo() -> tuple[list[str], np.ndarray]:
    if _EMBEDDINGS_CACHE_PATH.exists() and _CODIGOS_PATH.exists():
        claves = _cargar_codigos_validos()
        vectores = np.load(_EMBEDDINGS_CACHE_PATH)
        if vectores.shape[0] != len(claves):
            raise ValueError(
                f"Desfase entre codigos_validos ({len(claves)}) y embeddings "
                f"cacheados ({vectores.shape[0]}) — regenera el cache."
            )
        return claves, vectores

    catalogo = _cargar_catalogo()
    claves = [c for c in catalogo if c != _CODIGO_PLACEHOLDER]
    textos = [_con_prefijo(_construir_contexto(catalogo[c]), _PREFIJO_PASSAGE) for c in claves]

    modelo = _cargar_modelo()
    vectores = modelo.encode(
        textos,
        batch_size=128,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    _EMBEDDINGS_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(_EMBEDDINGS_CACHE_PATH, vectores)
    with _CODIGOS_PATH.open("w", encoding="utf-8") as f:
        json.dump(claves, f, ensure_ascii=False)

    return claves, vectores


def categorizar_concepto(
    descripcion: str,
    k: int = 5,
    umbral: float = UMBRAL_CONFIANZA,
) -> SugerenciaCategoria:
    if not descripcion or not descripcion.strip():
        return SugerenciaCategoria(None, None, 0.0, [], categorizado=False)

    modelo = _cargar_modelo()
    catalogo = _cargar_catalogo()
    claves, vectores = _cargar_o_construir_embeddings_catalogo()

    consulta_texto = _con_prefijo(descripcion, _PREFIJO_QUERY)
    consulta = modelo.encode([consulta_texto], normalize_embeddings=True, convert_to_numpy=True)[0]
    scores = vectores @ consulta

    top_idx = np.argsort(-scores)[:k]
    top_k = [(claves[i], catalogo[claves[i]]["descripcion"], float(scores[i])) for i in top_idx]

    mejor_clave, mejor_desc, mejor_score = top_k[0]
    categorizado = mejor_score >= umbral

    return SugerenciaCategoria(
        clave_prod_serv=mejor_clave if categorizado else None,
        descripcion_catalogo=mejor_desc if categorizado else None,
        confianza=mejor_score,
        top_k=top_k,
        categorizado=categorizado,
    )
