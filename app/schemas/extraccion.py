from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ExtraccionResponse(BaseModel):
    id: UUID = Field(..., description="ID único de la extracción en Supabase")
    id_organizacion: UUID = Field(..., description="ID de la organización a la que pertenece")
    id_documento: UUID = Field(..., description="ID del documento padre relacionado")
    folio_fiscal: str | None = Field(None, description="UUID o folio fiscal del CFDI")
    nombre_emisor: str | None = Field(None, description="Nombre o Razón Social del emisor")
    rfc_emisor: str | None = Field(None, description="RFC del emisor")
    nombre_receptor: str | None = Field(None, description="Nombre o Razón Social del receptor")
    rfc_receptor: str | None = Field(None, description="RFC del receptor")
    fecha_emision: datetime | None = Field(None, description="Fecha de emisión del comprobante")
    regimen_fiscal: str | None = Field(None, description="Régimen fiscal del receptor")
    total: float | None = Field(None, description="Monto total del comprobante")
    metodo_pago: str | None = Field(None, description="Método de pago (PUE, PPD)")
    forma_pago: str | None = Field(
        None, 
        description="Nombre de la forma de pago (Efectivo, Transferencia, etc.)"
    )
    tipo_comprobante: str | None = Field(
        None, 
        description="Tipo de comprobante (Ingreso, Egreso, etc.)"
    )
    uso_cfdi_receptor: str | None = Field(None, description="Uso del CFDI del receptor")
    estado: str = Field("procesado", description="Estado del procesamiento")
    metadatos: dict[str, Any] = Field(..., description="JSON completo estructurado por Mistral")
    created_at: datetime = Field(..., description="Fecha de creación del registro")
