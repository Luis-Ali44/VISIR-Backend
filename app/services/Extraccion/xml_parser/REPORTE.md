# Cobertura Actual del Parser CFDI

## CFDI Base

### Casos cubiertos

#### Comprobante

* Version
* Serie
* Folio
* Fecha
* TipoDeComprobante
* Moneda
* TipoCambio
* SubTotal
* Descuento
* Total
* LugarExpedicion
* Exportacion
* NoCertificado
* MetodoPago
* FormaPago

#### Emisor

* RFC
* Nombre
* RegimenFiscal

#### Receptor

* RFC
* Nombre
* UsoCFDI
* RegimenFiscalReceptor
* DomicilioFiscalReceptor

#### Timbre Fiscal Digital

* UUID
* FechaTimbrado
* RfcProvCertif
* NoCertificadoSAT

#### Impuestos Globales

* TotalImpuestosTrasladados
* TotalImpuestosRetenidos

#### Conceptos

* ClaveProdServ
* Descripcion
* Cantidad
* ClaveUnidad
* Unidad
* ValorUnitario
* Importe
* Descuento
* IVA trasladado por concepto

### Casos pendientes

#### Comprobante

* Certificado
* Sello

#### Timbre Fiscal Digital

* Version
* SelloCFD
* SelloSAT

#### Conceptos

* NoIdentificacion
* ObjetoImp
* Impuestos completos por concepto (ISR, IEPS, retenciones múltiples)
* Traslados múltiples por concepto
* Retenciones por concepto

# Complemento Carta Porte 3.1

## Casos cubiertos

### Carta Porte

* Version
* IdCCP
* TranspInternac
* EntradaSalidaMerc
* PaisOrigenDestino
* ViaEntradaSalida
* TotalDistRec
* RegistroISTMO
* UbicacionPoloOrigen
* UbicacionPoloDestino

### Regímenes Aduaneros

* RegimenAduanero

### Ubicaciones

* TipoUbicacion
* IDUbicacion
* RFCRemitenteDestinatario
* NombreRemitenteDestinatario
* NumRegIdTrib
* ResidenciaFiscal
* FechaHoraSalidaLlegada
* DistanciaRecorrida

### Domicilios

* Calle
* NumeroExterior
* NumeroInterior
* Colonia
* Localidad
* Municipio
* Estado
* Pais
* CodigoPostal
* Referencia

### Mercancias

* BienesTransp
* ClaveSTCC
* Descripcion
* Cantidad
* ClaveUnidad
* Unidad
* Dimensiones
* MaterialPeligroso
* CveMaterialPeligroso
* Embalaje
* DescripEmbalaje
* SectorCOFEPRIS
* PesoEnKg
* ValorMercancia
* Moneda
* FraccionArancelaria
* UUIDComercioExt
* TipoMateria
* DescripcionMateria

### Documentacion Aduanera

* TipoDocumento
* NumPedimento
* IdentDocAduanero
* RFCImpo

### Guias de Identificacion

* NumeroGuiaIdentificacion
* DescripGuiaIdentificacion
* PesoGuiaIdentificacion

### Cantidad Transporta

* Cantidad
* IDOrigen
* IDDestino
* CvesTransporte

### Detalle Mercancia

* UnidadPesoMerc
* PesoBruto
* PesoNeto
* PesoTara
* NumPiezas

### Autotransporte

* PermSCT
* NumPermisoSCT

### Identificacion Vehicular

* ConfigVehicular
* PesoBrutoVehicular
* PlacaVM
* AnioModeloVM

### Seguros

* AseguraRespCivil
* PolizaRespCivil
* AseguraMedAmbiente
* PolizaMedAmbiente
* AseguraCarga
* PolizaCarga
* PrimaSeguro

### Remolques

* SubTipoRem
* Placa

### Figura Transporte

* TipoFigura
* RFCFigura
* NumLicencia
* NombreFigura
* NumRegIdTribFigura
* ResidenciaFiscalFigura

### Partes Transporte

* ParteTransporte

## Casos pendientes

### Mercancias COFEPRIS

No implementados:

* NombreIngredienteActivo
* NomQuimico
* DenominacionGenericaProd
* DenominacionDistintivaProd
* Fabricante
* FechaCaducidad
* LoteMedicamento
* FormaFarmaceutica
* CondicionesEspTransp
* RegistroSanitarioFolioAutorizacion
* PermisoImportacion
* FolioImpoVUCEM
* NumCAS
* RazonSocialEmpImp
* NumRegSanPlagCOFEPRIS
* DatosFabricante
* DatosFormulador
* DatosMaquilador
* UsoAutorizado

### Transporte Marítimo

* Sin validar con XML reales
* Cobertura parcial o pendiente de pruebas

### Transporte Aéreo

* Sin validar con XML reales
* Cobertura parcial o pendiente de pruebas

### Transporte Ferroviario

* Sin validar con XML reales
* Cobertura parcial o pendiente de pruebas

# Complemento Comercio Exterior

## Casos cubiertos

### Comercio Exterior

