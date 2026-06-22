from __future__ import annotations

import contextlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from ...schemas.schema_extraccion import validar
from .catalogos import (
    CATALOGO_CLAVE_UNIDAD,
    CATALOGO_FORMA_PAGO,
    CATALOGO_METODO_PAGO,
    normalizar_catalogo,
    normalizar_rfc,
    validar_formato_rfc,
)
from .llm_extractor import construir_prompt
from .texto_utils import es_uuid_valido, es_valor_nulo, extraer_uuid_del_texto
from .texto_utils import normalizar_fecha as _normalizar_fecha

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL   = "mistral-large-latest"
MAX_REINTENTOS  = 4

EXTENSIONES_PDF    = {".pdf"}
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
EXTENSIONES_XML    = {".xml"}


def _norm_rfc(rfc: str) -> str:
    return normalizar_rfc(rfc)


def detectar_version(ruta: Path | None) -> str | None:
    if ruta and ruta.suffix.lower() == ".pdf":
        return _version_desde_pdf_embebido(ruta)
    return None


def _version_desde_pdf_embebido(ruta: Path) -> str | None:
    try:
        import fitz
        doc = fitz.open(str(ruta))
        for i in range(doc.embfile_count()):
            try:
                info = doc.embfile_info(i)
                if info.get("filename", "").lower().endswith(".xml"):
                    datos = doc.embfile_get(i).decode("utf-8", errors="ignore")
                    m = re.search(r'[Vv]ersion\s*=\s*"?(4\.0|3\.3)"?', datos)
                    if m:
                        doc.close()
                        return m.group(1)
            except Exception:
                continue
        doc.close()
    except Exception:
        pass
    return None


