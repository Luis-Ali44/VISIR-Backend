from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from catalogos import (
    CATALOGO_METODO_PAGO,
    CATALOGO_FORMA_PAGO,
    CATALOGO_USO_CFDI,
    CATALOGO_TIPO_COMPROBANTE,
    CATALOGO_CLAVE_UNIDAD,
    normalizar_catalogo,
    validar_digito_rfc,
)
from schema import validar

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL   = "mistral-large-latest"
MAX_REINTENTOS  = 4

EXTENSIONES_PDF    = {".pdf"}
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
EXTENSIONES_XML    = {".xml"}


def _norm_rfc(rfc: str) -> str:
    return re.sub(r"[\s\-_]", "", rfc.upper().strip())


def es_uuid_valido(cadena: str) -> bool:
    return bool(re.match(
        r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$",
        cadena,
    ))


def _reparar_uuid_ocr(candidato: str) -> str | None:
    mapa = {
        "O": "0", "o": "0", "I": "1", "l": "1", "|": "1",
        "B": "8", "S": "5", "Z": "2", "G": "6", "Q": "0", "U": "0",
    }
    limpio = "".join(mapa.get(ch, ch) for ch in candidato)
    limpio = re.sub(r"[^0-9A-Fa-f-]", "", limpio)
    if "-" in limpio:
        if re.fullmatch(r"[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}", limpio, re.IGNORECASE):
            return limpio.upper()
    else:
        if len(limpio) == 32 and re.fullmatch(r"[0-9A-F]{32}", limpio, re.IGNORECASE):
            s = limpio.upper()
            return f"{s[:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:]}"
    return None


def extraer_uuid_del_texto(texto: str) -> str | None:
    for patron in (
        r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}",
        r"\|\|1\.1\|([0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12})\|",
        r"[0-9A-Fa-fOoIiBbSsZz]{8}-[0-9A-Fa-fOoIiBbSsZz]{4}-[0-9A-Fa-fOoIiBbSsZz]{4}-[0-9A-Fa-fOoIiBbSsZz]{4}-[0-9A-Fa-fOoIiBbSsZz]{12}",
    ):
        m = re.search(patron, texto)
        if m:
            candidato = m.group(1) if m.lastindex else m.group(0)
            reparado = _reparar_uuid_ocr(candidato)
            if reparado:
                return reparado

    m = re.search(r"(?<![0-9A-Fa-f])([0-9A-Fa-f]{32})(?![0-9A-Fa-f])", texto)
    if m:
        reparado = _reparar_uuid_ocr(m.group(1))
        if reparado:
            return reparado

    return None


def detectar_version(texto: str, ruta: Path | None = None) -> str | None:
    if "||1.1|" in texto:
        return "4.0"
    if "||1.0|" in texto:
        return "3.3"

    for patron in (
        r'[Vv]ersion\s*=\s*"?(4\.0|3\.3)"?',
        r"[Cc][Ff][Dd][Ii]\s*:?\s*(4\.0|3\.3)",
        r"VERSI[OÓ]N\s*:?\s*(4\.0|3\.3)",
        r"\bV(4\.0|3\.3)\b",
    ):
        m = re.search(patron, texto, re.IGNORECASE)
        if m:
            return m.group(1).replace(",", ".")

    if ruta and ruta.suffix.lower() == ".pdf":
        v = _version_desde_pdf_embebido(ruta)
        if v:
            return v

    indicadores_40 = ["RegimenFiscalReceptor", "DomicilioFiscalReceptor",
                      "REGIMEN FISCAL RECEPTOR", "DOMICILIO FISCAL RECEPTOR"]
    if any(ind in texto for ind in indicadores_40):
        return "4.0"

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
        for pagina in doc:
            texto = pagina.get_text()
            if "||1.1|" in texto:
                doc.close()
                return "4.0"
            if "||1.0|" in texto:
                doc.close()
                return "3.3"
        doc.close()
    except Exception:
        pass
    return None


