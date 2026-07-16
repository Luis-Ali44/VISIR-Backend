from __future__ import annotations

CAMPOS_OBLIGATORIOS_CFDI: dict[str, str] = {
    "version": "Versión (3.3 o 4.0)",
    "tipo_comprobante": "TipoDeComprobante",
    "folio_fiscal": "UUID (folio fiscal)",
    "fecha_emision": "Fecha de emisión",
    "metodo_pago": "Método de pago",
    "forma_pago": "Forma de pago",
    "moneda": "Moneda",
    "lugar_expedicion": "LugarExpedicion",
    "emisor_rfc": "Emisor RFC",
    "emisor_nombre": "Emisor nombre",
    "regimen_fiscal_emisor": "RegimenFiscal (Emisor)",
    "receptor_rfc": "Receptor RFC",
    "receptor_nombre": "Receptor nombre",
    "uso_cfdi": "UsoCFDI",
    "subtotal": "SubTotal",
    "total": "Total",
}

CAMPOS_OBLIGATORIOS_4_0: dict[str, str] = {
    "exportacion": "Exportacion",
    "domicilio_fiscal_receptor": "DomicilioFiscalReceptor",
    "regimen_fiscal_receptor": "RegimenFiscalReceptor",
}
