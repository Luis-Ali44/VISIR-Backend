from __future__ import annotations

import json
import re
from collections.abc import Sequence
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import cast

from campos_cfdi import CAMPOS_OBLIGATORIOS_4_0, CAMPOS_OBLIGATORIOS_CFDI
from catalogos import (
    CATALOGO_CLAVE_UNIDAD,
    CATALOGO_FORMA_PAGO,
    CATALOGO_METODO_PAGO,
    CATALOGO_MONEDA,
    normalizar_catalogo,
)
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

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
    descripcion:     str   | None = Field(None, max_length=1000)
    clave_prod_serv: str   | None = Field(None, pattern=r"^\d{8}$")
    clave_unidad:    str   | None = Field(None, min_length=1, max_length=10)
    unidad:          str   | None = Field(None, max_length=20)
    cantidad:        float | None = Field(None, gt=0)
    valor_unitario:  float | None = Field(None, ge=0)
    descuento:       float | None = Field(None, ge=0)
    importe:         float | None = Field(None, ge=0)
    iva:             float | None = Field(None, ge=0)
    objeto_imp:      str   | None = Field(None, pattern=r"^0[1-4]$")

    @field_validator("clave_prod_serv")
    @classmethod
    def _validar_clave_prod_serv(cls, v: str | None) -> str | None:
        if v is None:
            return v
        claves = _claves_sat()
        if claves and v not in claves:
            raise ValueError(f"ClaveProdServ '{v}' no existe en el catálogo del SAT")
        return v

    @field_validator("clave_unidad")
    @classmethod
    def _validar_clave_unidad(cls, v: str | None) -> str | None:
        if v is not None and v not in CATALOGO_CLAVE_UNIDAD:
            raise ValueError(f"ClaveUnidad '{v}' no está en el catálogo del SAT")
        return v

    @model_validator(mode="after")
    def _validar_concepto(self) -> ConceptoMinimo:
        if (
            self.cantidad is not None
            and self.valor_unitario is not None
            and self.importe is not None
        ):
            esperado = self.cantidad * self.valor_unitario
            if abs(esperado - self.importe) > 1.0:
                raise ValueError(
                    f"Importe ({self.importe}) no cuadra con "
                    f"Cantidad x ValorUnitario : "
                    f"({self.cantidad} x {self.valor_unitario}={esperado:.2f})"
                )

        if (
            self.descuento is not None
            and self.importe is not None
            and self.descuento > self.importe
        ):
            raise ValueError(
                f"Importe ({self.importe}) no cuadra con "
                f"Cantidad x ValorUnitario "
                f"({self.cantidad} x {self.valor_unitario} = {esperado:.2f})"
            )
        return self


class ConceptoXML(ConceptoMinimo):
    clave_prod_serv: str   = Field(..., pattern=r"^\d{8}$")
    cantidad:        float = Field(..., gt=0)
    valor_unitario:  float = Field(..., ge=0)
    importe:         float = Field(..., ge=0)


