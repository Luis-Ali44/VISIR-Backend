from __future__ import annotations

import re


def expandir_abreviaturas(texto: str) -> str:
    texto_upper = texto.upper()
    texto_upper = re.sub(
        r'\bM\.?\s*N\.?\b|\bM/N\b|\bMN\b|\bPESOS?\b|\bPESO\s+MEXICANO\b',
        'MXN', texto_upper
    )
    texto_upper = re.sub(r'\bDLS?\b|\bDOLAR(?:ES)?\b', 'USD', texto_upper)
    texto_upper = re.sub(
        r'PAGO\s+EN\s+UNA\s+SOLA\s+EXHIBICI[OÓ]N|UNA\s+SOLA\s+EXHIBICI[OÓ]N',
        'PUE', texto_upper
    )
    texto_upper = re.sub(
        r'PAGO\s+EN\s+PARCIALIDADES\s+O\s+DIFERIDO|PARCIALIDADES|DIFERIDO',
        'PPD', texto_upper
    )
    mapeo_formas = {
        r'\bEFECTIVO\b': '01',
        r'\bCHEQUE(?:\s+NOMINATIVO)?\b': '02',
        r'TRANSFERENCIA(?:\s+ELECTRONICA(?:\s+DE\s+FONDOS)?)?': '03',
        r'TARJETA\s+DE\s+CREDITO': '04',
        r'TARJETA\s+DE\s+DEBITO|\bDEBITO\b': '28',
        r'\bVALES?\s+DE\s+DESPENSA\b': '08',
    }
    for patron, codigo in mapeo_formas.items():
        texto_upper = re.sub(patron, codigo, texto_upper)
    return texto_upper


CATALOGO_METODO_PAGO: dict[str, str] = {
    "PUE": "PUE", "PPD": "PPD",
    "PAGO EN UNA SOLA EXHIBICION": "PUE",
    "PAGO EN UNA SOLA EXHIBICIÓN": "PUE",
    "UNA SOLA EXHIBICION": "PUE",
    "PAGO EN PARCIALIDADES O DIFERIDO": "PPD",
    "PARCIALIDADES": "PPD",
    "DIFERIDO": "PPD",
}

CATALOGO_FORMA_PAGO: dict[str, str] = {
    "01": "01", "EFECTIVO": "01",
    "02": "02", "CHEQUE NOMINATIVO": "02", "CHEQUE": "02",
    "03": "03", "TRANSFERENCIA ELECTRONICA DE FONDOS": "03", "TRANSFERENCIA": "03",
    "04": "04", "TARJETA DE CREDITO": "04", "CREDITO": "04",
    "28": "28", "TARJETA DE DEBITO": "28", "DEBITO": "28",
    "99": "99", "POR DEFINIR": "99",
}

CATALOGO_USO_CFDI: dict[str, str] = {
    "G01": "G01", "ADQUISICION DE MERCANCIAS": "G01",
    "G02": "G02", "G03": "G03", "GASTOS EN GENERAL": "G03",
    "I01": "I01", "I02": "I02", "I03": "I03", "I04": "I04",
    "D01": "D01", "D02": "D02", "D03": "D03", "D04": "D04",
    "S01": "S01", "SIN EFECTOS FISCALES": "S01",
    "CP01": "CP01", "PAGOS": "CP01",
    "CN01": "CN01", "NOMINA": "CN01",
}

CATALOGO_CLAVE_UNIDAD: dict[str, str] = {
    "H87": "H87", "PIEZA": "H87", "PZA": "H87",
    "E48": "E48", "UNIDAD DE SERVICIO": "E48", "SERVICIO": "E48",
    "KGM": "KGM", "KILOGRAMO": "KGM", "KG": "KGM",
    "LTR": "LTR", "LITRO": "LTR",
    "MTR": "MTR", "METRO": "MTR",
    "E49": "E49", "UNIDAD": "E49",
}

CATALOGO_TIPO_COMPROBANTE: dict[str, str] = {
    "I": "I", "INGRESO": "I",
    "E": "E", "EGRESO": "E",
    "T": "T", "TRASLADO": "T",
    "N": "N", "NOMINA": "N",
    "P": "P", "PAGO": "P",
}


def normalizar_catalogo(valor: str | None, catalogo: dict[str, str]) -> str | None:
    if not valor:
        return valor
    clave = expandir_abreviaturas(str(valor).strip()).upper()
    return catalogo.get(clave, valor)


def _norm_rfc(rfc: str) -> str:
    return re.sub(r"[\s\-_]", "", rfc.upper().strip())


def validar_digito_rfc(rfc: str) -> bool:
    rfc = _norm_rfc(rfc)
    return bool(re.match(r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$", rfc))
