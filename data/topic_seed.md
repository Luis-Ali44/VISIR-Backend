---
titulo: topic_seed_corpus_fiscal
fuente: corpus actual de la carpeta data/
fecha_creacion: 2026-05-29
version: 1.0
proposito: servir como semilla semantica para ponderar la relevancia de nuevos documentos mediante embeddings
---

# Topic Seed del Corpus Fiscal

Este documento resume los temas que deben considerarse de mayor relevancia dentro del corpus fiscal actual. Se usa como referencia semantica para comparar documentos nuevos y asignarles una importancia relativa basada en contenido, no solo en nombre de archivo.

El objetivo es cubrir el corpus completo que vive en `data/`, tomando como referencia tanto los PDF como los archivos Markdown de apoyo. Los archivos Markdown no se ingieren como seed, pero si se usan como fuente de informacion para perfilar el dominio, las reglas de negocio y los temas clave.

## Mapa general del corpus

El corpus actual agrupa cuatro bloques grandes de informacion:

- Guia de llenado CFDI 4.0 y estructura del Anexo 20.
- Complementos de CFDI y operaciones relacionadas con pagos, nomina y traslado.
- Reglas fiscales normativas 2026, criterios RMF e impuestos.
- Conceptos de apoyo como RFC generico, tipos de comprobante, formas de pago y personas contribuyentes.

Estos bloques son los que deben dominar la comparacion semantica entre documentos nuevos.

## Prioridad 5 - Guía de llenado CFDI 4.0 y Anexo 20

Temas base del sistema: estructura del CFDI, nodo Comprobante, nodo Receptor, UsoCFDI, MetodoPago, FormaPago, Exportacion, regimen fiscal, tipo de comprobante, reglas de validacion y campos obligatorios.

Estos temas son centrales porque concentran la logica de emision, validacion y timbrado de comprobantes fiscales digitales.

### Archivo fuente principal

- `Anexo_20_Guia_Llenado_CFDI_v4_v2.pdf`

### Relacion con documentos de apoyo

- `tipos-comprobante.md`
- `metodos-pago.md`
- `rfc-generico.md`
- `complementos.md`

### Terminos clave de comparacion

CFDI 4.0, Anexo 20, comprobante, receptor, emisor, uso del CFDI, regimen fiscal, domicilio fiscal, exportacion, metodo de pago, forma de pago, complemento, validacion, nodo, catalogo, timbrado, PAC, factura, cancelacion, relacion de CFDI.

## Prioridad 5 - Complementos del CFDI y operaciones de pago

Incluye Complemento de Recepcion de Pagos, complemento de Nomina, Carta Porte, Comercio Exterior, INE y Leyendas Fiscales.

Tambien cubre casos de uso relacionados con pagos diferidos, anticipos, liquidaciones parciales y facturacion asociada a operaciones especiales.

### Archivo fuente principal

- `complementos.md`

### Temas que deben pesar mucho en la similitud

Recepcion de Pagos, REP, pago parcial, pago diferido, anticipo, complemento de nomina, salario, prestaciones, Carta Porte, traslado de mercancias, comercio exterior, exportacion definitiva, INE, fiscalizacion electoral, leyendas fiscales, operaciones especiales, informacion complementaria, validacion SAT.

### Relacion con documentos del corpus

- La seccion de pagos dialoga con `metodos-pago.md`.
- La seccion de recepcion de pagos conecta con `Anexo_20_Guia_Llenado_CFDI_v4_v2.pdf`.
- La seccion de traslado y transporte se vincula con `Anexo_20_Guia_Llenado_CFDI_v4_v2.pdf`.

## Prioridad 4 - RFC generico y reglas del receptor

Incluye XAXX010101000, XEXX010101000, Publico en General, extranjeros sin RFC mexicano, regimen 616, S01, factura global y restricciones de uso.

Este bloque es importante para validar la identificacion del receptor y la forma correcta de emitir un CFDI cuando no existe RFC mexicano.

### Archivo fuente principal

- `rfc-generico.md`

### Terminos clave de comparacion

RFC generico, XAXX010101000, XEXX010101000, publico en general, extranjero, regimen 616, S01, sin efectos fiscales, factura global, nombre o razon social, codigo postal, exportacion, receptor, validacion de consistencia, restricciones de uso.

### Relacion con el resto del corpus

- Este tema depende directamente de las reglas del CFDI del Anexo 20.
- Tambien cruza con operaciones de exportacion y con complementos cuando el receptor o la operacion requieren informacion adicional.

## Prioridad 4 - Tipos de comprobante y clasificacion de operaciones

Incluye comprobantes de Ingreso, Egreso, Traslado, Pago y Nomina, junto con sus casos de uso y su relacion con pagos parciales, devoluciones, transporte y salarios.

Este tema ayuda a distinguir la naturaleza fiscal de la operacion y el tipo de comprobante que corresponde emitir.

### Archivo fuente principal

- `tipos-comprobante.md`

### Terminos clave de comparacion

