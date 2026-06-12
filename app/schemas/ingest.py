from pydantic import BaseModel


class IngestStatusResponse(BaseModel):
    status: str
    mensaje: str
