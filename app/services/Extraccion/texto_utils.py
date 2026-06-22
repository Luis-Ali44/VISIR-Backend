from __future__ import annotations

import re

UUID_PATRON = r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}"

def es_uuid_valido(cadena: str) -> bool:
    return bool(re.fullmatch(UUID_PATRON, cadena, re.IGNORECASE))

def extraer_uuid_del_texto(texto: str) -> str | None:
    m = re.search(
        r"FOLIO\s+FISCAL.*?(" + UUID_PATRON + r")",
        texto, re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1).upper()

    m = re.search(r"\|(" + UUID_PATRON + r")\|", texto)
    if m:
        return m.group(1).upper()

    relacionados = {
        u.upper() for u in re.findall(r"[•\-]\s*(" + UUID_PATRON + r")", texto)
    }
    candidatos = [
        u.upper() for u in re.findall(UUID_PATRON, texto)
        if u.upper() not in relacionados
    ]
    if candidatos:
        return candidatos[0]

    m = re.search(
        r"[0-9A-Fa-f\s]{8,}-[0-9A-Fa-f\s]{4,}-[0-9A-Fa-f\s]{4,}-[0-9A-Fa-f\s]{4,}-[0-9A-Fa-f\s]{12,}",
        texto,
    )
    if m:
        limpio = re.sub(r"\s", "", m.group(0))
        if re.fullmatch(UUID_PATRON, limpio, re.IGNORECASE):
            limpio_upper = limpio.upper()
            if limpio_upper not in relacionados:
                return limpio_upper

    return None

def normalizar_fecha(fecha_str: str | None) -> str | None:
    if not fecha_str or not isinstance(fecha_str, str):
        return None
    s = fecha_str.strip()
    s = re.sub(r"\s+[aApP]\.?\s*[mM]\.?$", "", s).strip()
    s = re.sub(r"[+-]\d{2}:\d{2}$", "", s).rstrip("Z").strip()
    s = re.sub(r"\.\d+$", "", s)
    s = re.sub(r"[T ]", "T", s, count=1)
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})(?:T(\d{2}:\d{2}(?::\d{2})?))?$", s)
    if m:
        hora = m.group(4) or "00:00:00"
        if len(hora) == 5:
            hora += ":00"
        s = f"{m.group(3)}-{m.group(2)}-{m.group(1)}T{hora}"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        s += "T00:00:00"
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$", s):
        s += ":00"
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", s):
        return s
    return None

VALORES_NULOS = {"null", "none", "n/a", "na", "-", "ninguno", ""}

def es_valor_nulo(v: object) -> bool:
    return isinstance(v, str) and v.strip().lower() in VALORES_NULOS
