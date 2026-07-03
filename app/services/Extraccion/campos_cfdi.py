from __future__ import annotations

CAMPOS_OBLIGATORIOS_CFDI: dict[str, str] = {
    "version":         "Versión (3.3 o 4.0)",
    "folio_fiscal":    "UUID (folio fiscal)",
    "fecha_emision":   "Fecha de emisión",
    "metodo_pago":     "Método de pago",
    "forma_pago":      "Forma de pago",
    "moneda":          "Moneda",
    "emisor_rfc":      "Emisor RFC",
    "emisor_nombre":   "Emisor nombre",
    "receptor_rfc":    "Receptor RFC",
    "receptor_nombre": "Receptor nombre",
    "subtotal":        "SubTotal",
    "total":           "Total",
}

CAMPOS_OBLIGATORIOS_4_0: dict[str, str] = {
    "exportacion":               "Exportacion",
    "lugar_expedicion":          "LugarExpedicion",
    "domicilio_fiscal_receptor": "DomicilioFiscalReceptor",
    "regimen_fiscal_receptor":   "RegimenFiscalReceptor",
    "uso_cfdi":                  "UsoCFDI",
    "regimen_fiscal_emisor":     "RegimenFiscal (Emisor)",
}