def _limpiar_nulos(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _limpiar_nulos(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_limpiar_nulos(i) for i in obj]
    return None if es_valor_nulo(obj) else obj


def _postprocesar(
    datos: dict,
    version: str | None,
    uuid_extraido: str | None = None,
) -> dict:

    datos = _limpiar_nulos(datos)

    datos["metodo_pago"] = normalizar_catalogo(datos.get("metodo_pago"), CATALOGO_METODO_PAGO)
    datos["forma_pago"]  = normalizar_catalogo(datos.get("forma_pago"),  CATALOGO_FORMA_PAGO)
    for concepto in datos.get("conceptos", []):
        if isinstance(concepto, dict):
            concepto["unidad"] = normalizar_catalogo(concepto.get("unidad"), CATALOGO_CLAVE_UNIDAD)

    for entidad in ("emisor", "receptor"):
        nodo = datos.get(entidad, {})
        if isinstance(nodo, dict):
            rfc = nodo.get("RFC") or nodo.get("rfc")
            if rfc:
                nodo["RFC"] = _norm_rfc(str(rfc))
                if not validar_formato_rfc(nodo["RFC"]):
                    print(f" RFC {entidad} '{nodo['RFC']}' no tiene un formato válido")

    uuid_llm = str(datos.get("folio_fiscal") or "")
    if uuid_extraido and es_uuid_valido(uuid_extraido):
        if uuid_llm and es_uuid_valido(uuid_llm) and uuid_llm.upper() != uuid_extraido.upper():
            print(
                f"  [UUID] AVISO: LLM ('{uuid_llm}') y OCR ('{uuid_extraido}') "
                "no coinciden, ambos con formato válido. Se usa el de OCR; "
                "revisar manualmente si el monto/folio resultante no cuadra."
            )
        elif uuid_llm and uuid_llm.upper() != uuid_extraido.upper():
            print(
                f"LLM dio '{uuid_llm}' UUID on formato invalido "
                f"reemplazado por '{uuid_extraido}' del OCR"
            )
        datos["folio_fiscal"] = uuid_extraido.upper()
    elif not datos.get("folio_fiscal"):
        pass
    else:
        raw = re.sub(r"\s", "", str(datos["folio_fiscal"]).upper())
        sin_guiones = raw.replace("-", "")
        if len(sin_guiones) == 32 and re.fullmatch(r"[0-9A-F]{32}", sin_guiones):
            datos["folio_fiscal"] = (
                f"{sin_guiones[:8]}-{sin_guiones[8:12]}-"
                f"{sin_guiones[12:16]}-{sin_guiones[16:20]}-{sin_guiones[20:]}"
            )

    if version and not datos.get("version"):
        datos["version"] = version

    datos["fecha_emision"] = _normalizar_fecha(datos.get("fecha_emision"))
    if "fecha" in datos and "fecha_emision" not in datos:
        datos["fecha_emision"] = _normalizar_fecha(datos.pop("fecha"))
    else:
        datos.pop("fecha", None)

    return datos


def _extraer_todos_los_json(texto: str) -> list[dict]:
    resultados = []
    i = 0
    while i < len(texto):
        inicio = texto.find("{", i)
        if inicio == -1:
            break
        contador, fin = 0, -1
        for j, c in enumerate(texto[inicio:], start=inicio):
            contador += (c == "{") - (c == "}")
            if contador == 0:
                fin = j + 1
                break
        if fin == -1:
            break
        with contextlib.suppress(json.JSONDecodeError):
            resultados.append(json.loads(texto[inicio:fin]))
        i = fin
    return resultados


def _llamar_mistral(client, prompt: str) -> str:
    for intento in range(MAX_REINTENTOS):
        try:
            response = client.chat.complete(
                model=MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if "429" in str(e):
                espera = 20 * (intento + 1)
                print(
                    f"  Rate limit — esperando {espera}s "
                    f"(intento {intento + 1}/{MAX_REINTENTOS})"
                )
                time.sleep(espera)
            else:
                raise
    return ""


def _estructurar_con_mistral(
    texto_ocr: str,
    uuid_extraido: str | None,
    version_detectada: str | None,
) -> list[dict]:
    if not MISTRAL_API_KEY:
        raise ValueError(
            "MISTRAL_API_KEY no configurada.\n"
            "Ejecuta: export MISTRAL_API_KEY=tu_clave"
        )
    print(f"Clave de Mistral detectada (longitud={len(MISTRAL_API_KEY)})")

    try:
        from mistralai.client import Mistral
    except ImportError as e:
        raise ImportError("Instala mistralai: pip install mistralai") from e

    print("Validación de librería mistralai OK")

    client = Mistral(api_key=MISTRAL_API_KEY)

    prompt = construir_prompt(
        texto_ocr=texto_ocr,
        version=version_detectada,
        uuid_detectado=uuid_extraido,
    )

    respuesta = _llamar_mistral(client, prompt)
    respuesta = respuesta.replace("```json", "").replace("```", "").strip()

    datos_lista = _extraer_todos_los_json(respuesta)
    if not datos_lista:
        return []

    return [
        _postprocesar(d, version_detectada, uuid_extraido=uuid_extraido)
        for d in datos_lista
    ]


def _extraer_texto_ocr(ruta: Path) -> str:
    from .ocr_paddle import SCORE_MINIMO, SCORE_MINIMO_NATIVO, _get_paddle_ocr, _ocr_desde_array
    from .ocr_preprocess import extraer_imagen_suelta, extraer_paginas_pdf

    paginas = (
        extraer_paginas_pdf(ruta)
        if ruta.suffix.lower() == ".pdf"
        else extraer_imagen_suelta(ruta)
    )

    ocr = _get_paddle_ocr()
    bloques = []
    for img_proc, tipo, _dpi, _num, _total in paginas:
        score_min = SCORE_MINIMO_NATIVO if tipo == "nativo" else SCORE_MINIMO
        lineas = _ocr_desde_array(ocr, img_proc, score_minimo=score_min)
        bloques.append("\n".join(lineas))

    return "\n\n---Inicio de Pagina---\n\n".join(bloques)


def procesar(ruta_archivo: str | Path, guardar_txt: bool = True) -> dict:
    ruta = Path(ruta_archivo)
    ext  = ruta.suffix.lower()

    xml_hermano = ruta.with_suffix(".xml")
    if ext != ".xml" and xml_hermano.exists():
        return procesar(xml_hermano)

    if ext in EXTENSIONES_XML:
        from .xml_parser import extraer_desde_xml
        datos = extraer_desde_xml(ruta)
        valido, errores, _modelo = validar(datos)
        out_json = ruta.parent / f"{ruta.stem}_cfdis.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({"archivo": ruta.stem, "fuente": "xml", "datos": datos},
                      f, ensure_ascii=False, indent=2)
        return {"archivo": ruta.stem, "fuente": "xml", "datos": datos,
                "valido": valido, "errores": errores}

    if ext not in (EXTENSIONES_PDF | EXTENSIONES_IMAGEN):
        raise ValueError(f"Formato no soportado: {ext}")

    texto_ocr = _extraer_texto_ocr(ruta)
    print(f"Extracción OCR completada ({len(texto_ocr)} caracteres extraídos)")

    if guardar_txt:
        txt_path = ruta.parent / f"{ruta.stem}_ocr.txt"
        txt_path.write_text(texto_ocr, encoding="utf-8")

    version_detectada = detectar_version(ruta)
    uuid_extraido     = extraer_uuid_del_texto(texto_ocr)

    facturas = _estructurar_con_mistral(texto_ocr, uuid_extraido, version_detectada)
    print(f"Estructuración con LLM completada ({len(facturas)} factura(s) detectada(s))")

    version_final = version_detectada or next(
        (f.get("version") for f in facturas if f.get("version")), None
    )

    for factura in facturas:
        if not factura.get("version"):
            factura["version"] = version_final

    resultados_validados = []
    for i, factura in enumerate(facturas):
        factura["archivo"] = f"{ruta.stem}_cfdi_{i + 1:02d}"
        valido, errores, _ = validar(factura)
        resultados_validados.append({
            "datos":   factura,
            "valido":  valido,
            "errores": errores,
        })

    resultado = {
        "archivo": ruta.stem,
        "fuente":  "ocr+llm",
        "version": version_final,
        "cfdis":   resultados_validados,
    }

    out_json = ruta.parent / f"{ruta.stem}_cfdis.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    return resultado


def procesar_carpeta(carpeta: str | Path) -> list[dict]:
    carpeta  = Path(carpeta)
    archivos = sorted(
        p for p in carpeta.rglob("*")
        if p.suffix.lower() in (EXTENSIONES_PDF | EXTENSIONES_IMAGEN | EXTENSIONES_XML)
    )
    if not archivos:
        return []

    resultados = []
    for arch in archivos:
        try:
            xml_hermano = arch.with_suffix(".xml")
            if arch.suffix.lower() != ".xml" and xml_hermano.exists():
                continue
            resultados.append(procesar(arch))
        except Exception as e:
            print(f"  ERROR procesando {arch.name}: {e}")

    return resultados


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CFDI Pipeline — PaddleOCR + Mistral")
    parser.add_argument("ruta", nargs="?", help="PDF, imagen, XML o carpeta")
    args = parser.parse_args()

    if args.ruta:
        target = Path(args.ruta)
        if target.is_dir():
            procesar_carpeta(target)
        else:
            procesar(target)
    else:
        candidatos = sorted(Path(".").glob("*.pdf"))
        if not candidatos:
            print("ERROR: No se encontró ningún PDF.")
            print("Uso: python pipeline.py ruta/al/archivo.pdf")
            sys.exit(1)
        procesar(candidatos[0])