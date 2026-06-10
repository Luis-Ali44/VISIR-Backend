from __future__ import annotations

import re
from typing import Optional

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

CATALOGO_USO_CFDI: dict[str, str] = {
    "G01": "G01", "ADQUISICION DE MERCANCIAS": "G01",
    "G02": "G02", "DEVOLUCIONES, DESCUENTOS O BONIFICACIONES": "G02",
    "G03": "G03", "GASTOS EN GENERAL": "G03",
    "I01": "I01", "CONSTRUCCIONES": "I01",
    "I02": "I02", "MOBILIARIO Y EQUIPO DE OFICINA": "I02",
    "I03": "I03", "EQUIPO DE TRANSPORTE": "I03",
    "I04": "I04", "EQUIPO DE COMPUTO Y ACCESORIOS": "I04",
    "I05": "I05", "DADOS, TROQUELES, MOLDES, MATRICES Y HERRAMENTAL": "I05",
    "I06": "I06", "COMUNICACIONES TELEFONICAS": "I06",
    "I07": "I07", "COMUNICACIONES SATELITALES": "I07",
    "I08": "I08", "OTRA MAQUINARIA Y EQUIPO": "I08",
    "D01": "D01", "HONORARIOS MEDICOS, DENTALES Y GASTOS HOSPITALARIOS": "D01",
    "D02": "D02", "GASTOS MEDICOS POR INCAPACIDAD O DISCAPACIDAD": "D02",
    "D03": "D03", "GASTOS FUNERARIOS": "D03",
    "D04": "D04", "DONATIVOS": "D04",
    "D05": "D05", "INTERESES REALES EFECTIVAMENTE PAGADOS POR CREDITOS HIPOTECARIOS": "D05",
    "D06": "D06", "APORTACIONES VOLUNTARIAS AL SAR": "D06",
    "D07": "D07", "PRIMAS POR SEGUROS DE GASTOS MEDICOS": "D07",
    "D08": "D08", "GASTOS DE TRANSPORTACION ESCOLAR": "D08",
    "D09": "D09", "DEPOSITOS EN CUENTAS PARA EL AHORRO, PRIMAS QUE TENGAN COMO BASE PLANES DE PENSIONES": "D09",
    "D10": "D10", "PAGOS POR SERVICIOS EDUCATIVOS": "D10",
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
    "DAY": "DAY", "DIA": "DAY",
    "GRM": "GRM", "GRAMO": "GRM",
    "MLT": "MLT", "MILILITRO": "MLT",
    "MTK": "MTK", "METRO CUADRADO": "MTK",
    "PR": "PR", "PAR": "PR",
    "SET": "SET", "CONJUNTO": "SET",
    "XBX": "XBX", "CAJA": "XBX",
    "XPK": "XPK", "PAQUETE": "XPK",
    "XUN": "XUN", "UNIDAD": "XUN",
}

CATALOGO_TIPO_COMPROBANTE: dict[str, str] = {
    "I": "I", "INGRESO": "I",
    "E": "E", "EGRESO": "E",
    "T": "T", "TRASLADO": "T",
    "N": "N", "NOMINA": "N",
    "P": "P", "PAGO": "P",
}

CATALOGO_MONEDA: dict[str, str] = {
    "MXN": "MXN", "PESOS": "MXN", "PESO MEXICANO": "MXN", "MN": "MXN",
    "USD": "USD", "DOLAR": "USD", "DLS": "USD",
    "EUR": "EUR", "EURO": "EUR",
    "CAD": "CAD", "DOLAR CANADIENSE": "CAD",
    "GBP": "GBP", "LIBRA ESTERLINA": "GBP",
    "JPY": "JPY", "YEN": "JPY",
}

CATALOGO_EXPORTACION: dict[str, str] = {
    "01": "01", "NO APLICA": "01",
    "02": "02", "DEFINITIVA": "02",
    "03": "03", "TEMPORAL": "03",
    "04": "04", "DEFINITIVA CON CLAVE DISTINTA A A1": "04",
}

CATALOGO_REGIMEN_FISCAL: dict[str, str] = {
    "601": "601", "GENERAL DE LEY PERSONAS MORALES": "601",
    "603": "603", "PERSONAS MORALES CON FINES NO LUCRATIVOS": "603",
    "605": "605", "SUELDOS Y SALARIOS E INGRESOS ASIMILADOS A SALARIOS": "605",
    "606": "606", "ARRENDAMIENTO": "606",
    "607": "607", "REGIMEN DE ENAJENACION O ADQUISICION DE BIENES": "607",
    "608": "608", "DEMAS INGRESOS": "608",
    "610": "610", "RESIDENTES EN EL EXTRANJERO SIN ESTABLECIMIENTO PERMANENTE EN MEXICO": "610",
    "611": "611", "INGRESOS POR DIVIDENDOS": "611",
    "612": "612", "PERSONAS FISICAS CON ACTIVIDADES EMPRESARIALES Y PROFESIONALES": "612",
    "614": "614", "INGRESOS POR INTERESES": "614",
    "615": "615", "REGIMEN DE LOS INGRESOS POR OBTENCION DE PREMIOS": "615",
    "616": "616", "SIN OBLIGACIONES FISCALES": "616",
    "620": "620", "SOCIEDADES COOPERATIVAS DE PRODUCCION QUE OPTAN POR DIFERIR SUS INGRESOS": "620",
    "621": "621", "INCORPORACION FISCAL": "621",
    "622": "622", "ACTIVIDADES AGRICOLAS, GANADERAS, SILVICOLAS Y PESQUERAS": "622",
    "623": "623", "OPCIONAL PARA GRUPOS DE SOCIEDADES": "623",
    "624": "624", "COORDINADOS": "624",
    "625": "625", "REGIMEN DE LAS ACTIVIDADES EMPRESARIALES CON INGRESOS A TRAVES DE PLATAFORMAS TECNOLOGICAS": "625",
    "626": "626", "REGIMEN SIMPLIFICADO DE CONFIANZA": "626",
    "628": "628", "HIDROCARBUROS": "628",
    "629": "629", "DE LOS REGIMENES FISCALES PREFERENTES Y DE LAS EMPRESAS MULTINACIONALES": "629",
    "630": "630", "ENAJENACION DE ACCIONES EN BOLSA DE VALORES": "630",
}


def normalizar_catalogo(valor: Optional[str], catalogo: dict[str, str]) -> Optional[str]:
    """Normaliza un valor usando el catálogo dado (expande abreviaturas previamente)."""
    if not valor:
        return valor
    clave = expandir_abreviaturas(str(valor).strip()).upper()
    return catalogo.get(clave, valor)


def _norm_rfc(rfc: str) -> str:
    """Elimina espacios y guiones de un RFC."""
    return re.sub(r"[\s\-_]", "", rfc.upper().strip())


def validar_digito_rfc(rfc: str) -> bool:
    """Valida la estructura de un RFC (Persona Moral o Física)."""
    rfc = _norm_rfc(rfc)
    return bool(re.match(r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$", rfc))


def normalizar_rfc(rfc: str) -> str:
    """Devuelve el RFC normalizado (sin espacios, en mayúsculas)."""
    return _norm_rfc(rfc)


def normalizar_cp(cp: str) -> str:
    """Limpia un código postal (solo dígitos)."""
    if not cp:
        return cp
    return re.sub(r"\D", "", str(cp))[:5]