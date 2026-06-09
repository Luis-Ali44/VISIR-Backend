from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


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


class ExtractionResult(BaseModel):
    version:         Optional[str] = Field(None, pattern=r"^(3\.3|4\.0)$")
    emisor_rfc:      Optional[str] = Field(None, min_length=12, max_length=13)
    emisor_nombre:   Optional[str] = Field(None, max_length=254)
    receptor_rfc:    Optional[str] = Field(None, min_length=12, max_length=13)
    receptor_nombre: Optional[str] = Field(None, max_length=254)
    fecha_emision:   Optional[str] = None
    folio_fiscal:    Optional[str] = Field(None, min_length=36, max_length=36)
    subtotal:        Optional[float] = Field(None, ge=0)
    descuento:       Optional[float] = Field(None, ge=0)
    total:           Optional[float] = Field(None, ge=0)
    iva:             Optional[float] = Field(None, ge=0)
    retenciones:     Optional[float] = Field(None, ge=0)
    metodo_pago:     Optional[str] = Field(None, pattern=r"^(PUE|PPD)$")
    forma_pago:      Optional[str] = None
    moneda:          Optional[str] = None
    uso_cfdi:        Optional[str] = None
    tipo_de_comprobante: Optional[str] = None
    conceptos:       List[ConceptoMinimo] = Field(default_factory=list)

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


def _aplanar_estructura(data: dict) -> dict:
    resultado = dict(data)

    if "emisor" in resultado and isinstance(resultado["emisor"], dict):
        emisor = resultado.pop("emisor")
        resultado.setdefault("emisor_rfc",    emisor.get("RFC"))
        resultado.setdefault("emisor_nombre", emisor.get("nombre"))

    if "receptor" in resultado and isinstance(resultado["receptor"], dict):
        receptor = resultado.pop("receptor")
        resultado.setdefault("receptor_rfc",    receptor.get("RFC"))
        resultado.setdefault("receptor_nombre", receptor.get("nombre"))

    if "fecha" in resultado and "fecha_emision" not in resultado:
        resultado["fecha_emision"] = resultado.pop("fecha")
    else:
        resultado.pop("fecha", None)

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
