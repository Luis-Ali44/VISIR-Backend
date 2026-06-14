from __future__ import annotations

import re


def expandir_abreviaturas(texto: str) -> str:
    if not texto:
        return texto
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
    "PUE": "PUE",
    "PPD": "PPD",
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
    "05": "05", "MONEDERO ELECTRONICO": "05",
    "06": "06", "DINERO DIGITAL": "06",
    "08": "08", "VALES DE DESPENSA": "08",
    "12": "12", "DACION EN PAGO": "12",
    "13": "13", "PAGO POR SUBROGACION": "13",
    "14": "14", "PAGO POR CONSIGNACION": "14",
    "15": "15", "CONDONACION": "15",
    "17": "17", "COMPENSACION": "17",
    "23": "23", "NOVACION": "23",
    "24": "24", "CONFUSION": "24",
    "25": "25", "REMISION DE DEUDA": "25",
    "26": "26", "PRESCRIPCION O CADUCIDAD": "26",
    "27": "27", "A SATISFACCION DEL ACREEDOR": "27",
    "28": "28", "TARJETA DE DEBITO": "28", "DEBITO": "28",
    "29": "29", "TARJETA DE SERVICIOS": "29",
    "30": "30", "APLICACION DE ANTICIPOS": "30",
    "31": "31", "PAGOS POR INTERMEDIARIO": "31",
    "99": "99", "POR DEFINIR": "99",
}

CATALOGO_CLAVE_UNIDAD: dict[str, str] = {
    "H87": "H87", "PIEZA": "H87", "PZA": "H87",
    "E48": "E48", "UNIDAD DE SERVICIO": "E48", "SERVICIO": "E48",
    "KGM": "KGM", "KILOGRAMO": "KGM", "KG": "KGM",
    "LTR": "LTR", "LITRO": "LTR",
    "MTR": "MTR", "METRO": "MTR",
    "E49": "E49",
    "DAY": "DAY", "DIA": "DAY",
    "GRM": "GRM", "GRAMO": "GRM",
    "MLT": "MLT", "MILILITRO": "MLT",
    "MTK": "MTK", "METRO CUADRADO": "MTK",
    "PR": "PR",  "PAR": "PR",
    "SET": "SET", "CONJUNTO": "SET",
    "XBX": "XBX", "CAJA": "XBX",
    "XPK": "XPK", "PAQUETE": "XPK",
    "XUN": "XUN", "UNIDAD": "XUN",
}

CATALOGO_MONEDA: dict[str, str] = {
    "MXN": "MXN", "PESOS": "MXN", "PESO MEXICANO": "MXN", "MN": "MXN",
    "USD": "USD", "DOLAR": "USD", "DLS": "USD",
    "EUR": "EUR", "EURO": "EUR",
    "CAD": "CAD", "DOLAR CANADIENSE": "CAD",
    "GBP": "GBP", "LIBRA ESTERLINA": "GBP",
    "JPY": "JPY", "YEN": "JPY",
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


def normalizar_rfc(rfc: str) -> str:
    return _norm_rfc(rfc)


def normalizar_cp(cp: str) -> str:
    if not cp:
        return cp
    return re.sub(r"\D", "", str(cp))[:5]
