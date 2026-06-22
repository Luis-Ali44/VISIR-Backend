from __future__ import annotations

from typing import Any

import numpy as np

from .ocr_preprocess import agrupar_en_lineas

_paddle_ocr_instance: Any = None


def _get_paddle_ocr() -> Any:
    global _paddle_ocr_instance
    if _paddle_ocr_instance is None:
        import paddle
        from paddleocr import PaddleOCR

        if paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0:
            paddle.device.set_device("gpu:0")
            device = "gpu"
        else:
            paddle.device.set_device("cpu")
            device = "cpu"

        _paddle_ocr_instance = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            lang="es",
            device=device,
        )
    return _paddle_ocr_instance


def _centroide_bbox(poly: Any) -> tuple[float, float]:
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
    ocr: Any,
    img_array: np.ndarray, 
    score_minimo: float = SCORE_MINIMO,
) -> list[str]:
    try:
        resultado = list(ocr.predict(img_array))
    except Exception:
        return []

    items: list[tuple[str, float, float, float]] = []
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