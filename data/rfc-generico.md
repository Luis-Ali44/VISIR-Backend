---
titulo: rfc_generico_cfdi
fuente: SAT — Regla 2.7.1.23 de la Resolución Miscelánea Fiscal 2025
fecha_publicacion_SAT: 30-12-2024
fecha_consulta: 26-05-2026
version: 1.0
---

# RFC Genérico en el CFDI 4.0

El RFC genérico es una clave predefinida y oficial que el SAT permite usar cuando el receptor de un CFDI no cuenta con RFC o es extranjero sin registro fiscal en México. No requiere trámite ni registro: se captura directamente en el campo RFC del receptor al momento de emitir la factura.

El SAT define exactamente dos RFC genéricos. No existe un tercero ni variantes propias.

---

## XAXX010101000 — Público en General

Se utiliza cuando el receptor es una persona física o moral de nacionalidad mexicana que no cuenta con RFC, o cuando el cliente no proporciona sus datos fiscales al momento de la transacción.

Cuando se usa este RFC, el campo Nombre o Razón Social debe registrarse obligatoriamente como `PUBLICO EN GENERAL` (en mayúsculas, sin acentos). El régimen fiscal del receptor debe ser `616 — Sin obligaciones fiscales` y el uso del CFDI debe ser `S01 — Sin efectos fiscales`. El código postal del receptor se captura igual al lugar de expedición del emisor.

Casos de uso: ventas de mostrador donde el cliente no solicita factura, negocios nuevos aún no dados de alta ante el SAT, operaciones de comercio minorista con público no identificado.

### Factura Global

Cuando se utiliza XAXX010101000, la operación se considera realizada con el público en general conforme a la regla 2.7.1.46 de la RMF. En estos casos, el emisor puede agrupar todas las ventas del periodo en un solo CFDI llamado **factura global**, habilitando el nodo de Información Global con la periodicidad, los meses y el año que correspondan.

---

## XEXX010101000 — Extranjeros

Se utiliza cuando el receptor es residente en el extranjero sin inscripción en el RFC mexicano. A diferencia del RFC genérico nacional, con este RFC sí se debe registrar el nombre real del receptor en el campo correspondiente, ya que el SAT necesita identificar a quién se le vendió aunque no tenga RFC mexicano.

El régimen fiscal del receptor debe ser igualmente `616 — Sin obligaciones fiscales` y el uso del CFDI `S01 — Sin efectos fiscales`. Adicionalmente, cuando la operación involucra exportación de mercancías, el campo `Exportacion` del comprobante debe indicar `02` (Definitiva) o `03` (Temporal) según corresponda; si además hay traslado físico de bienes, se requiere el complemento Carta Porte; y si el pago se recibe en moneda extranjera, debe registrarse el tipo de cambio del día.

Casos de uso: ventas a turistas extranjeros que solicitan factura para devolución de IVA, exportación de bienes a clientes sin domicilio fiscal en México, servicios prestados a empresas extranjeras sin establecimiento permanente en territorio nacional.

---

## Restricciones comunes a ambos RFC genéricos

No es válido usar un RFC genérico cuando el receptor sí cuenta con RFC mexicano: el PAC rechazará el CFDI si se detecta la inconsistencia. Tampoco es posible combinar estos RFC con usos de CFDI distintos a `S01` ni con regímenes fiscales distintos a `616`, ya que esas combinaciones presuponen un receptor identificado con obligaciones fiscales reales.
