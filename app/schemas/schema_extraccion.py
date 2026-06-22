from __future__ import annotations

import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from app.services.Extraccion.catalogos import (
    CATALOGO_FORMA_PAGO,
    CATALOGO_METODO_PAGO,
    CATALOGO_MONEDA,
    normalizar_catalogo,
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
    if not re.match(r"^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$", v):
        raise ValueError(f"RFC inválido: {v!r}")
    return v


class ConceptoMinimo(BaseModel):
    descripcion:     str        = Field(..., min_length=1, max_length=1000)
    clave_prod_serv: str | None = Field(None, pattern=r"^\d{8}$")
    unidad:          str | None = None
    cantidad:        float | None = Field(None, ge=0)
    valor_unitario:  float | None = Field(None, ge=0)
    descuento:       float | None = Field(None, ge=0)
    importe:         float | None = Field(None, ge=0)
    iva:             float | None = Field(None, ge=0)

    @field_validator("clave_prod_serv")
    @classmethod
    def _validar_clave_prod_serv(cls, v: str | None) -> str | None:
        if v is None:
            return v
        claves = _claves_sat()
        if claves and v not in claves:
            raise ValueError(f"ClaveProdServ '{v}' no existe en el catálogo del SAT")
        return v


class ExtractionResult(BaseModel):
    version:         str | None = Field(None, pattern=r"^(3\.3|4\.0)$")
    folio_fiscal:    str | None = Field(None, min_length=36, max_length=36)
    fecha_emision:   str | None = None
    metodo_pago:     str | None = Field(None, pattern=r"^(PUE|PPD)$")
    forma_pago:      str | None = None
    moneda:          str | None = None
    emisor_rfc:      str | None = Field(None, min_length=12, max_length=13)
    emisor_nombre:   str | None = Field(None, max_length=254)
    receptor_rfc:    str | None = Field(None, min_length=12, max_length=13)
    receptor_nombre: str | None = Field(None, max_length=254)
    subtotal:        float | None = Field(None, ge=0)
    descuento:       float | None = Field(None, ge=0)
    iva:             float | None = Field(None, ge=0)
    retenciones:     float | None = Field(None, ge=0)
    total:           float | None = Field(None, ge=0)
    conceptos:       list[ConceptoMinimo] = Field(default_factory=list)

    @field_validator("metodo_pago", mode="before")
    @classmethod
    def _normalizar_metodo_pago(cls, v: str | None) -> str | None:
        return normalizar_catalogo(v, CATALOGO_METODO_PAGO)

    @field_validator("forma_pago", mode="before")
    @classmethod
    def _normalizar_forma_pago(cls, v: str | None) -> str | None:
        return normalizar_catalogo(v, CATALOGO_FORMA_PAGO)

    @field_validator("moneda", mode="before")
    @classmethod
    def _normalizar_moneda(cls, v: str | None) -> str | None:
        return normalizar_catalogo(v, CATALOGO_MONEDA)

    @field_validator("emisor_rfc")
    @classmethod
    def _val_emisor_rfc(cls, v: str | None) -> str | None:
        return _validar_rfc(v, permitir_genericos=False) if v else v

    @field_validator("receptor_rfc")
    @classmethod
    def _val_receptor_rfc(cls, v: str | None) -> str | None:
        return _validar_rfc(v, permitir_genericos=True) if v else v

    @field_validator("folio_fiscal")
    @classmethod
    def _val_uuid(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.upper()
        if not re.match(r"^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$", v):
            raise ValueError(f"folio_fiscal no tiene formato UUID válido: {v!r}")
        return v

    @field_validator("fecha_emision")
    @classmethod
    def _validar_fecha(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$", v):
            raise ValueError(f"Fecha debe tener formato ISO: YYYY-MM-DDTHH:MM:SS, recibido: {v}")
        try:
            datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Fecha inválida: {v}") from e
        return v

    @model_validator(mode="after")
    def _reglas_negocio(self) -> ExtractionResult:
        if (
            self.descuento is not None
            and self.subtotal is not None
            and self.descuento > self.subtotal
        ):
            raise ValueError(f"Descuento ({self.descuento}) > SubTotal ({self.subtotal})")

        if (
            self.metodo_pago == "PPD"
            and self.forma_pago is not None
            and self.forma_pago != "99"
        ):
            raise ValueError("MetodoPago PPD requiere FormaPago = '99'")

        if self.metodo_pago == "PUE" and self.forma_pago == "99":
            raise ValueError("MetodoPago PUE no puede usar FormaPago '99'")

        return self


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
    campos_validos = set(ExtractionResult.model_fields)
    payload = _aplanar_estructura(data)
    payload = {k: v for k, v in payload.items() if k in campos_validos and v is not None}

    errores: list[str] = []
    try:
        modelo = ExtractionResult(**payload)
        return True, [], modelo
    except ValidationError as e:
        for err in e.errors():
            loc = " → ".join(str(x) for x in err["loc"])
            errores.append(f"{loc}: {err['msg']}")
        return False, errores, None
    except Exception as e:
        errores.append(str(e))
        return False, errores, None


def validar_con_obligatorios(
    data: dict,
) -> tuple[bool, list[str], list[str], ExtractionResult | None]:
    valido_formato, errores_formato, modelo = validar(data)

    campos_obligatorios = {
        "version":         "Versión (4.0)",
        "folio_fiscal":    "UUID (folio fiscal)",
        "fecha_emision":   "Fecha de emisión",
        "metodo_pago":     "Método de pago",
        "forma_pago":      "Forma de pago",
        "moneda":          "Moneda",
        "emisor_rfc":      "Emisor RFC",
        "emisor_nombre":   "Emisor nombre",
        "receptor_rfc":    "Receptor RFC",
        "receptor_nombre": "Receptor nombre",
        "subtotal":        "SubTotal",
        "total":           "Total",
    }

    ausentes: list[str] = []
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