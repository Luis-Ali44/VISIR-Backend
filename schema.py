from __future__ import annotations

import re
import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Optional, Literal, List

from pydantic import BaseModel, Field, field_validator, model_validator

from catalogos import (
    normalizar_catalogo,
    CATALOGO_METODO_PAGO,
    CATALOGO_FORMA_PAGO,
    CATALOGO_USO_CFDI,
    CATALOGO_TIPO_COMPROBANTE,
    CATALOGO_MONEDA,
    CATALOGO_EXPORTACION,
    CATALOGO_REGIMEN_FISCAL,
)

_CATALOGO_PATH = Path(__file__).parent / "catalogo_prodserv_sat.json"


@lru_cache(maxsize=1)
def _claves_sat() -> frozenset[str]:
    try:
        with _CATALOGO_PATH.open(encoding="utf-8") as f:
            return frozenset(json.load(f).keys())
    except FileNotFoundError:
        return frozenset()



def _validar_rfc(v: str, permitir_genericos: bool = False) -> str:
    v = re.sub(r"[\s\-_]", "", v.upper().strip())
    if permitir_genericos and v in ("XAXX010101000", "XEXX010101000"):
        return v
    patron = r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$"
    if not re.match(patron, v):
        raise ValueError(f"RFC inválido: {v!r}")
    return v


class ConceptoMinimo(BaseModel):
    descripcion:     str   = Field(..., min_length=1, max_length=1000)
    clave_prod_serv: Optional[str] = Field(None, pattern=r"^\d{8}$")
    unidad:          Optional[str] = None
    cantidad:        Optional[float] = Field(None, ge=0)
    valor_unitario:  Optional[float] = Field(None, ge=0)
    importe:         Optional[float] = Field(None, ge=0)
    iva:             Optional[float] = Field(None, ge=0)

    @field_validator("clave_prod_serv")
    @classmethod
    def _validar_clave_prod_serv(cls, v):
        if v is None:
            return v
        claves = _claves_sat()
        if claves and v not in claves:
            raise ValueError(f"ClaveProdServ '{v}' no existe en el catálogo del SAT")
        return v

class ExtractionResult(BaseModel):
    version:         Optional[str] = Field(None, pattern=r"^(3\.3|4\.0)$")
    emisor_rfc:      Optional[str] = Field(None, min_length=12, max_length=13)
    emisor_nombre:   Optional[str] = Field(None, max_length=254)
    emisor_regimen_fiscal: Optional[str] = None 
    receptor_rfc:    Optional[str] = Field(None, min_length=12, max_length=13)
    receptor_nombre: Optional[str] = Field(None, max_length=254)
    receptor_regimen_fiscal: Optional[str] = None   
    receptor_domicilio_fiscal: Optional[str] = None 
    fecha_emision:   Optional[str] = None
    fecha_timbrado:  Optional[str] = None          
    folio_fiscal:    Optional[str] = Field(None, min_length=36, max_length=36)
    lugar_expedicion: Optional[str] = None          
    subtotal:        Optional[float] = Field(None, ge=0)
    descuento:       Optional[float] = Field(None, ge=0)
    total:           Optional[float] = Field(None, ge=0)
    iva:             Optional[float] = Field(None, ge=0)
    retenciones:     Optional[float] = Field(None, ge=0)
    metodo_pago:     Optional[str] = Field(None, pattern=r"^(PUE|PPD)$")
    forma_pago:      Optional[str] = None
    moneda:          Optional[str] = None
    tipo_cambio:     Optional[float] = Field(None, ge=0)   
    exportacion:     Optional[str] = None                
    uso_cfdi:        Optional[str] = None
    tipo_de_comprobante: Optional[str] = None
    conceptos:       List[ConceptoMinimo] = Field(default_factory=list)

  
    @field_validator("metodo_pago", mode="before")
    def _normalizar_metodo_pago(cls, v):
        return normalizar_catalogo(v, CATALOGO_METODO_PAGO)

    @field_validator("forma_pago", mode="before")
    def _normalizar_forma_pago(cls, v):
        return normalizar_catalogo(v, CATALOGO_FORMA_PAGO)

    @field_validator("uso_cfdi", mode="before")
    def _normalizar_uso_cfdi(cls, v):
        return normalizar_catalogo(v, CATALOGO_USO_CFDI)

    @field_validator("tipo_de_comprobante", mode="before")
    def _normalizar_tipo_comprobante(cls, v):
        return normalizar_catalogo(v, CATALOGO_TIPO_COMPROBANTE)

    @field_validator("moneda", mode="before")
    def _normalizar_moneda(cls, v):
        return normalizar_catalogo(v, CATALOGO_MONEDA)

    @field_validator("exportacion", mode="before")
    def _normalizar_exportacion(cls, v):
        return normalizar_catalogo(v, CATALOGO_EXPORTACION)

    @field_validator("emisor_regimen_fiscal", "receptor_regimen_fiscal", mode="before")
    def _normalizar_regimen_fiscal(cls, v):
        return normalizar_catalogo(v, CATALOGO_REGIMEN_FISCAL)


    @field_validator("emisor_rfc")
    @classmethod
    def _val_emisor_rfc(cls, v):
        return _validar_rfc(v, permitir_genericos=False) if v else v

    @field_validator("receptor_rfc")
    @classmethod
    def _val_receptor_rfc(cls, v):
        return _validar_rfc(v, permitir_genericos=True) if v else v

    @field_validator("folio_fiscal")
    @classmethod
    def _val_uuid(cls, v):
        if v is None:
            return v
        patron = r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$"
        v = v.upper()
        if not re.match(patron, v):
            raise ValueError(f"folio_fiscal no tiene formato UUID válido: {v!r}")
        return v


    @field_validator("fecha_emision", "fecha_timbrado")
    @classmethod
    def _validar_fecha(cls, v):
        if v is None:
            return v

        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", v):
            raise ValueError(f"Fecha debe tener formato ISO: YYYY-MM-DDTHH:MM:SS, recibido: {v}")
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(f"Fecha inválida: {v}")
        return v

    @field_validator("lugar_expedicion", "receptor_domicilio_fiscal")
    @classmethod
    def _validar_cp(cls, v):
        if v is None:
            return v
        if not re.match(r"^\d{5}$", v):
            raise ValueError(f"Código postal debe tener 5 dígitos: {v}")
        return v

    @model_validator(mode="after")
    def _reglas_negocio(self):
     
        if self.descuento is not None and self.subtotal is not None:
            if self.descuento > self.subtotal:
                raise ValueError(f"Descuento ({self.descuento}) > SubTotal ({self.subtotal})")
      
        if self.metodo_pago == "PPD" and self.forma_pago is not None and self.forma_pago != "99":
            raise ValueError("MetodoPago PPD requiere FormaPago = '99'")
        
        if self.metodo_pago == "PUE" and self.forma_pago == "99":
            raise ValueError("MetodoPago PUE no puede usar FormaPago '99'")
      
        if self.moneda is not None and self.moneda != "MXN" and self.tipo_cambio is None:
            raise ValueError(f"TipoCambio es obligatorio para moneda '{self.moneda}'")
        if self.moneda == "MXN" and self.tipo_cambio is not None:
            raise ValueError("No debe especificar TipoCambio cuando Moneda es MXN")
        return self

