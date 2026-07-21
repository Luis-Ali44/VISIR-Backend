---
titulo: complementos_cfdi_comunes
fuente: SAT CFDI 4.0 - Complementos publicados en portal SAT
fecha_publicacion_sat: 2025-12-31 
fecha_consulta: 26-05-2026
version: 1.0
---

# Complementos Comunes del CFDI 4.0

Un complemento es un nodo adicional que se incorpora al CFDI cuando una operación requiere información fiscal más allá del estándar base. Cada complemento tiene versión propia y es validado por el SAT durante el timbrado.

---

## Recepción de Pagos (REP) — v2.0

También conocido como Recibo Electrónico de Pago. Se incorpora a un CFDI de tipo **P**.

Se emite cuando una factura de ingreso fue generada con método de pago PPD (Pago en Parcialidades o Diferido) y el pago se recibe en una fecha posterior a la emisión, ya sea de forma total o parcial. Debe emitirse a más tardar el **quinto día natural** del mes siguiente al que se recibió el pago (Regla  2.7.1.32 RMF 2026).

Casos de uso: pago parcial de una factura, liquidación total diferida, abonos en múltiples fechas.

---

## Nómina — v1.2 rev. E

Se incorpora a un CFDI de tipo **N** (Nómina).

Es obligatorio para todos los patrones que realicen pagos a trabajadores por concepto de salarios y prestaciones laborales. Permite al SAT validar percepciones, deducciones, retenciones y otros pagos conforme al régimen de contratación del trabajador.

Casos de uso: pago de sueldo mensual o quincenal, aguinaldo, prima vacacional, bonos, participación de utilidades (PTU).

---

## Carta Porte — v3.1

Se incorpora a un CFDI de tipo **I** (cuando el transportista presta el servicio) o de tipo **T** (cuando el propietario traslada su propia mercancía).

Es obligatorio para acreditar el traslado legal de mercancías por territorio nacional, incluyendo vías terrestres federales, aéreas, marítimas y ferroviarias. Sin este complemento, la mercancía en tránsito no tiene respaldo fiscal ante una verificación.

Casos de uso: transporte de mercancías por carretera federal, traslado entre sucursales, envío de productos a clientes, logística de última milla.

---

## Comercio Exterior — v2.0

Se incorpora a un CFDI de tipo **I** cuando la operación involucra exportación definitiva de mercancías con pedimento A1.

Es obligatorio para personas físicas y morales que realicen enajenación de mercancías al extranjero. Permite identificar exportadores, claves arancelarias, incoterms y valores en aduana conforme a las regulaciones fiscales y aduaneras de México.

Casos de uso: exportación definitiva de bienes, operaciones con pedimento A1, ventas al extranjero con transferencia de propiedad.

---

## INE — v1.1

Se incorpora a cualquier CFDI emitido a favor de partidos políticos,
coaliciones o asociaciones civiles de aspirantes y candidatos independientes.

Es obligatorio para todos los contribuyentes que vendan, arrienden o presten servicios a estas entidades durante procesos ordinarios, de precampaña o campaña. Su objetivo es garantizar la transparencia en el uso de recursos públicos destinados a gastos electorales, conforme al artículo 41, base V, apartado B de la Constitución y el artículo 46 del Reglamento de Fiscalización del INE.

Casos de uso: venta de propaganda y publicidad, contratación de espectáculos o grupos musicales, bienes y servicios para eventos de campaña, operación ordinaria de partidos políticos.

---

## Leyendas Fiscales — v1.0

Se incorpora a cualquier tipo de CFDI cuando una disposición legal obliga al emisor a incluir texto específico que no está contemplado en el estándar base del comprobante.

Permite registrar la ley o resolución que regula la leyenda, el número de artículo o regla aplicable, y el texto de la leyenda en sí. Es especialmente común en operaciones de empresas con programa IMMEX, donde se deben declarar transferencias virtuales entre empresas maquiladoras.

Casos de uso: exportaciones temporales y virtuales bajo programa IMMEX, operaciones con tratamiento fiscal especial, estímulos o beneficios fiscales que deben constar en el comprobante.

---

## Otros Derechos e Impuestos — v1.0

Se incorpora a un CFDI cuando en la operación se generan impuestos o derechos de carácter local (estatal o municipal) que deben desglosarse en la factura, adicionales a los impuestos federales estándar (IVA, IEPS, ISR).

El SAT lo define como el complemento para incluir información de derechos o impuestos locales retenidos o trasladados en la factura.

Casos de uso: servicios de hospedaje sujetos al impuesto sobre alojamiento, prestación de servicios gravados con impuestos estatales, operaciones inmobiliarias con contribuciones de mejoras, actividades con cargas tributarias municipales específicas.