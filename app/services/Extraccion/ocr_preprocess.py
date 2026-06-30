from __future__ import annotations

from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image

EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

_DPI_TICKET    = 200
_DPI_NATIVO    = 300
_DPI_ESCANEADO = 250

SCORE_MINIMO        = 0.35
SCORE_MINIMO_NATIVO = 0.25


def es_pdf_nativo(pagina: fitz.Page) -> bool:
    return len(pagina.get_text().strip()) > 50


def clasificar_pagina(pagina: fitz.Page) -> str:
    ancho_pt = pagina.rect.width
    if ancho_pt < 300:
        return "ticket"
    if es_pdf_nativo(pagina):
        return "nativo"
    return "escaneado"


def dpi_para_tipo(tipo: str) -> int:
    return {
        "ticket":   _DPI_TICKET,
        "nativo":   _DPI_NATIVO,
        "escaneado": _DPI_ESCANEADO,
    }[tipo]


def renderizar_pagina(pagina: fitz.Page, dpi: int) -> np.ndarray:
    escala = dpi / 72.0
    mat    = fitz.Matrix(escala, escala)
    pix    = pagina.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    return np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)


def imagen_a_array(ruta: Path) -> np.ndarray:
    return np.array(Image.open(ruta).convert("RGB"))


def _preprocesar_ticket(img: np.ndarray) -> np.ndarray:
    gray  = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray  = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    gray  = clahe.apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)


def _preprocesar_nativo(img: np.ndarray) -> np.ndarray:
    gray  = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY) if img.ndim == 3 else img
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    gray  = clahe.apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)


def _preprocesar_escaneado(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    std  = float(np.std(gray))
    clip = 1.5 if std > 40 else 3.0
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
    gray  = clahe.apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)


def preprocesar(img: np.ndarray, tipo: str) -> np.ndarray:
    if tipo == "ticket":
        return _preprocesar_ticket(img)
    if tipo == "nativo":
        return _preprocesar_nativo(img)
    return _preprocesar_escaneado(img)


def agrupar_en_lineas(
    items: list[tuple],
    tolerancia_y: float = 8.0,
) -> list[list[tuple]]:
    if not items:
        return []

    ordenados    = sorted(items, key=lambda x: x[2])
    lineas       = []
    linea_actual = [ordenados[0]]
    y_ref        = ordenados[0][2]

    for item in ordenados[1:]:
        if abs(item[2] - y_ref) <= tolerancia_y:
            linea_actual.append(item)
        else:
            linea_actual.sort(key=lambda x: x[3])
            lineas.append(linea_actual)
            linea_actual = [item]
            y_ref        = item[2]

    if linea_actual:
        linea_actual.sort(key=lambda x: x[3])
        lineas.append(linea_actual)

    return lineas


def items_a_texto(lineas: list[list[tuple]]) -> list[str]:
    return [" ".join(item[0] for item in linea) for linea in lineas]


def extraer_paginas_pdf(ruta: Path) -> list[tuple[np.ndarray, str, int, int, int]]:
    doc     = fitz.open(str(ruta))
    paginas = []

    for num, pagina in enumerate(doc):
        tipo = clasificar_pagina(pagina)
        dpi  = dpi_para_tipo(tipo)
        raw  = renderizar_pagina(pagina, dpi)
        proc = preprocesar(raw, tipo)
        paginas.append((proc, tipo, dpi, num + 1, len(doc)))

    doc.close()
    return paginas


def extraer_imagen_suelta(ruta: Path) -> list[tuple[np.ndarray, str, int, int, int]]:
    raw  = imagen_a_array(ruta)
    tipo = "ticket" if (raw.shape[1] < 600) else "escaneado"
    proc = preprocesar(raw, tipo)
    return [(proc, tipo, 0, 1, 1)]
