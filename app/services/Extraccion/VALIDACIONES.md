# Validaciones y normalizaciones en schema

## Comprobante

| Campo | Normaliza | Valida | Detalle |
|-------|-----------|--------|---------|
| version | No | Si | Regex ^(3.3|4.0)$ |
| tipo_comprobante | No | Si | Regex ^(I|E|P|N|T)$ |
| folio_fiscal | Mayusculas | Si | UUID valido formato 8-4-4-4-12 |
| fecha_emision | Si | Si | Normaliza: dd/mm/aaaa, timezone, Z, milisegundos, fecha sin hora -> YYYY-MM-DDTHH:MM:SS. Valida: formato exacto despues de normalizar |
| sello | No | Si | Regex base64 |
| no_certificado | No | Si | Exactamente 20 digitos |
| metodo_pago | Si | Si | Alias "PAGO EN UNA SOLA EXHIBICION" -> PUE. Valida PUE o PPD |
| forma_pago | Si | No | Alias "EFECTIVO" -> 01, contra CATALOGO_FORMA_PAGO |
| moneda | Si | No | Alias "PESOS" -> MXN, contra CATALOGO_MONEDA |
| exportacion | No | Si | Regex ^0[1-4]$ |
| lugar_expedicion | No | Si | 5 digitos (codigo postal) |
| subtotal / total / iva / retenciones / descuento | No | Si | float, ge=0 |

## Emisor / Receptor

| Campo | Normaliza | Valida | Detalle |
|-------|-----------|--------|---------|
| emisor_rfc | Si | Si | Quita espacios/guiones/underscore, mayusculas, regex RFC. No acepta genericos |
| receptor_rfc | Si | Si | Mismo que emisor pero si acepta XAXX010101000 / XEXX010101000 |
| emisor_nombre / receptor_nombre | Si | No | Mayusculas + strip |
| regimen_fiscal_emisor / regimen_fiscal_receptor | No | Si | 3 digitos |
| domicilio_fiscal_receptor | No | Si | 5 digitos |
| uso_cfdi | No | Si | Regex ^[A-Z][A-Z0-9]\d{1,2}$ |

## Conceptos

| Campo | Normaliza | Valida | Detalle |
|-------|-----------|--------|---------|
| clave_unidad | Si | Si | Normaliza: "PIEZA"/"PZA" -> H87. Valida: existe en CATALOGO_CLAVE_UNIDAD |
| clave_prod_serv | No | Si | 8 digitos. Obligatorio en XML, opcional en OCR. Valida contra catalogo_prodserv_sat.json si existe |
| objeto_imp | No | Si | Regex ^0[1-4]$. Obligatorio por concepto si version == "4.0" |
| cantidad / valor_unitario / importe | No | Si | Obligatorios en XML, opcionales en OCR |
| descuento / iva | No | Si | ge=0 |
| unidad | No | Si | Solo longitud maxima. No se valida contra catalogo |
| Importe = Cantidad x ValorUnitario | No | Si | Tolerancia ±1.0 |
| Descuento <= Importe | No | Si | Por concepto |

## Reglas de negocio a nivel comprobante

- Descuento <= SubTotal
- Si TipoDeComprobante no es "P":
  - MetodoPago = PPD requiere FormaPago = "99"
  - MetodoPago = PUE no puede usar FormaPago = "99"
- Total = SubTotal - Descuento + IVA - Retenciones (tolerancia ±1.0)

## Completitud por tipo de comprobante

Campos obligatorios base: version, tipo_comprobante, folio_fiscal, fecha_emision, lugar_expedicion, metodo_pago, forma_pago, moneda, emisor_rfc, emisor_nombre, regimen_fiscal_emisor, receptor_rfc, receptor_nombre, uso_cfdi, subtotal, total.

Excepciones por tipo:

| Tipo | forma_pago | metodo_pago |
|------|------------|-------------|
| I / E | obligatorio | obligatorio |
| P (Pago) | omitido | omitido |
| T (Traslado) | omitido | omitido |
| N (Nomina) | omitido | obligatorio |

Adicional en CFDI 4.0: exportacion, domicilio_fiscal_receptor, regimen_fiscal_receptor son obligatorios solo si version == "4.0". Cada concepto requiere objeto_imp en 4.0.