Recursos XSD del SAT (CFDI)

Documentación de referencia sobre los esquemas XSD incluidos en este repositorio (tomados de phpcfdi/resources-sat-xml: https://github.com/phpcfdi/resources-sat-xml). Son los esquemas oficiales del SAT para validar CFDI 3.3 y 4.0, sus complementos y los catálogos de claves.

Estructura de carpetas

```
resources/
  sat/
    cfdi_combinado.xsd
    cfd/
      3.3/
        cfdv33.xsd
      4/
        cfdv40.xsd
      TimbreFiscalDigital/
        TimbreFiscalDigitalv11.xsd
      Pagos/
        Pagos20.xsd
      nomina/
        nomina12.xsd
      CartaPorte/
        CartaPorte31.xsd
      ComercioExterior/
        ComercioExterior20.xsd
      ine/
        ine10.xsd
        ine11.xsd
      leyendasFiscales/
        leyendasFisc.xsd
      tipoDatos/
        tdCFDI/
          tdCFDI.xsd
      catalogos/
        catCFDI.xsd
        CartaPorte/
          catCartaPorte.xsd
        ComExt/
          catComExt.xsd
        Nomina/
          catNomina.xsd
        Pagos/
          catPagos.xsd
```

cfdi_combinado.xsd importa todos los demás schemas, sirve como punto de entrada único.

Comprobante base

cfdv33.xsd es la versión 3.3 del CFDI, elemento raíz Comprobante. Ya no se usa para timbrar nuevos pero sigue siendo válida para leer CFDI históricos.

cfdv40.xsd es la versión 4.0, vigente desde 2022, mismo elemento raíz Comprobante. Agrega InformacionGlobal y Exportacion, y es más estricta con RFC y domicilio fiscal. Es la que usamos en VISIR.

Complemento obligatorio

TimbreFiscalDigitalv11.xsd es el sello que agrega el PAC al timbrar (UUID, fecha, sellos digitales). Va siempre dentro de Comprobante/Complemento.

Complementos opcionales

Pagos20.xsd aplica en CFDI tipo P, cuando se paga en parcialidades o a crédito.

nomina12.xsd aplica en CFDI tipo N, recibos de nómina.

CartaPorte31.xsd aplica cuando hay traslado de mercancías dentro del país.

ComercioExterior20.xsd aplica en exportaciones definitivas.

ine10.xsd e ine11.xsd se usan para aportaciones a partidos o candidatos reportadas al INE (la 11 es la vigente).

leyendasFisc.xsd se usa cuando aplica alguna leyenda fiscal obligatoria, por ejemplo maquiladoras o IEPS.

Tipos de datos comunes

tdCFDI.xsd define tipos reutilizables (RFC, código postal, año, etc.) que los demás schemas importan para no repetir validaciones de formato.

Catálogos

Estos XSD no describen estructura de XML, solo listan valores válidos (claves SAT) para campos como forma de pago, régimen fiscal, unidad de medida, producto o servicio, etc.

catCFDI.xsd es el catálogo general (5.6 MB), incluye régimen fiscal, uso CFDI, forma de pago, moneda, país y la clave de producto/servicio.

catCartaPorte.xsd (2.3 MB) trae los catálogos propios de Carta Porte.

catComExt.xsd (996 KB) trae los catálogos de Comercio Exterior.

catNomina.xsd (16 KB) trae los catálogos de nómina.

catPagos.xsd (4 KB) es el más pequeño, trae MonedaDR y TipoCadenaPago.

Cómo se relacionan

cfdv40.xsd y cfdv33.xsd importan tdCFDI.xsd para los tipos comunes, y dentro de Complemento pueden traer TimbreFiscalDigitalv11.xsd, Pagos20.xsd, nomina12.xsd, CartaPorte31.xsd, ComercioExterior20.xsd, ine10 o ine11, y leyendasFisc.xsd. Cada complemento referencia su propio catálogo, y casi todos usan también catCFDI.xsd para las claves generales.

Relevancia para VISIR

El pipeline de extracción XML valida contra cfdv40.xsd (y cfdv33.xsd para CFDI antiguos) más TimbreFiscalDigitalv11.xsd. Los campos obligatorios que ya tenemos en campos_cfdi.py y schema.py salen de estos mismos XSD, así que ante cualquier duda sobre formato u obligatoriedad, aquí está la fuente original. catCFDI.xsd es de donde sale c_ClaveProdServ, que usa el modelo de categorización. Si más adelante se agrega soporte a Carta Porte, Pagos o Nómina, los XSD ya están listos aquí para derivar los modelos Pydantic.

Nota final

Estos son los esquemas oficiales del SAT, replicados por phpcfdi/resources-sat-xml para no depender del sitio del SAT. Conviene revisar el repositorio original de vez en cuando, sobre todo catCFDI.xsd y catComExt.xsd, porque el SAT libera nuevas versiones de catálogos con cierta frecuencia.