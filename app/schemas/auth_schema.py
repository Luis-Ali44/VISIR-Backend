from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints

TextoLimpio = Annotated[
    str, Field(..., min_length=3, max_length=50), StringConstraints(strip_whitespace=True)
]


class Registrar(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="La contraseña debe de tener minimo 6 caracteres",
    )

    nombre: TextoLimpio
    apellido_paterno: TextoLimpio
    apellido_materno: TextoLimpio


class Login(BaseModel):
    email: EmailStr
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="La contraseña debe de tener minimo 6 caracteres",
    )


class TokenResponse(BaseModel):
    token: str
    token_type: str


class MenssageResponse(BaseModel):
    menssage: str
