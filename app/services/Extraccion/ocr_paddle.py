from __future__ import annotations

import os

import numpy as np
from .ocr_preprocess import agrupar_en_lineas

_paddle_ocr_instance = None


def _get_paddle_ocr():
    global _paddle_ocr_instance
    if _paddle_ocr_instance is None:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["FLAGS_USE_CUDA"] = "0"
        path_original = os.environ.get("PATH", "")
        partes_limpias = [
            p for p in path_original.split(os.pathsep)
            if "torch" not in p.lower() and "cuda" not in p.lower()
        ]
        os.environ["PATH"] = os.pathsep.join(partes_limpias)
        import paddle
        paddle.device.set_device("cpu")
        from paddleocr import PaddleOCR
        _paddle_ocr_instance = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            lang="es",
        )
        os.environ["PATH"] = path_original
    return _paddle_ocr_instance


def _centroide_bbox(poly) -> tuple[float, float]:
    try:
        poly_arr = np.array(poly, dtype=float)
        cx = float(poly_arr[:, 0].mean())
        cy = float(poly_arr[:, 1].mean())
        return cx, cy
    except (TypeError, ValueError, IndexError):
        try:
            return float(poly[0][0]), float(poly[0][1])
        except (TypeError, ValueError, IndexError):
            return 0.0, 0.0


SCORE_MINIMO        = 0.35
SCORE_MINIMO_NATIVO = 0.25


def _ocr_desde_array(
    ocr,
    img_array: np.ndarray,
    score_minimo: float = SCORE_MINIMO,
) -> list[str]:
    try:
        resultado = list(ocr.predict(img_array))
    except Exception:
        return []

    items: list[tuple] = []
    for res in resultado:
        if res is None:
            continue
        rec_texts  = res.get("rec_texts",  []) or []
        rec_scores = res.get("rec_scores", []) or []
        rec_polys  = res.get("rec_polys",  []) or []
        for texto, score, poly in zip(rec_texts, rec_scores, rec_polys, strict=False):
            if score < score_minimo:
                continue
            texto_str = str(texto).strip()
            if not texto_str:
                continue
            cx, cy = _centroide_bbox(poly)
            items.append((texto_str, score, cy, cx))

    lineas_agrupadas = agrupar_en_lineas(items)
    return [" ".join(item[0] for item in linea) for linea in lineas_agrupadas]
