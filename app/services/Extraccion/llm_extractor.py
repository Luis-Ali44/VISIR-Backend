from __future__ import annotations

_PROMPT_CFDI = """\
Eres un especialista en CFDIs e información fiscal mexicana.
El texto puede contener UNO O VARIOS comprobantes fiscales (CFDIs).
Devuelve ÚNICAMENTE objetos JSON válidos, uno por CFDI encontrado,
separados por salto de línea. Sin explicaciones, sin markdown, sin texto extra.
Si un campo no aparece en el texto usa null.
{nota_uuid}

REGLAS CRÍTICAS PARA LA EXTRACCIÓN:

1. VERSIÓN
   {instruccion_version}

2. EMISOR vs RECEPTOR
   • EMISOR   → quien EXPIDE la factura. RFC y nombre aparecen en el ENCABEZADO,
                ANTES del "FOLIO FISCAL" / UUID.
   • RECEPTOR → quien RECIBE. Sus datos aparecen DESPUÉS del folio fiscal.
   • NUNCA pongas el mismo RFC en emisor y receptor.
   • NUNCA tomes un RFC de la "Cadena Original del SAT" (el bloque que empieza
     con "1|1.1|" o similar) ni del bloque de sellos digitales. Esos contienen
     el identificador del PAC certificador, no el RFC del emisor ni del receptor.
   • Si no encuentras un RFC explícito en el encabezado o en la sección de
     receptor, usa null. No tomes como RFC ningún texto alfanumérico que solo
     coincida en formato si no está claramente etiquetado como RFC del emisor
     o del receptor.

3. folio_fiscal
   Busca el UUID en TODO el documento, incluso dentro de la Cadena Original del SAT.
   Formato obligatorio: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (32 hex + 4 guiones).
   Copia los caracteres tal como aparecen, sin inventar ni completar.

4. Fechas (fecha_emision)
   Formato requerido: YYYY-MM-DDTHH:MM:SS (ISO 8601 sin zona horaria).
   Si el texto trae otro formato, conviértelo. Si no hay hora, usa 00:00:00.

5. metodo_pago → exactamente "PUE" o "PPD".
6. forma_pago  → código de 2 dígitos ("01", "02", "03", "28", "99", etc.).
   Solo extrae el código si aparece EXPLÍCITAMENTE en el texto como número.
7. moneda      → código ISO de 3 letras ("MXN", "USD", "EUR", etc.).
8. Campos numéricos → número sin símbolo de moneda ni comas (ej. 1234.56).
9. RFCs        → sin espacios, sin guiones, en MAYÚSCULAS.
10. NUNCA inventes datos. Si un campo no está visible en el texto → null.
11. descripcion de cada concepto → copia el texto COMPLETO y LITERAL.
    No resumir, no parafrasear. El texto de la tabla puede venir sin columnas
    separadas; corta la descripción ANTES de palabras que pertenezcan a otra
    columna como "Unidad", "Tasa", "IVA", un porcentaje aislado seguido de
    cifras, o un número que claramente sea valor unitario/importe. No agregues
    a la descripción palabras de columnas vecinas (cantidad, unidad, tasa,
    impuesto) aunque estén en la misma línea de texto.

estructura JSON requerida por cada CFDI:

{{
    "version":       null,
    "folio_fiscal":  null,
    "fecha_emision": null,
    "metodo_pago":   null,
    "forma_pago":    null,
    "moneda":        null,
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
    if version:
        instruccion_version = (
            f'La versión pre-detectada por OCR es "{version}". Úsala, '
            'salvo que el propio texto indique claramente otra versión '
            '(p. ej. un literal "Versión 3.3" o "CFDI 3.3" visible).'
        )
    else:
        instruccion_version = (
            'No se pudo pre-detectar la versión por OCR. Búscala tú en el '
            'texto (suele indicarse como "Versión", "CFDI" seguido de '
            '"4.0" o "3.3"). Si tampoco la encuentras, usa null — '
            'NO la inventes ni asumas "4.0" por defecto.'
        )
    return _PROMPT_CFDI.format(
        instruccion_version=instruccion_version,
        nota_uuid=nota_uuid,
        texto=texto_ocr[:max_chars],
    )
