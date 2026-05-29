from pydantic import BaseModel, EmailStr


class LoginData(BaseModel):
    email: EmailStr
    password: str


class UsuariosModel(BaseModel):
    nombre: str
    apellido_paterno: str
