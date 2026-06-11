from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from app.services.Extraccion.catalogos import (
    CATALOGO_CLAVE_UNIDAD,
    CATALOGO_FORMA_PAGO,
    CATALOGO_METODO_PAGO,
    CATALOGO_USO_CFDI,
    normalizar_catalogo,
)

LLM_CONFIG = {
    "ollama_url": "http://localhost:11434/api/generate",
    "mistral_model": "mistral-large-latest",
    "ollama_model": "llama3.2:latest",
    "timeout": 300,
    "temperature": 0.0,
    "max_tokens": 8192,
}

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")


def extraer_campos_regex(texto: str) -> dict[str, Any]:
    resultado: dict[str, Any] = {
        "version": None,
        "emisor_rfc": None,
        "emisor_nombre": None,
        "receptor_rfc": None,
        "receptor_nombre": None,
        "folio_fiscal": None,
        "fecha_emision": None,
        "metodo_pago": None,
        "forma_pago": None,
        "moneda": None,
        "subtotal": None,
        "iva": None,
        "total": None,
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
        resultado["emisor_rfc"] = rfc_list[0].upper()
        if len(rfc_list) > 1:
            resultado["receptor_rfc"] = rfc_list[1].upper()

    m = re.search(r"Emisor.*?Nombre\s*:?\s*([^\n]+)", texto, re.IGNORECASE | re.DOTALL)
    if m:
        resultado["emisor_nombre"] = m.group(1).strip()
    m = re.search(r"Receptor.*?Nombre\s*:?\s*([^\n]+)", texto, re.IGNORECASE | re.DOTALL)
    if m:
        resultado["receptor_nombre"] = m.group(1).strip()

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
        texto,
        re.IGNORECASE,
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
    m = re.search(
        r"(?:IVA|Impuesto trasladado)\s*:?\s*\$?\s*([\d,]+(?:\.\d{1,2})?)", texto, re.IGNORECASE
    )
    if m:
        resultado["iva"] = float(m.group(1).replace(",", ""))
    m = re.search(r"\bTOTAL\s*:?\s*\$?\s*([\d,]+(?:\.\d{1,2})?)", texto, re.IGNORECASE)
    if m:
        resultado["total"] = float(m.group(1).replace(",", ""))

    return resultado


_PROMPT_EXTRACCION = """Eres un extractor de datos para facturas CFDI mexicanas.
Debes EXTRAER LITERALMENTE los valores tal como aparecen en el texto OCR.
NO CORRIJAS, NO INTERPRETES, NO NORMALICES. Copia exactamente los caracteres.

Si un campo tiene formato diferente al esperado (ej. UUID sin guiones), cópialo tal cual.
No añadas ni quites guiones, espacios, ni cambies mayúsculas/minúsculas.

Devuelve SOLO un objeto JSON válido, sin texto adicional ni markdown.
Si un campo no aparece, usa null.

Esquema JSON requerido:
{{
    "version": "string ('3.3' o '4.0')",
    "emisor_rfc": "string (sin guiones ni espacios)",
    "emisor_nombre": "string",
    "receptor_rfc": "string",
    "receptor_nombre": "string",
    "folio_fiscal": (
    "string UUID con o sin guiones, tal cual aparece,
    formato xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)",
    "fecha_emision":
    "string — copia la cadena COMPLETA tal como aparece,
    incluyendo hora, 'a.m.', 'p.m.', 'T', etc.",
    "metodo_pago": "string ('PUE' o 'PPD')",
    "forma_pago": "string (código de 2 dígitos)",
    "moneda": "string (código ISO: 'MXN', 'USD', 'EUR')",
    "subtotal": "number",
    "iva": "number",
    "total": "number",
    "conceptos": [
        {{
            "descripcion": "string — copia el texto COMPLETO y LITERAL tal como aparece.
            NO resumir, NO parafrasear.",
            "clave_prod_serv": "string (8 dígitos)",
            "unidad": "string (clave SAT: 'H87', 'E48', 'KGM')",
            "cantidad": "number",
            "valor_unitario": "number",
            "importe": "number"
        }}
    ]
}}

REGLAS CRÍTICAS:
1. folio_fiscal: busca el UUID en TODO el documento, incluso dentro de la Cadena Original del SAT.
2. fecha_emision:
busca 'Fecha de emisión',
'Fecha Expedicion',
'FECHA Y HORA DE EMISIÓN DE CFDI'.
COPIA la cadena exacta.
3. version: si en la cadena original aparece '||1.1|' la versión es '4.0'.
Si aparece '||1.0|' es '3.3'.
4. NUNCA inventes datos. Si no está visible en el texto, usa null.

TEXTO OCR:
{texto}

JSON:"""


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
                        print(f"    Rate limit/error, reintento {intento + 1}/3 en {espera}s")
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
                cleaned = cleaned[len(prefix) :]
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

    def _normalizar(self, resultado: dict, texto_ocr: str = "") -> dict:
        norm = resultado.copy()

        if self.use_regex_fallback and texto_ocr:
            regex_data = extraer_campos_regex(texto_ocr)
            for key in norm:
                if norm.get(key) is None and regex_data.get(key) is not None:
                    norm[key] = regex_data[key]
                    print(f"    [Fallback regex] {key}: {norm[key]}")
            if not norm.get("conceptos") and regex_data.get("conceptos"):
                norm["conceptos"] = regex_data["conceptos"]

        norm["metodo_pago"] = normalizar_catalogo(norm.get("metodo_pago"), CATALOGO_METODO_PAGO)
        norm["forma_pago"] = normalizar_catalogo(norm.get("forma_pago"), CATALOGO_FORMA_PAGO)
        norm["uso_cfdi"] = normalizar_catalogo(norm.get("uso_cfdi"), CATALOGO_USO_CFDI)

        for campo in ("subtotal", "iva", "total"):
            v = norm.get(campo)
            if v is not None:
                try:
                    norm[campo] = round(float(v), 2)
                except (ValueError, TypeError):
                    norm[campo] = None

        for campo in ("emisor_rfc", "receptor_rfc"):
            if norm.get(campo):
                norm[campo] = re.sub(r"[\s\-_]", "", str(norm[campo]).upper())

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

    def extract(self, texto_ocr: str, use_cache: bool = True) -> dict[str, Any]:
        cache_key = hash(texto_ocr[:2000])
        if use_cache and cache_key in self._cache:
            return self._cache[cache_key]

        prompt = _PROMPT_EXTRACCION.format(texto=texto_ocr[:6000])
        response = self._call_llm(prompt)
        resultado = self._parse_json(response)

        if not resultado:
            print("  [LLM] Respuesta vacía — usando solo regex")
            resultado = extraer_campos_regex(texto_ocr)

        resultado = self._normalizar(resultado, texto_ocr)

        if use_cache:
            self._cache[cache_key] = resultado

        return resultado
