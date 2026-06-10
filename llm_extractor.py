from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from catalogos import (
    CATALOGO_METODO_PAGO,
    CATALOGO_FORMA_PAGO,
    CATALOGO_CLAVE_UNIDAD,
    normalizar_catalogo,
)

LLM_CONFIG = {
    "ollama_url":    "http://localhost:11434/api/generate",
    "mistral_model": "mistral-large-latest",
    "ollama_model":  "llama3.2:latest",
    "timeout":       300,
    "temperature":   0.0,
    "max_tokens":    8192,
}

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")

_PROMPT_CFDI = """\
Eres un especialista en CFDIs e información fiscal mexicana.
El texto puede contener UNO O VARIOS comprobantes fiscales (CFDIs).
Devuelve ÚNICAMENTE objetos JSON válidos, uno por CFDI encontrado,
separados por salto de línea. Sin explicaciones, sin markdown, sin texto extra.
Si un campo no aparece en el texto usa null.
{nota_uuid}

REGLAS CRÍTICAS PARA LA EXTRACCIÓN:

1. VERSIÓN
   La versión pre-detectada es "{version}". Úsala exactamente.
   Si encuentras "||1.1|" en la cadena original → "4.0".
   Si encuentras "||1.0|" en la cadena original → "3.3".

2. EMISOR vs RECEPTOR
   • EMISOR   → quien EXPIDE la factura. RFC y nombre aparecen en el ENCABEZADO,
                ANTES del "FOLIO FISCAL" / UUID.
   • RECEPTOR → quien RECIBE. Sus datos aparecen DESPUÉS del folio fiscal.
   • NUNCA pongas el mismo RFC en emisor y receptor.

3. folio_fiscal
   Busca el UUID en TODO el documento, incluso dentro de la Cadena Original del SAT.
   Formato obligatorio: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (32 hex + 4 guiones).
   Copia los caracteres tal como aparecen, sin inventar ni completar.

4. Fechas (fecha_emision)
   Formato requerido: YYYY-MM-DDTHH:MM:SS (ISO 8601 sin zona horaria).
   Si el texto trae otro formato, conviértelo. Si no hay hora, usa 00:00:00.

5. metodo_pago → exactamente "PUE" o "PPD" (si aparece como pago en parcialidades es PPD y si aparece como pago en una sola exhibición es PUE).
6. forma_pago  → código de 2 dígitos ("01", "02", "03", "28", "99", etc.) Solo extrae el código si aparece EXPLÍCITAMENTE en el texto como número.
7. moneda      → código ISO de 3 letras ("MXN", "USD", "EUR", etc.).
8. Campos numéricos → número sin símbolo de moneda ni comas (ej. 1234.56).
9. RFCs        → sin espacios, sin guiones, en MAYÚSCULAS.
10. NUNCA inventes datos. Si un campo no está visible en el texto → null.
11. descripcion de cada concepto → copia el texto COMPLETO y LITERAL.
    No resumir, no parafrasear.

    
estructura JSON requerida por cada CFDI

{{
    "version":      null,
    "folio_fiscal": null,
    "fecha_emision": null,
    "metodo_pago":  null,
    "forma_pago":   null,
    "moneda":       null,
    "emisor": {{
        "RFC":    null,
        "nombre": null
    }},
    "receptor": {{
        "RFC":    null,
        "nombre": null
    }},
    "conceptos": [
        {{
            "descripcion":     null,
            "clave_prod_serv": null,
            "unidad":          null,
            "cantidad":        null,
            "valor_unitario":  null,
            "descuento":       null,
            "importe":         null,
            "iva":             null
        }}
    ],
    "subtotal":    null,
    "descuento":   null,
    "iva":         null,
    "retenciones": null,
    "total":       null
}}


TEXTO OCR:
{texto}
"""


def construir_prompt(
    texto_ocr: str,
    version: str | None = None,
    uuid_detectado: str | None = None,
    max_chars: int = 6_000,
) -> str:
    nota_uuid = (
        f'\nNOTA: El folio fiscal pre-extraído es "{uuid_detectado}". '
        'Úsalo directamente en "folio_fiscal" sin modificarlo.\n'
        if uuid_detectado else ""
    )
    return _PROMPT_CFDI.format(
        version=version or "desconocida",
        nota_uuid=nota_uuid,
        texto=texto_ocr[:max_chars],
    )


