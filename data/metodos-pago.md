---
titulo: formas_de_pago_cfdi
fuente: "SAT c_FormaPago Anexo 20 RMF 2022 (DOF 13-01-2022) | descripciones: cfdi.org.mx (no oficial)"
fecha_publicacion_SAT: 13-01-2022
fecha_elaboracion: 26-05-2026
version: 1.1
---

# Catálogo de Formas de Pago en un CFDI

El catálogo de formas de pago SAT se encuentra vigente desde la Segunda Resolución de
Modificaciones de la Miscelánea Fiscal del 2016 y describe los requisitos del CFDI.

---

## Códigos

**01 — Efectivo**
Consiste en el pago realizado con dinero directamente en el establecimiento.

**02 — Cheque Nominativo**
La empresa o persona que paga el servicio emite un cheque a nombre del beneficiado.

**03 — Transferencia Electrónica de Fondos SPEI**
Transferencia electrónica de banco a banco sin importar si son cuentahabiente de la misma institución.

**04 — Tarjeta de Crédito**
El pago se realiza con tarjeta de crédito y regularmente se especifica en la factura la terminación de la tarjeta.

**05 — Monedero Electrónico**
Al ser un monedero autorizado por el SAT, se puede realizar el pago con el monedero electrónico.

**06 — Dinero Electrónico**
El dinero electrónico es el capital almacenado en un hardware.

**08 — Vales de Despensa**
Vales que el contribuyente es acreedor por parte de una empresa.

**12 — Dación en Pago**
Consiste en el pago por medio de un bien sobre lo que se adquirió.

**13 — Pago por Subrogación**
Cuando quien realiza el pago lo está realizando por medio de un derecho de éste, ejemplo: una herencia.

**14 — Pago por Consignación**
Consiste en el pago por medio del tribunal correspondiente. Solo un juez dará finalización a esta acción.

**15 — Condonación**
Cuando la deuda es perdonada.

**17 — Compensación**
Tanto deudor como acreedor tienen la misma obligación de pago.

**23 — Novación**
Se trata de un pago sobre un cambio, es decir, que la obligación inicial cambia.

**24 — Confusión**
Cuando el pago lo realizará el mismo que deberá pagarla.

**25 — Remisión de Deuda**
Si se estipula que el deudor ya no pagará, deberá estar especificado por una remisión de deuda.

**26 — Prescripción o Caducidad**
Cuando después de un determinado tiempo por ley no procede el pago.

**27 — A Satisfacción del Acreedor**
Cuando el acreedor en convenio con el deudor han firmado de no pago.

**28 — Tarjeta de Débito**
Sin importar la institución de la que se trate la tarjeta, ésta siempre deberá tener fondos.

**29 — Tarjeta de Servicios**
Mientras la tarjeta esté emitida por el sistema financiero mexicano.

**30 — Aplicación de Anticipos**
Se trata de pagos anticipados; estos deberán verse reflejados en complemento de factura.

**31 — Intermediario Pagos**
Una tercera persona realizará el pago.

**99 — Por Definir**
Esta opción se especifica cuando al momento de emitir el CFDI de ingreso aún no se conoce la forma de pago real (casos de pago en parcialidades o diferido).

---

## Relación con el Método de Pago

**PUE** *(Pago en Una sola Exhibición)* — se conoce la forma de pago al momento de emitir:
01, 02, 03, 04, 05, 06, 08, 12, 13, 14, 15, 17, 23, 24, 25, 26, 27, 28, 29, 30, 31

**PPD** *(Pago en Parcialidades o Diferido)* — Al emitir la factura original, el pago aún no ha ocurrido, por lo que **obligatoriamente** se debe registrar `FormaPago = '99'`

---

## Nota sobre PPD

Cuando una factura se emite con método de pago PPD:
- El CFDI original (tipo `I`) **debe** llevar `MetodoPago = 'PPD'` y `FormaPago = '99'`.
- Posteriormente, al recibir el pago, se emite un CFDI de tipo `P` con el complemento REP.
- En ese complemento se indica la forma de pago real mediante el campo `FormaDePagoP`, usando la clave correspondiente del catálogo (01, 02, 03, etc.).