* Version
* MotivoTraslado
* ClaveDePedimento
* CertificadoOrigen
* NumCertificadoOrigen
* NumeroExportadorConfiable
* Incoterm
* Observaciones
* TipoCambioUSD
* TotalUSD

### Emisor

* CURP
* Domicilio

### Receptor

* NumRegIdTrib
* Domicilio

### Propietarios

* NumRegIdTrib
* ResidenciaFiscal

### Destinatarios

* NumRegIdTrib
* Nombre
* Domicilios

### Mercancias

* NoIdentificacion
* FraccionArancelaria
* CantidadAduana
* UnidadAduana
* ValorUnitarioAduana
* ValorDolares

### Descripciones Específicas

* Marca
* Modelo
* SubModelo
* NumeroSerie

## Casos pendientes

* Validación con casos reales complejos
* Múltiples destinatarios internacionales
* Casos especiales de exportación temporal
* Cobertura completa de todas las variantes SAT

# Complemento Nómina 1.2

## Casos cubiertos

### Nómina

* Datos generales de nómina

### Emisor

* CURP
* RegistroPatronal
* RfcPatronOrigen
* EntidadSNCF

### Receptor

* CURP
* TipoContrato
* TipoRegimen
* NumEmpleado
* Departamento
* Puesto
* TipoJornada
* PeriodicidadPago
* Banco
* CuentaBancaria
* SalarioBaseCotApor
* SalarioDiarioIntegrado
* ClaveEntFed
* NumSeguridadSocial
* FechaInicioRelLaboral
* Antigüedad
* RiesgoPuesto
* Sindicalizado
* SubContratacion

### Percepciones

* Percepciones
* HorasExtra
* JubilacionPensionRetiro
* SeparacionIndemnizacion

### Deducciones

* Deducciones

### Otros Pagos

* OtrosPagos

### Incapacidades

* Incapacidades

## Casos pendientes

* Validación exhaustiva con nóminas reales
* Cobertura completa de todos los tipos SAT
* Casos SNCF complejos

# Complemento Pagos 2.0

## Casos cubiertos

### Totales

* TotalRetencionesIVA
* TotalRetencionesISR
* TotalRetencionesIEPS
* TotalTrasladosBaseIVA16
* TotalTrasladosImpuestoIVA16
* TotalTrasladosBaseIVA8
* TotalTrasladosImpuestoIVA8
* TotalTrasladosBaseIVA0
* TotalTrasladosImpuestoIVA0
* TotalTrasladosBaseIVAExento
* MontoTotalPagos

### Pago

* FechaPago
* FormaDePagoP
* MonedaP
* TipoCambioP
* Monto

### Doctos Relacionados

* IdDocumento
* Serie
* Folio
* MonedaDR
* EquivalenciaDR
* NumParcialidad
* ImpSaldoAnt
* ImpPagado
* ImpSaldoInsoluto
* ObjetoImpDR

### ImpuestosDR

* TrasladosDR
* RetencionesDR

### ImpuestosP

* TrasladosP
* RetencionesP

## Casos pendientes

* Validación con REP complejos
* Múltiples monedas
* Casos bancarios especiales

# Complemento INE

## Casos cubiertos

### INE

* Version
* TipoProceso
* TipoComite

### Entidad

* ClaveEntidad
* Ambito

### Contabilidad

* IdContabilidad

## Casos pendientes

* Validación con XML reales de campañas y partidos

# Complemento Leyendas Fiscales

## Casos cubiertos

### Leyendas Fiscales

* Version

### Leyenda

* DisposicionFiscal
* Norma
* TextoLeyenda

## Casos pendientes

* Validación con múltiples leyendas

# Addenda

## Casos cubiertos

* Extracción completa del nodo Addenda en formato genérico

## Casos pendientes

* Parsers específicos por proveedor
* Addendas comerciales propietarias


# Resumen de Pruebas 

