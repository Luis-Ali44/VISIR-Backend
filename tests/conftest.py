from app.core.config import settings
from app.core.dependencies import get_user
from app.main import app
from app.repositories import documents_repository as real_documents_repo
from app.schemas.user_schema import UsuarioActual


def fake_user():
    return UsuarioActual(
        id="83bfd116-2276-43d7-9c17-25d7bd6700d3",
        id_organizacion="22222222-2222-2222-2222-222222222222",
        jwt="dummy-jwt-token",
    )


class FakeDocumentRepository:
    def __init__(self, user_or_ctx):
        self.ctx = user_or_ctx

    def get_documents_repository(self, limit: int, cursor: str | None = None):
        return []

    def get_document_by_id(self, documento_id: str):
        return []

    def get_my_documents(
        self, limit: int, cursor: str | None, id_usuario: str, id_organizacion: str
    ):
        return []

    def save_document_metadata(self, data: dict):
        return [data]

    def save_document_storage(
        self, contenido_archivo: bytes, nombre_archivo: str, tipo_archivo: str
    ):
        return "fake/path"


# Reemplazar la clase real por la fake durante las pruebas
real_documents_repo.DocumentRepository = FakeDocumentRepository  # type: ignore[misc,assignment]


app.dependency_overrides[get_user] = fake_user

# Marcar entorno de pruebas para comportamientos deterministas
settings.environment = "test"