def extraer_campos_regex(texto: str) -> dict[str, Any]:
    resultado: dict[str, Any] = {
        "version": None,
        "emisor":   {"RFC": None, "nombre": None},
        "receptor": {"RFC": None, "nombre": None},
        "folio_fiscal": None, "fecha_emision": None,
        "metodo_pago": None, "forma_pago": None, "moneda": None,
        "subtotal": None, "iva": None, "total": None,
        "descuento": None, "retenciones": None,
        "conceptos": [],
    }

    if "||1.1|" in texto:
        resultado["version"] = "4.0"
    elif "||1.0|" in texto:
        resultado["version"] = "3.3"
    else:
        m = re.search(r"[Cc][Ff][Dd][Ii]\s*[:\-]?\s*[Vv](?:ersi[oó]n)?\s*(4\.0|3\.3)", texto)
        if not m:
            m = re.search(r"VERSI[OÓ]N\s*[:\-]?\s*(4\.0|3\.3)", texto, re.IGNORECASE)
        resultado["version"] = m.group(1) if m else None

    rfc_pattern = r"[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}"
    rfc_list = re.findall(rfc_pattern, texto, re.IGNORECASE)
    if rfc_list:
        resultado["emisor"]["RFC"] = rfc_list[0].upper()
        if len(rfc_list) > 1:
            resultado["receptor"]["RFC"] = rfc_list[1].upper()

    m = re.search(r"Emisor.*?Nombre\s*:?\s*([^\n]+)", texto, re.IGNORECASE | re.DOTALL)
    if m:
        resultado["emisor"]["nombre"] = m.group(1).strip()
    m = re.search(r"Receptor.*?Nombre\s*:?\s*([^\n]+)", texto, re.IGNORECASE | re.DOTALL)
    if m:
        resultado["receptor"]["nombre"] = m.group(1).strip()

    m = re.search(
        r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}",
        texto,
    )
    if m:
        resultado["folio_fiscal"] = m.group(0).upper()
    else:
        m2 = re.search(r"(?<![0-9A-Fa-f])([0-9A-Fa-f]{32})(?![0-9A-Fa-f])", texto)
        if m2:
            raw = m2.group(1).upper()
            resultado["folio_fiscal"] = (
                f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"
            )

    m = re.search(
        r"\b\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2})?\b"
        r"|\b\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}:\d{2}(?:\s*[aApP]\.?\s*[mM]\.?)?)?\b",
        texto, re.IGNORECASE,
    )
    resultado["fecha_emision"] = m.group(0) if m else None

    m = re.search(r"M[ée]todo de pago\s*:?\s*(PUE|PPD)", texto, re.IGNORECASE)
    resultado["metodo_pago"] = m.group(1).upper() if m else None
    m = re.search(r"Forma de pago\s*:?\s*(\d{2})", texto, re.IGNORECASE)
    resultado["forma_pago"] = m.group(1) if m else None

    m = re.search(r"Moneda\s*:?\s*([A-Z]{3})", texto, re.IGNORECASE)
    resultado["moneda"] = m.group(1).upper() if m else None

    m = re.search(r"SUBTOTAL\s*:?\s*\$?\s*([\d,]+(?:\.\d{1,2})?)", texto, re.IGNORECASE)
    if m:
        resultado["subtotal"] = float(m.group(1).replace(",", ""))
    m = re.search(r"(?:IVA|Impuesto trasladado)\s*:?\s*\$?\s*([\d,]+(?:\.\d{1,2})?)", texto, re.IGNORECASE)
    if m:
        resultado["iva"] = float(m.group(1).replace(",", ""))
    m = re.search(r"\bTOTAL\s*:?\s*\$?\s*([\d,]+(?:\.\d{1,2})?)", texto, re.IGNORECASE)
    if m:
        resultado["total"] = float(m.group(1).replace(",", ""))

    return resultado


