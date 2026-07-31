from typing import Any
from uuid import uuid4

from app.core.database import ExecCtx
from app.repositories.base_repository import BaseRepository
from app.schemas.user_schema import UsuarioActual


class DocumentRepository(BaseRepository):
    def __init__(self, user_or_ctx: UsuarioActual | ExecCtx):
        super().__init__(user_or_ctx)

    def save_document_storage(
        self, contenido_archivo: bytes, nombre_archivo: str, tipo_archivo: str
    ) -> str:
        extension = nombre_archivo.split(".")[-1]
        ruta_archivo = f"usuarios/{self.ctx.id_usuario}/documentos/{uuid4()}.{extension}"
        self.db.storage.from_("documentos").upload(
            path=ruta_archivo,
            file=contenido_archivo,
            file_options={"content-type": tipo_archivo},
        )
        return ruta_archivo

    def save_document_metadata(self, data: dict) -> list[Any]:
        data["id_organizacion"] = self.ctx.id_organizacion
        response = self.table("documentos").insert(data).execute()
        return list(response.data)

    def get_document_by_id(self, documento_id: str) -> list[Any]:
        response = self.scoped("documentos").eq("id", documento_id).execute()
        return list(response.data)

    def get_documents_repository(self, limit: int, cursor: str | None = None) -> list[Any]:
        query = self.scoped("documentos").order("created_at", desc=True).limit(limit)
        if cursor:
            query = query.lt("created_at", cursor)
        response = query.execute()
        return list(response.data)

    def get_my_documents(
        self, limit: int, cursor: str | None, id_usuario: str, id_organizacion: str
    ) -> list[Any]:
        query = (
            self.scoped("documentos")
            .eq("id_organizacion", id_organizacion)
            .eq("id_usuario", id_usuario)
            .order("created_at", desc=True)
            .limit(limit)
        )
        if cursor:
            query = query.lt("created_at", cursor)
        response = query.execute()
        return list(response.data)

    def get_id_categoria(self, categoria: str = "Sin categoria") -> str | None:
        response = (
            self.db.table("categorias")
            .select("id")
            .ilike("nombre", categoria)
            .maybe_single()
            .execute()
        )

        if response and isinstance(response.data, dict):
            return str(response.data["id"])

        if categoria == "Sin categoria":
            return None

        default_response = (
            self.db.table("categorias")
            .select("id")
            .ilike("nombre", "Sin categoria")
            .maybe_single()
            .execute()
        )

        if default_response and isinstance(default_response.data, dict):
            return str(default_response.data["id"])
        return None

    def save_extracciones_repository(self, data: list[dict[str, Any]]) -> list[Any]:
        for row in data:
            row["id_organizacion"] = self.ctx.id_organizacion
        response = self.table("extracciones").insert(data).execute()
        return list(response.data)

    def tipo_comprobante(self, tipo: str) -> str | None:
        if not tipo:
            return None
        try:
            response = (
                self.db.table("tipos_comprobantes")
                .select("nombre")
                .eq("clave", str(tipo).strip().upper())
                .maybe_single()
                .execute()
            )
            if response and isinstance(response.data, dict):
                return str(response.data.get("nombre"))
        except Exception:
            print(f"Error al obtener tipo_comprobante para clave: {tipo}")
        return None

    def nombre_forma_pago(self, forma_pago: str) -> str | None:
        if not forma_pago:
            return None
        try:
            clave = int(str(forma_pago).strip())
        except (TypeError, ValueError):
            return None
        try:
            response = (
                self.db.table("formas_pago")
                .select("nombre")
                .eq("clave", clave)
                .maybe_single()
                .execute()
            )
            if response and isinstance(response.data, dict):
                return str(response.data.get("nombre"))
        except Exception:
            return None
        return None

    def delete_document_storage(self, ruta_archivo: str) -> None:
        self.db.storage.from_("documentos").remove([ruta_archivo])

    def delete_document_metadata(self, documento_id: str) -> None:
        self.table("documentos").delete().eq("id", documento_id).eq(
            "id_organizacion", self.ctx.id_organizacion
        ).execute()

    def get_document_by_hash(self, hash_archivo: str) -> list[Any]:
        response = self.scoped("documentos").eq("hash_archivo", hash_archivo).execute()
        return list(response.data)

    def descargar_documento_storage(self, ruta_archivo: str) -> Any:
        try:
            response = self.db.storage.from_("documentos").download(ruta_archivo)
            return response
        except Exception as e:
            print(f"[Error] No se pudo descargar el archivo: {e}")
            return None

    def update_document_estado(self, documento_id: str, estado: str) -> None:
        self.table("documentos").update({"estado": estado}).eq("id", documento_id).eq(
            "id_organizacion", self.ctx.id_organizacion
        ).execute()

    def actualizar_estado_documento(self, id_documento: str) -> None:
        (
            self.table("documentos")
            .update({"estado_documento": "procesado"})
            .eq("id", id_documento)
            .eq("id_organizacion", self.ctx.id_organizacion)
            .execute()
        )