def _aplanar_estructura(data: dict) -> dict:
    resultado = dict(data)

    if "emisor" in resultado and isinstance(resultado["emisor"], dict):
        emisor = resultado.pop("emisor")
        resultado.setdefault("emisor_rfc",    emisor.get("RFC"))
        resultado.setdefault("emisor_nombre", emisor.get("nombre"))
        resultado.setdefault("emisor_regimen_fiscal", emisor.get("regimen_fiscal"))

    if "receptor" in resultado and isinstance(resultado["receptor"], dict):
        receptor = resultado.pop("receptor")
        resultado.setdefault("receptor_rfc",    receptor.get("RFC"))
        resultado.setdefault("receptor_nombre", receptor.get("nombre"))
        resultado.setdefault("receptor_regimen_fiscal", receptor.get("regimen_fiscal"))
        resultado.setdefault("receptor_domicilio_fiscal", receptor.get("domicilio_fiscal"))

    if "fecha" in resultado and "fecha_emision" not in resultado:
        resultado["fecha_emision"] = resultado.pop("fecha")
    else:
        resultado.pop("fecha", None)

    if "fecha_timbrado" not in resultado and "timbre_fiscal" in resultado:
        resultado["fecha_timbrado"] = resultado["timbre_fiscal"].get("fecha_timbrado")

    return resultado


def validar(data: dict) -> tuple[bool, list[str], ExtractionResult | None]:
    campos_validos = {f for f in ExtractionResult.model_fields}
    payload = _aplanar_estructura(data)
    payload = {k: v for k, v in payload.items() if k in campos_validos and v is not None}

    errores: list[str] = []
    try:
        modelo = ExtractionResult(**payload)
        return True, [], modelo
    except Exception as e:
        try:
            for err in e.errors():
                loc = " → ".join(str(x) for x in err["loc"])
                errores.append(f"{loc}: {err['msg']}")
        except AttributeError:
            errores.append(str(e))
        return False, errores, None


def validar_con_obligatorios(data: dict) -> tuple[bool, list[str], list[str], ExtractionResult | None]:

    valido_formato, errores_formato, modelo = validar(data)

    campos_obligatorios = {
        "version": "Versión (4.0)",
        "fecha_emision": "Fecha de emisión",
        "tipo_de_comprobante": "Tipo de comprobante",
        "subtotal": "SubTotal",
        "total": "Total",
        "moneda": "Moneda",
        "emisor_rfc": "Emisor RFC",
        "emisor_nombre": "Emisor nombre",
        "emisor_regimen_fiscal": "Emisor régimen fiscal",
        "receptor_rfc": "Receptor RFC",
        "receptor_nombre": "Receptor nombre",
        "receptor_regimen_fiscal": "Receptor régimen fiscal",
        "receptor_domicilio_fiscal": "Receptor domicilio fiscal (CP)",
        "uso_cfdi": "Receptor uso CFDI",
        "folio_fiscal": "UUID (folio fiscal)",
        "fecha_timbrado": "Fecha de timbrado",
        "lugar_expedicion": "Lugar de expedición (CP)",
        "exportacion": "Exportación",
    }

    ausentes = []
    payload = _aplanar_estructura(data)
    for campo, etiqueta in campos_obligatorios.items():
        valor = payload.get(campo)
        if valor is None or (isinstance(valor, str) and valor.strip() == ""):
            ausentes.append(etiqueta)

    conceptos = payload.get("conceptos", [])
    for i, conc in enumerate(conceptos):
        if not conc.get("descripcion"):
            ausentes.append(f"Concepto #{i+1} → Descripción")
        if conc.get("clave_prod_serv") is None:
            ausentes.append(f"Concepto #{i+1} → ClaveProdServ")
        if conc.get("cantidad") is None:
            ausentes.append(f"Concepto #{i+1} → Cantidad")
        if conc.get("valor_unitario") is None:
            ausentes.append(f"Concepto #{i+1} → ValorUnitario")
        if conc.get("importe") is None:
            ausentes.append(f"Concepto #{i+1} → Importe")

    valido_total = valido_formato and len(ausentes) == 0
    return valido_total, errores_formato, ausentes, modelo