def _normalizar_fecha(fecha_str: str | None) -> str | None:
    if not fecha_str or not isinstance(fecha_str, str):
        return None
    s = fecha_str.strip()
    s = re.sub(r"\s+[aApP]\.?\s*[mM]\.?$", "", s).strip()
    s = re.sub(r"[+-]\d{2}:\d{2}$", "", s).rstrip("Z").strip()
    s = re.sub(r"\.\d+$", "", s)
    s = re.sub(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})", r"\1T\2", s)
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})(?:[T ](\d{2}:\d{2}(?::\d{2})?))?$", s)
    if m:
        hora = m.group(4) or "00:00:00"
        if len(hora) == 5:
            hora += ":00"
        s = f"{m.group(3)}-{m.group(2)}-{m.group(1)}T{hora}"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        s = s + "T00:00:00"
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$", s):
        s = s + ":00"
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", s):
        return s
    print(f"  [LLM Fecha] No se pudo normalizar: {fecha_str!r}")
    return None


_UUID_PATRON = r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"


class LLMPipeline:

    def __init__(
        self,
        model: str | None = None,
        provider: str = "mistral",
        timeout: int | None = None,
        temperature: float | None = None,
        use_regex_fallback: bool = True,
    ):
        self.provider = provider.lower()
        self.timeout = timeout or LLM_CONFIG["timeout"]
        self.temperature = temperature if temperature is not None else LLM_CONFIG["temperature"]
        self.use_regex_fallback = use_regex_fallback

        if model:
            self.model = model
        elif self.provider == "mistral":
            self.model = LLM_CONFIG["mistral_model"]
        else:
            self.model = LLM_CONFIG["ollama_model"]

        self._cache: dict[int, dict] = {}

    def _call_ollama(self, prompt: str) -> str:
        import requests
        payload = {
        "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": LLM_CONFIG["max_tokens"],
            },
        }
        try:
            resp = requests.post(LLM_CONFIG["ollama_url"], json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            print(f"  [LLM Ollama] Error: {e}")
            return ""

    def _call_mistral(self, prompt: str) -> str:
        if not MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY no configurada. Usa: export MISTRAL_API_KEY=tu_clave")
        try:
            from mistralai import Mistral
            client = Mistral(api_key=MISTRAL_API_KEY)
            for intento in range(3):
                try:
                    response = client.chat.complete(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.temperature,
                        max_tokens=LLM_CONFIG["max_tokens"],
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    if intento < 2 and ("timeout" in str(e).lower() or "429" in str(e)):
                        espera = 20 * (intento + 1)
                        print(f"    Rate limit/error, reintento {intento+1}/3 en {espera}s")
                        time.sleep(espera)
                        continue
                    raise
        except Exception as e:
            print(f"  [LLM Mistral] Error: {e}")
            return ""

    def _call_llm(self, prompt: str) -> str:
        if self.provider == "mistral":
            return self._call_mistral(prompt)
        return self._call_ollama(prompt)

    def _parse_json(self, response: str) -> dict[str, Any]:
        cleaned = response.strip()
        for prefix in ("```json", "```"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", cleaned)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    pass
            print("  [LLM] No se pudo parsear JSON — usando regex fallback")
            return {}

    def _validar_uuid_contra_texto(
        self, uuid_llm: str | None, texto_ocr: str
    ) -> str | None:
        
        if not texto_ocr:
            return uuid_llm

        if uuid_llm and uuid_llm.upper() in texto_ocr.upper():
            return uuid_llm

        m = re.search(
            r"FOLIO\s+FISCAL.*?(" + _UUID_PATRON + r")",
            texto_ocr, re.IGNORECASE | re.DOTALL,
        )
        if m:
            corregido = m.group(1).upper()
            print(
                f"    [UUID fix] LLM dio '{uuid_llm}' → "
                f"corregido a '{corregido}' (etiqueta FOLIO FISCAL)"
            )
            return corregido

        m = re.search(r"\|(" + _UUID_PATRON + r")\|", texto_ocr)
        if m:
            corregido = m.group(1).upper()
            print(
                f"    [UUID fix] LLM dio '{uuid_llm}' → "
                f"corregido a '{corregido}' (cadena original SAT)"
            )
            return corregido

        todos = re.findall(_UUID_PATRON, texto_ocr)
        relacionados = set(
            u.upper()
            for u in re.findall(
                r"[•\-]\s*(" + _UUID_PATRON + r")", texto_ocr
            )
        )
        candidatos = [u.upper() for u in todos if u.upper() not in relacionados]
        if candidatos:
            corregido = candidatos[0]
            print(
                f"    [UUID fix] LLM dio '{uuid_llm}' → "
                f"usando primer UUID candidato: '{corregido}'"
            )
            return corregido
        
        print(f"    [UUID fix] No se encontró UUID alternativo, manteniendo: '{uuid_llm}'")
        return uuid_llm

    def _normalizar(self, resultado: dict, texto_ocr: str = "") -> dict:
        norm = resultado.copy()

        if self.use_regex_fallback and texto_ocr:
            regex_data = extraer_campos_regex(texto_ocr)
            for key in ("folio_fiscal", "fecha_emision", "metodo_pago",
                        "forma_pago", "moneda", "subtotal", "iva", "total", "version"):
                if norm.get(key) is None and regex_data.get(key) is not None:
                    norm[key] = regex_data[key]
                    print(f"    [Fallback regex] {key}: {norm[key]}")

            for entidad in ("emisor", "receptor"):
                if not isinstance(norm.get(entidad), dict):
                    norm[entidad] = {}
                nodo_regex = regex_data.get(entidad, {})
                for subcampo in ("RFC", "nombre"):
                    if not norm[entidad].get(subcampo) and nodo_regex.get(subcampo):
                        norm[entidad][subcampo] = nodo_regex[subcampo]
                        print(f"    [Fallback regex] {entidad}.{subcampo}: {nodo_regex[subcampo]}")

            if not norm.get("conceptos") and regex_data.get("conceptos"):
                norm["conceptos"] = regex_data["conceptos"]

        norm["metodo_pago"]   = normalizar_catalogo(norm.get("metodo_pago"), CATALOGO_METODO_PAGO)
        norm["forma_pago"]    = normalizar_catalogo(norm.get("forma_pago"),  CATALOGO_FORMA_PAGO)
        norm["fecha_emision"] = _normalizar_fecha(norm.get("fecha_emision"))

        for campo in ("subtotal", "iva", "total", "descuento", "retenciones"):
            v = norm.get(campo)
            if v is not None:
                try:
                    norm[campo] = round(float(v), 2)
                except (ValueError, TypeError):
                    norm[campo] = None

        for entidad in ("emisor", "receptor"):
            nodo = norm.get(entidad)
            if isinstance(nodo, dict) and nodo.get("RFC"):
                nodo["RFC"] = re.sub(r"[\s\-_]", "", str(nodo["RFC"]).upper())

        # --- Formatear folio_fiscal ---
        if norm.get("folio_fiscal"):
            raw = re.sub(r"\s", "", str(norm["folio_fiscal"]).upper())
            sin_guiones = raw.replace("-", "")
            if len(sin_guiones) == 32 and re.fullmatch(r"[0-9A-F]{32}", sin_guiones):
                norm["folio_fiscal"] = (
                    f"{sin_guiones[:8]}-{sin_guiones[8:12]}-"
                    f"{sin_guiones[12:16]}-{sin_guiones[16:20]}-{sin_guiones[20:]}"
                )
            else:
                norm["folio_fiscal"] = raw

        if texto_ocr:
            norm["folio_fiscal"] = self._validar_uuid_contra_texto(
                norm.get("folio_fiscal"), texto_ocr
            )

        conceptos = norm.get("conceptos")
        if isinstance(conceptos, list):
            conceptos_norm = []
            for c in conceptos[:10]:
                if not isinstance(c, dict):
                    continue
                for num_campo in ("cantidad", "valor_unitario", "importe", "descuento"):
                    v = c.get(num_campo)
                    if v is not None:
                        try:
                            c[num_campo] = round(float(v), 2)
                        except (ValueError, TypeError):
                            c[num_campo] = None
                c["unidad"] = normalizar_catalogo(c.get("unidad"), CATALOGO_CLAVE_UNIDAD)
                conceptos_norm.append(c)
            norm["conceptos"] = conceptos_norm

        return norm

    def extract(
        self,
        texto_ocr: str,
        version: str | None = None,
        uuid_detectado: str | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        cache_key = hash(texto_ocr[:2000])
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        prompt = construir_prompt(
            texto_ocr=texto_ocr,
            version=version,
            uuid_detectado=uuid_detectado,
        )
        response = self._call_llm(prompt)
        resultado = self._parse_json(response)

        if not resultado:
            print("  [LLM] Respuesta vacía — usando solo regex")
            resultado = extraer_campos_regex(texto_ocr)

        resultado = self._normalizar(resultado, texto_ocr)

        if use_cache:
            self._cache[cache_key] = resultado

        return resultado