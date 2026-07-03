# Tabla de Precisión por Campo — Parser XML CFDI (Provisional)

**Corpus:** 40 pares XML+JSON  |  **Generado:** 2026-06-29 16:33
**Método:** comparación directa XML (fuente verdad) vs JSON generado por el parser

> Los campos marcados como **N/A** no aplican para ese tipo de comprobante o versión  
> (ej. `exportacion` en CFDI 3.3, `metodo_pago` en tipo P).  
> La columna **Condicional** explica cuándo se espera ausencia.

---

## Comprobante

| Campo | Correctos | Ausentes | Diferentes | N/A | Total | Precisión | Condicional |
|---|---|---|---|---|---|---|---|
| `version` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `folio_fiscal` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `fecha_emision` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `tipo_comprobante` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `lugar_expedicion` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `exportacion` | 38 | 0 | 0 | 2 | 40 | 100% | Solo CFDI 4.0 |
| `no_certificado` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `metodo_pago` | 35 | 0 | 0 | 5 | 40 | 100% | No aplica en tipo P/N |
| `forma_pago` | 35 | 0 | 0 | 5 | 40 | 100% | No aplica en tipo P/N |
| `moneda` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `tipo_cambio` | 5 | 0 | 0 | 35 | 40 | 100% | Solo cuando Moneda ≠ MXN |
| `subtotal` | 40 | 0 | 0 | 0 | 40 | 100% | Condicional en tipo P |
| `descuento` | 21 | 0 | 0 | 19 | 40 | 100% | Opcional |
| `iva` | 30 | 0 | 0 | 10 | 40 | 100% | Solo cuando hay traslados |
| `retenciones` | 8 | 0 | 0 | 32 | 40 | 100% | Solo cuando hay retenciones |
| `total` | 40 | 0 | 0 | 0 | 40 | 100% | Condicional en tipo P |
| `emisor_rfc` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `emisor_nombre` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `regimen_fiscal_emisor` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `receptor_rfc` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `receptor_nombre` | 40 | 0 | 0 | 0 | 40 | 100% |  |
| `domicilio_fiscal_receptor` | 38 | 0 | 0 | 2 | 40 | 100% | Solo CFDI 4.0 |
| `regimen_fiscal_receptor` | 38 | 0 | 0 | 2 | 40 | 100% | Solo CFDI 4.0 |
| `uso_cfdi` | 40 | 0 | 0 | 0 | 40 | 100% |  |

## Conceptos

| Campo | Correctos | Ausentes | Diferentes | N/A | Total | Precisión | Condicional |
|---|---|---|---|---|---|---|---|
| `concepto_descripcion` | 63 | 0 | 0 | 0 | 63 | 100% |  |
| `concepto_clave_prod_serv` | 63 | 0 | 0 | 0 | 63 | 100% |  |
| `concepto_clave_unidad` | 63 | 0 | 0 | 0 | 63 | 100% |  |
| `concepto_unidad` | 63 | 0 | 0 | 0 | 63 | 100% |  |
| `concepto_cantidad` | 63 | 0 | 0 | 0 | 63 | 100% |  |
| `concepto_valor_unitario` | 63 | 0 | 0 | 0 | 63 | 100% |  |
| `concepto_importe` | 63 | 0 | 0 | 0 | 63 | 100% |  |
| `concepto_descuento` | 19 | 0 | 0 | 44 | 63 | 100% | Opcional |
| `concepto_objeto_imp` | 60 | 0 | 0 | 3 | 63 | 100% | Solo CFDI 4.0 |
| `concepto_iva` | 53 | 0 | 0 | 10 | 63 | 100% |  |

---

### Cómo interpretar

- **Correctos**: el valor extraído coincide exactamente con el XML (tolerancia ±0.01 en decimales).
- **Ausentes**: el XML tiene el campo pero el JSON lo tiene en `null`.
- **Diferentes**: ambos tienen valor pero no coinciden.
- **N/A**: el XML no tiene ese campo (es condicional y no aplica en ese documento).
- **Precisión**: `Correctos / (Total - N/A)`.

*Próxima medición: con corpus real H-03 (≥50 documentos anonimizados)*