| Archivo | Campos XML | Implementados | XML Correctos | Cobertura | Errores |
|----------|-----------:|--------------:|--------------:|----------:|---------:|
| prueba_addenda | 75 | 46 | 46 | 61.33% | 0 |
| prueba_carta_porte_autotransporte | 131 | 120 | 120 | 91.60% | 0 |
| prueba_carta_porte_nacional | 118 | 106 | 106 | 89.83% | 0 |
| pruebas_comercio_exterior_ingreso | 145 | 148 | 145 | 100.00% | 0 |
| pruebas_comercio_exterior_receptorExtranjero | 88 | 68 | 68 | 77.27% | 0 |
| prueba_ine | 44 | 44 | 44 | 100.00% | 0 |
| prueba_leyendas_fiscales | 43 | 42 | 42 | 97.67% | 0 |
| prueba_nomina_horas_extras | 89 | 93 | 89 | 100.00% | 0 |
| prueba_nomina_ordinaria | 83 | 89 | 83 | 100.00% | 0 |
| prueba_pagos_extranjero | 61 | 82 | 61 | 100.00% | 0 |
| prueba_pago_con_IVA_exento | 67 | 92 | 67 | 100.00% | 0 |
| prueba_pago_dos_complementos | 132 | 178 | 132 | 100.00% | 0 |
| cfdi_33_egreso_029 | 49 | 35 | 35 | 71.43% | 0 |
| cfdi_33_egreso_030 | 63 | 44 | 44 | 69.84% | 0 |
| cfdi_40_egreso_026 | 51 | 38 | 38 | 74.51% | 0 |
| cfdi_40_egreso_027 | 67 | 47 | 47 | 70.15% | 0 |
| cfdi_40_egreso_028 | 54 | 38 | 38 | 70.37% | 0 |
| cfdi_v40_addenda_021 | 54 | 41 | 41 | 75.93% | 0 |
| cfdi_v40_addenda_022 | 76 | 50 | 50 | 65.79% | 0 |
| cfdi_v40_addenda_023 | 89 | 59 | 59 | 66.29% | 0 |
| cfdi_v40_addenda_024 | 89 | 59 | 59 | 66.29% | 0 |
| cfdi_v40_addenda_025 | 69 | 50 | 50 | 72.46% | 0 |
| cfdi_40_mxn_ingreso_transporte_013 | 99 | 101 | 99 | 100.00% | 0 |
| cfdi_40_mxn_ingreso_transporte_014 | 90 | 92 | 90 | 100.00% | 0 |
| cfdi_40_mxn_ingreso_transporte_015 | 89 | 92 | 89 | 100.00% | 0 |
| cfdi_v40_comercio_ext_usd_016 | 104 | 81 | 81 | 77.88% | 0 |
| cfdi_v40_comercio_ext_usd_017 | 108 | 81 | 81 | 75.00% | 0 |
| cfdi_v40_comercio_ext_usd_018 | 108 | 81 | 81 | 75.00% | 0 |
| cfdi_v40_comercio_ext_usd_019 | 107 | 81 | 81 | 75.70% | 0 |
| cfdi_v40_comercio_ext_usd_020 | 87 | 66 | 66 | 75.86% | 0 |
| cfdi_40_mxn_ingreso_construccion_009 | 64 | 47 | 47 | 73.44% | 0 |
| cfdi_40_mxn_ingreso_construccion_010 | 89 | 56 | 56 | 62.92% | 0 |
| cfdi_40_mxn_ingreso_restaurante_007 | 68 | 47 | 47 | 69.12% | 0 |
| cfdi_40_mxn_ingreso_restaurante_008 | 69 | 47 | 47 | 68.12% | 0 |
| cfdi_40_mxn_ingreso_salud_011 | 90 | 56 | 56 | 62.22% | 0 |
| cfdi_40_mxn_ingreso_salud_012 | 66 | 47 | 47 | 71.21% | 0 |
| cfdi_40_eur_ingreso_005 | 67 | 47 | 47 | 70.15% | 0 |
| cfdi_40_eur_ingreso_006 | 91 | 56 | 56 | 61.54% | 0 |
| cfdi_40_mxn_ingreso_001 | 91 | 56 | 56 | 61.54% | 0 |
| cfdi_40_mxn_ingreso_002 | 52 | 38 | 38 | 73.08% | 0 |
| cfdi_40_usd_ingreso_003 | 52 | 38 | 38 | 73.08% | 0 |
| cfdi_40_usd_ingreso_004 | 74 | 47 | 47 | 63.51% | 0 |
| cfdi_v40_nomina_036 | 83 | 86 | 83 | 100.00% | 0 |
| cfdi_v40_nomina_037 | 83 | 86 | 83 | 100.00% | 0 |
| cfdi_v40_nomina_038 | 83 | 86 | 83 | 100.00% | 0 |
| cfdi_v40_nomina_039 | 83 | 86 | 83 | 100.00% | 0 |
| cfdi_v40_nomina_040 | 83 | 86 | 83 | 100.00% | 0 |
| cfdi_v40_pago_031 | 94 | 114 | 94 | 100.00% | 0 |
| cfdi_v40_pago_032 | 94 | 114 | 94 | 100.00% | 0 |
| cfdi_v40_pago_033 | 67 | 82 | 67 | 100.00% | 0 |
| cfdi_v40_pago_034 | 94 | 114 | 94 | 100.00% | 0 |
| cfdi_v40_pago_035 | 68 | 82 | 68 | 100.00% | 0 |


### Observaciones

* Se obtuvo **0 errores en todos los casos evaluados**.
* La columna **XML Correctos** representa únicamente los campos presentes en el XML que fueron extraídos correctamente.
* La columna **Implementados** incluye además campos opcionales, normalizados o derivados que el parser genera aunque no existan explícitamente en el XML.
* La diferencia entre **Campos XML** e **Implementados** corresponde principalmente a campos fuera del alcance actual del parser o a estructuras opcionales del modelo de salida.
* Los complementos evaluados (**Carta Porte, Comercio Exterior, Nómina, Pagos, INE, Leyendas Fiscales y Addenda**) muestran extracción consistente para los casos de prueba disponibles.

