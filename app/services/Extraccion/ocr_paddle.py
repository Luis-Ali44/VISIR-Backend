from __future__ import annotations

import os
import time
from pathlib import Path

import cv2
import fitz
import numpy as np
from PIL import Image

EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}

_paddle_ocr_instance = None


def _get_paddle_ocr():
    global _paddle_ocr_instance
    if _paddle_ocr_instance is None:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["FLAGS_use_cuda"] = "0"  # noqa: SIM112
        path_original = os.environ.get("PATH", "")
        partes_limpias = [
            p
            for p in path_original.split(os.pathsep)
            if "torch" not in p.lower() and "cuda" not in p.lower()
        ]
        os.environ["PATH"] = os.pathsep.join(partes_limpias)
        import paddle

        paddle.device.set_device("cpu")
        from paddleocr import PaddleOCR

        print("Cargando PaddleOCR...")
        _paddle_ocr_instance = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            lang="es",
        )
        os.environ["PATH"] = path_original
        print("PaddleOCR listo.")
    return _paddle_ocr_instance


def _es_ticket(img_array: np.ndarray) -> bool:
    h, w = img_array.shape[:2]
    ratio = h / w
    es = ratio > 2.5 or w < 800
    if es:
        print(
            f"    [Ticket detectado] alto={h}px ancho={w}px ratio={ratio:.2f} "
            f"({'ratio>2.5' if ratio > 2.5 else 'ancho<800'})"
        )
    else:
        print(f"    [Factura normal] alto={h}px ancho={w}px ratio={ratio:.2f}")
    return es


def _preprocesar_factura_escaneada(img_array: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    std = float(np.std(gray))
    clip = 1.5 if std > 40 else 3.0
    print(f"    [Preprocesamiento escaneado] std={std:.1f} clipLimit={clip}")
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)


def _preprocesar_ticket(img_array: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    gray = clahe.apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)


def _preprocesar_nativo(img_array: np.ndarray) -> np.ndarray:
    gray = img_array if len(img_array.shape) == 2 else cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)


def _preprocesar_imagen(img_array: np.ndarray, nativo: bool = False) -> np.ndarray:
    if _es_ticket(img_array):
        return _preprocesar_ticket(img_array)
    if nativo:
        return _preprocesar_nativo(img_array)
    return _preprocesar_factura_escaneada(img_array)


def _centroide_bbox(poly) -> tuple[float, float]:
    try:
        poly_arr = np.array(poly, dtype=float)
        cx = float(poly_arr[:, 0].mean())
        cy = float(poly_arr[:, 1].mean())
        return cx, cy
    except Exception:
        try:
            return float(poly[0][0]), float(poly[0][1])
        except Exception:
            return 0.0, 0.0


def _agrupar_en_lineas(
    items: list[tuple],
    tolerancia_y: float = 8.0,
) -> list[list[tuple]]:
    if not items:
        return []
    ordenados = sorted(items, key=lambda x: x[2])
    lineas = []
    linea_actual = [ordenados[0]]
    y_ref = ordenados[0][2]
    for item in ordenados[1:]:
        if abs(item[2] - y_ref) <= tolerancia_y:
            linea_actual.append(item)
        else:
            linea_actual.sort(key=lambda x: x[3])
            lineas.append(linea_actual)
            linea_actual = [item]
            y_ref = item[2]
    if linea_actual:
        linea_actual.sort(key=lambda x: x[3])
        lineas.append(linea_actual)
    return lineas


_SCORE_MINIMO = 0.35
_SCORE_MINIMO_NATIVO = 0.25

SCORE_MINIMO = _SCORE_MINIMO
SCORE_MINIMO_NATIVO = _SCORE_MINIMO_NATIVO


def _ocr_desde_array(
    ocr,
    img_array: np.ndarray,
    score_minimo: float = _SCORE_MINIMO,
) -> list[str]:
    try:
        resultado = list(ocr.predict(img_array))
        items: list[tuple] = []
        for res in resultado:
            if res is None:
                continue
            rec_texts = res.get("rec_texts", []) or []
            rec_scores = res.get("rec_scores", []) or []
            rec_polys = res.get("rec_polys", []) or []

            for texto, score, poly in zip(  # noqa: B905
                rec_texts,
                rec_scores,
                rec_polys,
            ):
                if score < score_minimo:
                    continue
                texto_str = str(texto).strip()
                if not texto_str:
                    continue
                cx, cy = _centroide_bbox(poly)
                items.append((texto_str, score, cy, cx))
        lineas_agrupadas = _agrupar_en_lineas(items)
        return [" ".join(item[0] for item in linea) for linea in lineas_agrupadas]
    except Exception as e:
        print(f"    Error interno OCR: {e}")
        return []


_DPI_ESCANEADO = 250
_DPI_NATIVO = 300
_DPI_TICKET = 200


def _es_pdf_nativo(pagina: fitz.Page) -> bool:
    texto = pagina.get_text()
    return len(texto.strip()) > 50


def extraer_texto_paddle(ruta_archivo: str) -> str:
    inicio = time.time()
    ruta = Path(ruta_archivo)
    ocr = _get_paddle_ocr()
    paginas_texto: list[str] = []

    if ruta.suffix.lower() == ".pdf":
        doc = fitz.open(str(ruta))
        for num, pagina in enumerate(doc):
            ancho_pt = pagina.rect.width
            es_ticket = ancho_pt < 300
            nativo = False
            if not es_ticket:
                nativo = _es_pdf_nativo(pagina)

            if es_ticket:
                dpi = _DPI_TICKET
                score_min = _SCORE_MINIMO
                tipo_str = "ticket"
            elif nativo:
                dpi = _DPI_NATIVO
                score_min = _SCORE_MINIMO_NATIVO
                tipo_str = "nativo"
            else:
                dpi = _DPI_ESCANEADO
                score_min = _SCORE_MINIMO
                tipo_str = "escaneado"

            escala = dpi / 72.0
            mat = fitz.Matrix(escala, escala)
            pix = pagina.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            img_proc = _preprocesar_imagen(img_array, nativo=nativo)
            lineas = _ocr_desde_array(ocr, img_proc, score_minimo=score_min)
            paginas_texto.append("\n".join(lineas))

            print(
                f"  Pagina {num + 1}/{len(doc)} "
                f"({dpi} DPI, {tipo_str}, score>={score_min}) -- {len(lineas)} lineas"
            )
        doc.close()

    elif ruta.suffix.lower() in EXTENSIONES_IMAGEN:
        img_array = np.array(Image.open(ruta).convert("RGB"))
        img_proc = _preprocesar_imagen(img_array, nativo=False)
        lineas = _ocr_desde_array(ocr, img_proc, score_minimo=_SCORE_MINIMO)
        paginas_texto.append("\n".join(lineas))
        print(f"  Imagen -- {len(lineas)} lineas")

    else:
        raise ValueError(f"Formato no soportado: {ruta.suffix}")

    print(f"  OCR completado en {time.time() - inicio:.2f}s")
    return "\n\n---Inicio de Pagina---\n\n".join(paginas_texto)
