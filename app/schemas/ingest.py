from pydantic import BaseModel


class IngestStatusResponse(BaseModel):
    status: str
    mensaje: str


class ReindexResponse(BaseModel):
    status: str
    mensaje: str
    intentados: int = 0
    exitosos: int = 0
    fallidos: int = 0
    errores: list[str] = []