class ExtractionResultBase(BaseModel):
    version:          str | None = Field(None, pattern=r"^(3\.3|4\.0)$")
    folio_fiscal:     str | None = Field(None, min_length=36, max_length=36)
    fecha_emision:    str | None = None
    sello:            str | None = Field(None, pattern=r"^[A-Za-z0-9+/]+=*$")
    metodo_pago:      str | None = Field(None, pattern=r"^(PUE|PPD)$")
    forma_pago:       str | None = None
    moneda:           str | None = None
    tipo_comprobante: str | None = Field(None, pattern=r"^(I|E|P|N|T)$")
    no_certificado:   str | None = Field(None, pattern=r"^\d{20}$")
    exportacion:      str | None = Field(None, pattern=r"^0[1-4]$")
    lugar_expedicion: str | None = Field(None, pattern=r"^\d{5}$")

    emisor_rfc:            str | None = Field(None, min_length=12, max_length=13)
    emisor_nombre:         str | None = Field(None, max_length=254)
    regimen_fiscal_emisor: str | None = Field(None, pattern=r"^\d{3}$")

    receptor_rfc:              str | None = Field(None, min_length=12, max_length=13)
    receptor_nombre:           str | None = Field(None, max_length=254)
    domicilio_fiscal_receptor: str | None = Field(None, pattern=r"^\d{5}$")
    regimen_fiscal_receptor:   str | None = Field(None, pattern=r"^\d{3}$")
    uso_cfdi:                  str | None = Field(None, pattern=r"^[A-Z][A-Z0-9]\d{1,2}$")

    subtotal:    float | None = Field(None, ge=0)
    descuento:   float | None = Field(None, ge=0)
    iva:         float | None = Field(None, ge=0)
    retenciones: float | None = Field(None, ge=0)
    total:       float | None = Field(None, ge=0)
    conceptos:   Sequence[ConceptoMinimo] = Field(default_factory=list)

    @field_validator("metodo_pago", mode="before")
    @classmethod
    def _normalizar_metodo_pago(cls, v: str | None) -> str | None:
        # cast: normalizar_catalogo() puede no tener anotación de retorno en
        # catalogos.py, lo que hace que mypy infiera Any en vez de str | None.
        return cast("str | None", normalizar_catalogo(v, CATALOGO_METODO_PAGO))

    @field_validator("forma_pago", mode="before")
    @classmethod
    def _normalizar_forma_pago(cls, v: str | None) -> str | None:
        return cast("str | None", normalizar_catalogo(v, CATALOGO_FORMA_PAGO))

    @field_validator("moneda", mode="before")
    @classmethod
    def _normalizar_moneda(cls, v: str | None) -> str | None:
        return cast("str | None", normalizar_catalogo(v, CATALOGO_MONEDA))

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

    @field_validator("emisor_nombre", mode="before")
    @classmethod
    def _norm_emisor_nombre(cls, v: str | None) -> str | None:
        return v.upper().strip() if v else v

    @field_validator("receptor_nombre", mode="before")
    @classmethod
    def _norm_receptor_nombre(cls, v: str | None) -> str | None:
        return v.upper().strip() if v else v

    @model_validator(mode="after")
    def _reglas_negocio(self) -> ExtractionResultBase:
        if (
            self.descuento is not None
            and self.subtotal is not None
            and self.descuento > self.subtotal
        ):
            raise ValueError(f"Descuento ({self.descuento}) > SubTotal ({self.subtotal})")

        if self.tipo_comprobante != "P":
            if (
                self.metodo_pago == "PPD"
                and self.forma_pago is not None
                and self.forma_pago != "99"
            ):
                raise ValueError("MetodoPago PPD requiere FormaPago = '99'")

            if self.metodo_pago == "PUE" and self.forma_pago == "99":
                raise ValueError("MetodoPago PUE no puede usar FormaPago '99'")

        if self.subtotal is not None and self.total is not None:
            iva         = self.iva         or 0.0
            retenciones = self.retenciones or 0.0
            descuento   = self.descuento   or 0.0
            esperado = self.subtotal - descuento + iva - retenciones
            if abs(esperado - self.total) > 1.0:
                raise ValueError(
                    f"Total ({self.total}) no cuadra: "
                    f"SubTotal({self.subtotal}) - Descuento({descuento}) "
                    f"+ IVA({iva}) - Retenciones({retenciones}) = {esperado:.2f}"
                )

        return self


class ExtractionResultOCR(ExtractionResultBase):
    pass


class ExtractionResultXML(ExtractionResultBase):
    conceptos: list[ConceptoXML] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validar_completitud(self) -> ExtractionResultXML:
        ausentes: list[str] = []
        es_pago = self.tipo_comprobante == "P"

        for campo, etiqueta in CAMPOS_OBLIGATORIOS_CFDI.items():
            if getattr(self, campo) in (None, ""):
                if es_pago and campo in ["forma_pago", "metodo_pago"]:
                    continue
                ausentes.append(etiqueta)

        if not self.conceptos:
            ausentes.append("Conceptos (al menos 1)")

        if self.version == "4.0":
            for campo, etiqueta in CAMPOS_OBLIGATORIOS_4_0.items():
                if not getattr(self, campo, None):
                    ausentes.append(f"[4.0] {etiqueta}")

            for i, conc in enumerate(self.conceptos):
                if not getattr(conc, "objeto_imp", None):
                    ausentes.append(f"Concepto #{i+1} → ObjetoImp [4.0]")

        if ausentes:
            raise ValueError(
                "Campos obligatorios faltantes en CFDI: " + ", ".join(ausentes)
            )

        return self