def _limpiar_nulos(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _limpiar_nulos(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_limpiar_nulos(i) for i in obj]
    return None if obj == "null" else obj


def _postprocesar(datos: dict, version: str | None, uuid_fallback: str | None = None) -> dict:
    datos = _limpiar_nulos(datos)

    datos["metodo_pago"]         = normalizar_catalogo(datos.get("metodo_pago"),         CATALOGO_METODO_PAGO)
    datos["forma_pago"]          = normalizar_catalogo(datos.get("forma_pago"),          CATALOGO_FORMA_PAGO)
    datos["uso_cfdi"]            = normalizar_catalogo(datos.get("uso_cfdi"),            CATALOGO_USO_CFDI)
    datos["tipo_de_comprobante"] = normalizar_catalogo(datos.get("tipo_de_comprobante"), CATALOGO_TIPO_COMPROBANTE)

    for concepto in datos.get("conceptos", []):
        if isinstance(concepto, dict):
            concepto["unidad"] = normalizar_catalogo(concepto.get("unidad"), CATALOGO_CLAVE_UNIDAD)

    for entidad in ("emisor", "receptor"):
        nodo = datos.get(entidad, {})
        if isinstance(nodo, dict):
            rfc = nodo.get("RFC") or nodo.get("rfc")
            if rfc:
                nodo["RFC"] = _norm_rfc(str(rfc))
                if not validar_digito_rfc(nodo["RFC"]):
                    print(f"  Advertencia: RFC {entidad} '{nodo['RFC']}' no pasa dígito verificador")

    if uuid_fallback and es_uuid_valido(uuid_fallback):
        if not datos.get("folio_fiscal") or "X" in uuid_fallback.upper():
            datos["folio_fiscal"] = uuid_fallback.upper()

    if version and not datos.get("version"):
        datos["version"] = version

    if "fecha" in datos and "fecha_emision" not in datos:
        datos["fecha_emision"] = datos.pop("fecha")
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
        try:
            resultados.append(json.loads(texto[inicio:fin]))
        except json.JSONDecodeError:
            pass
        i = fin
    return resultados


_PROMPT = """Eres un especialista en CFDIs e información fiscal mexicana.
El texto puede contener UNO O VARIOS comprobantes fiscales (CFDIs).
Devuelve ÚNICAMENTE objetos JSON válidos, uno por cada CFDI encontrado,
separados por salto de línea. Sin explicaciones, sin markdown, sin texto extra.
Si un campo no aparece en el texto usa null.
{nota_uuid}
REGLAS CRÍTICAS:

1. VERSIÓN: La versión detectada automáticamente es "{version}".
   Usa exactamente ese valor.

2. EMISOR vs RECEPTOR — regla de posición:
   - EMISOR: quien EXPIDE la factura. RFC y nombre en el ENCABEZADO, ANTES del "FOLIO FISCAL".
   - RECEPTOR: quien RECIBE. Sus datos aparecen DESPUÉS del folio fiscal.
   - NUNCA pongas el mismo RFC en emisor y receptor.

3. metodo_pago: exactamente 'PUE' o 'PPD'.
4. forma_pago: código de 2 dígitos ('01', '02', '03', '28', '99').
5. folio_fiscal: formato xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.
6. fecha_emision: copia la cadena COMPLETA tal como aparece.

Estructura EXACTA por CFDI:
{{
    "folio_fiscal": null,
    "fecha_emision": null,
    "version": null,
    "emisor": {{"nombre": null, "RFC": null}},
    "receptor": {{"nombre": null, "RFC": null}},
    "serie": null,
    "folio": null,
    "metodo_pago": null,
    "forma_pago": null,
    "moneda": null,
    "uso_cfdi": null,
    "tipo_de_comprobante": null,
    "conceptos": [
        {{
            "descripcion": null,
            "clave_prod_serv": null,
            "unidad": null,
            "cantidad": null,
            "valor_unitario": null,
            "descuento": null,
            "importe": null,
            "iva": null
        }}
    ],
    "subtotal": null,
    "descuento": null,
    "iva": null,
    "retenciones": null,
    "total": null
}}

Texto OCR:
{texto}
"""


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
                print(f"  Rate limit — esperando {espera}s (intento {intento + 1}/{MAX_REINTENTOS})")
                time.sleep(espera)
            else:
                raise
    return ""


def _second_pass_rfc(texto_ocr: str, facturas: list[dict], client) -> list[dict]:
    necesita = any(
        not f.get("emisor", {}).get("RFC") or not f.get("receptor", {}).get("RFC")
        for f in facturas
    )
    if not necesita:
        return facturas

    prompt_rfc = (
        "Del siguiente texto de una factura CFDI mexicana, extrae SOLO los RFCs.\n"
        "EMISOR RFC: aparece en el ENCABEZADO, ANTES de la sección 'FOLIO FISCAL'.\n"
        "RECEPTOR RFC: aparece DESPUÉS del folio fiscal.\n"
        "Responde ÚNICAMENTE con este JSON:\n"
        '{"emisor_rfc": "RFC_O_null", "receptor_rfc": "RFC_O_null"}\n\n'
        f"Texto OCR:\n{texto_ocr[:3000]}"
    )
    try:
        resp = _llamar_mistral(client, prompt_rfc)
        resp = resp.replace("```json", "").replace("```", "").strip()
        rfcs = json.loads(resp)
        for factura in facturas:
            emisor   = factura.setdefault("emisor",   {"nombre": None, "RFC": None})
            receptor = factura.setdefault("receptor", {"nombre": None, "RFC": None})
            if not emisor.get("RFC") and rfcs.get("emisor_rfc") not in (None, "null"):
                emisor["RFC"] = rfcs["emisor_rfc"]
                print(f"    [Second pass] emisor_rfc: {rfcs['emisor_rfc']}")
            if not receptor.get("RFC") and rfcs.get("receptor_rfc") not in (None, "null"):
                receptor["RFC"] = rfcs["receptor_rfc"]
                print(f"    [Second pass] receptor_rfc: {rfcs['receptor_rfc']}")
    except Exception as e:
        print(f"  [Second pass] Error: {e}")
    return facturas


def _estructurar_con_mistral(
    texto_ocr: str,
    uuid_detectado: str | None,
    version_detectada: str | None,
) -> list[dict]:
    if not MISTRAL_API_KEY:
        raise ValueError(
            "MISTRAL_API_KEY no configurada.\n"
            "Ejecuta: export MISTRAL_API_KEY=tu_clave"
        )

    try:
        from mistralai.client import Mistral
    except ImportError:
        raise ImportError("Instala mistralai: pip install mistralai")

    client = Mistral(api_key=MISTRAL_API_KEY)

    nota_uuid = (
        f'\nNOTA: El folio fiscal (UUID) pre-extraído es "{uuid_detectado}". '
        f'Úsalo directamente en "folio_fiscal".\n'
        if uuid_detectado else ""
    )

    prompt = _PROMPT.format(
        nota_uuid=nota_uuid,
        version=version_detectada or "desconocida",
        texto=texto_ocr[:6000],
    )

    respuesta = _llamar_mistral(client, prompt)
    respuesta = respuesta.replace("```json", "").replace("```", "").strip()

    datos_lista = _extraer_todos_los_json(respuesta)
    if not datos_lista:
        print("  [Mistral] Sin JSON en la respuesta")
        return []

    print(f"  {len(datos_lista)} CFDI(s) encontrado(s)")

    facturas = [
        _postprocesar(d, version_detectada, uuid_fallback=uuid_detectado)
        for d in datos_lista
    ]
    facturas = _second_pass_rfc(texto_ocr, facturas, client)
    return facturas


def _extraer_texto_ocr(ruta: Path) -> str:
    from ocr_preprocess import extraer_paginas_pdf, extraer_imagen_suelta, items_a_texto

    if ruta.suffix.lower() == ".pdf":
        paginas = extraer_paginas_pdf(ruta)
    else:
        paginas = extraer_imagen_suelta(ruta)

    from ocr_paddle import _get_paddle_ocr, _ocr_desde_array, SCORE_MINIMO, SCORE_MINIMO_NATIVO

    ocr = _get_paddle_ocr()
    bloques = []
    for img_proc, tipo, dpi, num, total in paginas:
        score_min = SCORE_MINIMO_NATIVO if tipo == "nativo" else SCORE_MINIMO
        lineas = _ocr_desde_array(ocr, img_proc, score_minimo=score_min)
        bloques.append("\n".join(lineas))
        print(f"  Pagina {num}/{total} ({dpi} DPI, {tipo}) — {len(lineas)} lineas")

    return "\n\n---Inicio de Pagina---\n\n".join(bloques)


def procesar(ruta_archivo: str | Path, guardar_txt: bool = True) -> dict:
    ruta = Path(ruta_archivo)
    ext  = ruta.suffix.lower()

    print(f"\n{'='*60}")
    print(f" Procesando: {ruta.name}")
    print(f"{'='*60}")

    xml_hermano = ruta.with_suffix(".xml")
    if ext != ".xml" and xml_hermano.exists():
        print(f"  [XML hermano] usando {xml_hermano.name} en lugar de OCR")
        return procesar(xml_hermano)

    if ext in EXTENSIONES_XML:
        print("[XML] Parseando directamente...")
        from xml_parser import extraer_desde_xml
        datos = extraer_desde_xml(ruta)
        valido, errores, modelo = validar(datos)
        print(f"[Validación] {'OK' if valido else 'ERRORES'}")
        if errores:
            for e in errores:
                print(f"  {e}")

        out_json = ruta.parent / f"{ruta.stem}_cfdis.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({"archivo": ruta.stem, "fuente": "xml", "datos": datos}, f, ensure_ascii=False, indent=2)
        print(f"\n[OK] JSON guardado en: {out_json}")

        return {"archivo": ruta.stem, "fuente": "xml", "datos": datos,
                "valido": valido, "errores": errores}

    if ext not in (EXTENSIONES_PDF | EXTENSIONES_IMAGEN):
        raise ValueError(f"Formato no soportado: {ext}")

    print("Extrayendo texto con PaddleOCR")
    texto_ocr = _extraer_texto_ocr(ruta)

    if guardar_txt:
        txt_path = ruta.parent / f"{ruta.stem}_ocr.txt"
        txt_path.write_text(texto_ocr, encoding="utf-8")
        print(f"[OCR] Texto crudo → {txt_path}")

    version_detectada = detectar_version(texto_ocr, ruta) or "4.0"
    uuid_detectado    = extraer_uuid_del_texto(texto_ocr)

    print(f"[Versión] {version_detectada}")
    print(f"[UUID] {uuid_detectado or 'no encontrado'}")

    print(f"\n[Mistral] Estructurando con {MISTRAL_MODEL}")
    facturas = _estructurar_con_mistral(texto_ocr, uuid_detectado, version_detectada)

    resultados_validados = []
    for i, factura in enumerate(facturas):
        factura["archivo"] = f"{ruta.stem}_cfdi_{i + 1:02d}"
        valido, errores, _ = validar(factura)
        print(f"[Validación CFDI {i+1}] {'OK' if valido else 'ERRORES'}")
        if errores:
            for e in errores:
                print(f"  {e}")
        resultados_validados.append({
            "datos": factura,
            "valido": valido,
            "errores": errores,
        })

    resultado = {
        "archivo":  ruta.stem,
        "fuente":   "ocr+llm",
        "version":  version_detectada,
        "cfdis":    resultados_validados,
    }

    out_json = ruta.parent / f"{ruta.stem}_cfdis.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] JSON guardado en: {out_json}")

    return resultado


def procesar_carpeta(carpeta: str | Path) -> list[dict]:
    carpeta = Path(carpeta)
    archivos = sorted(
        p for p in carpeta.rglob("*")
        if p.suffix.lower() in (EXTENSIONES_PDF | EXTENSIONES_IMAGEN | EXTENSIONES_XML)
    )
    if not archivos:
        print(f"No se encontraron archivos compatibles en {carpeta}")
        return []

    print(f"Procesando {len(archivos)} archivo(s) en {carpeta}...")
    resultados = []
    for arch in archivos:
        try:
            xml_hermano = arch.with_suffix(".xml")
            if arch.suffix.lower() != ".xml" and xml_hermano.exists():
                print(f"  [Skip] {arch.name} — existe XML hermano")
                continue

            resultados.append(procesar(arch))
        except Exception as e:
            print(f"  ERROR procesando {arch.name}: {e}")

    print(f"\nTotal procesados: {len(resultados)}/{len(archivos)}")
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
        print(f"[Auto] Usando: {candidatos[0]}\n")
        procesar(candidatos[0])