Ingreso, Egreso, Traslado, Pago, Nomina, devolucion, descuento, bonificacion, transporte, pago parcial, liquidacion, complemento de pagos, salario, prestacion laboral, naturaleza del comprobante.

### Relacion con otros documentos

- Se conecta con `complementos.md` cuando el tipo de comprobante requiere un complemento.
- Se conecta con `metodos-pago.md` cuando la naturaleza del pago influye en la emision del comprobante.

## Prioridad 3 - Criterios normativos y disposiciones fiscales

Incluye criterios normativos RMF 2026, reglas de la resolucion miscelanea, validaciones fiscales, obligaciones del contribuyente y criterios de aplicacion.

Sirve como base normativa para interpretar las reglas de emision y los efectos de cumplimiento fiscal.

### Archivos fuente principales

- `Anexo_7_RMF2026-09012026_limpio.pdf`

### Temas clave de comparacion

Reglas miscelaneas, criterios normativos, RMF 2026, obligacion fiscal, validacion, cumplimiento, aplicacion de reglas, interpretacion normativa, autoridad fiscal, procedimiento, disposicion aplicable, referencia juridica.

### Relacion con temas operativos

- Este bloque da contexto normativo a CFDI, complementos y pagos.
- Debe capturar documentos que expliquen el por que de una regla, no solo su campo tecnico.

## Prioridad 3 - Personas contribuyentes, tarifas ISR y referencias de apoyo

Incluye el ABC de personas contribuyentes, tarifas ISR 2026, clasificacion general de contribuyentes y referencias complementarias.

Se utiliza como contexto de apoyo para comparaciones semanticas cuando un documento no pertenece directamente a la facturacion CFDI pero sigue dentro del dominio fiscal.

### Archivos fuente principales

- `Anexo_8_RMF2026-09012026_limpio.pdf`
- `El_ABC_personas_contribuyentes_v2.pdf`

### Temas clave de comparacion

Personas contribuyentes, obligaciones, tarifas ISR, calculo de impuesto, clasificacion de contribuyentes, regimen fiscal, definiciones generales, guia de referencia, obligaciones formales, retenciones, cumplimiento.

### Relacion con el corpus principal

- Estos documentos no siempre son tan operativos como el Anexo 20, pero si aportan contexto normativo y fiscal de fondo.
- Deben subir la relevancia de documentos relacionados con obligaciones, calculos y clasificacion fiscal.

## Prioridad 4 - Formas de pago y anticipos

Este bloque merece alta relevancia porque conecta la emision del CFDI con la forma real de cobro, la conciliacion de pagos y el tratamiento de anticipos.

### Archivo fuente principal

- `metodos-pago.md`

### Terminos clave de comparacion

Forma de pago, metodo de pago, efectivo, transferencia, cheque, tarjeta, anticipos, compensacion, dacion en pago, subrogacion, condonacion, novacion, remision de deuda, aplicacion de anticipos, pago por consignacion.

### Relacion con CFDI

- Se cruza directamente con UsoCFDI, MetodoPago y complemento de pagos.
- Debe elevar la relevancia de documentos que hablen de cobro, liquidacion, parcialidades y conciliacion de ingresos.

## Prioridad 4 - Complementos operativos y escenarios especiales

Este bloque captura las operaciones especiales que no siempre son parte del flujo basico, pero que siguen siendo muy importantes en un entorno fiscal real.

### Temas integrados

- Carta Porte y traslado de mercancias.
- Comercio exterior y exportacion definitiva.
- Nomina y pagos a trabajadores.
- INE y gastos electorales.
- Leyendas fiscales y textos obligatorios.

### Relacion con documentos de referencia

- `complementos.md`
- `Anexo_20_Guia_Llenado_CFDI_v4_v2.pdf`

## Prioridad 3 - Operacion fiscal general y contexto de consulta

Este nivel agrupa documentos que no siempre son el centro del timbrado, pero ayudan a responder consultas sobre cumplimiento, definicion de conceptos y reglas generales del dominio fiscal.

### Archivos fuente

- `Anexo_7_RMF2026-09012026_limpio.pdf`
- `Anexo_8_RMF2026-09012026_limpio.pdf`
- `El_ABC_personas_contribuyentes_v2.pdf`

### Temas clave de comparacion

Consulta fiscal, criterio normativo, interpretacion, regla, disposicion, tarifa, ISR, obligacion, contribuyente, guia de referencia, definicion operativa, contexto fiscal.

## Lectura para modelos de embedding nuevos

Cuando se cambie el modelo de embeddings, este archivo debe seguir sirviendo como referencia porque no depende de una representacion numerica fija, sino de semantica de dominio.

La comparacion debe priorizar:

1. Coincidencia con CFDI 4.0 y Anexo 20.
2. Coincidencia con complementos, pagos y tipos de comprobante.
3. Coincidencia con RFC generico y reglas del receptor.
4. Coincidencia con criterios normativos, RMF, ISR y referencias de apoyo.

La semilla debe favorecer documentos que expliquen reglas concretas, casos de uso, validaciones, restricciones y relaciones entre campos.