def _aplanar_estructura(data: dict) -> dict:
    resultado = dict(data)

    if "emisor" in resultado and isinstance(resultado["emisor"], dict):
        emisor = resultado.pop("emisor")
        resultado.setdefault("emisor_rfc",            emisor.get("RFC"))
        resultado.setdefault("emisor_nombre",         emisor.get("nombre"))
        resultado.setdefault("regimen_fiscal_emisor", emisor.get("regimen_fiscal"))

    if "receptor" in resultado and isinstance(resultado["receptor"], dict):
        receptor = resultado.pop("receptor")
        resultado.setdefault("receptor_rfc",              receptor.get("RFC"))
        resultado.setdefault("receptor_nombre",           receptor.get("nombre"))
        resultado.setdefault("uso_cfdi",                  receptor.get("uso_cfdi"))
        resultado.setdefault("regimen_fiscal_receptor",   receptor.get("regimen_fiscal"))
        resultado.setdefault("domicilio_fiscal_receptor", receptor.get("domicilio_fiscal"))

    if "fecha" in resultado and "fecha_emision" not in resultado:
        resultado["fecha_emision"] = resultado.pop("fecha")
    else:
        resultado.pop("fecha", None)

    return resultado


def validar[T: ExtractionResultBase](
    data: dict,
    modelo_cls: type[T],
) -> tuple[bool, list[str], T | None]:
    campos_validos = set(modelo_cls.model_fields)
    payload = _aplanar_estructura(data)
    payload = {k: v for k, v in payload.items() if k in campos_validos and v is not None}

    errores: list[str] = []
    try:
        modelo = modelo_cls(**payload)
        return True, [], modelo
    except ValidationError as e:
        for err in e.errors():
            loc = " → ".join(str(x) for x in err["loc"])
            errores.append(f"{loc}: {err['msg']}")
        return False, errores, None
    except Exception as e:
        errores.append(str(e))
        return False, errores, None


def validar_ocr(data: dict) -> tuple[bool, list[str], ExtractionResultOCR | None]:
    return validar(data, ExtractionResultOCR)


def validar_xml(data: dict) -> tuple[bool, list[str], ExtractionResultXML | None]:
    return validar(data, ExtractionResultXML)


def campos_obligatorios_ausentes(data: dict) -> list[str]:
    ausentes: list[str] = []
    payload = _aplanar_estructura(data)

    tipo_comprobante = payload.get("tipo_comprobante", "")
    es_pago = tipo_comprobante == "P"

    for campo, etiqueta in CAMPOS_OBLIGATORIOS_CFDI.items():
        valor = payload.get(campo)
        if valor is None or (isinstance(valor, str) and valor.strip() == ""):
            if es_pago and campo in ["forma_pago", "metodo_pago"]:
                continue
            ausentes.append(etiqueta)

    if payload.get("version") == "4.0":
        for campo, etiqueta in CAMPOS_OBLIGATORIOS_4_0.items():
            valor = payload.get(campo)
            if not valor or (isinstance(valor, str) and valor.strip() == ""):
                ausentes.append(f"[4.0] {etiqueta}")

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
        if payload.get("version") == "4.0" and not conc.get("objeto_imp"):
            ausentes.append(f"Concepto #{i+1} → ObjetoImp [4.0]")

    return ausentes


def validar_con_obligatorios(
    data: dict,
) -> tuple[bool, list[str], list[str], ExtractionResultXML | None]:
    valido_formato, errores_formato, modelo = validar_xml(data)
    ausentes = campos_obligatorios_ausentes(data)
    valido_total = valido_formato and len(ausentes) == 0
    return valido_total, errores_formato, ausentes, modelo
