from typing import Any, cast

from app.core.database import ExecCtx
from app.repositories.base_repository import BaseRepository


class ConsultaRepository(BaseRepository):
    def __init__(self, ctx: ExecCtx):
        super().__init__(ctx)

    def gasto_provedor(self) -> list[dict[str, Any]]:
        response = (
            self.scoped("extracciones")
            .select("rfc_emisor, nombre_emisor, total.sum(), id.count()")
            .eq("estado", "procesado")
            .execute()
        )

        return cast(list[dict[str, Any]], response.data)

    def gasto_categoria(self) -> list[dict[str, Any]]:
        response = (
            self.scoped("extracciones")
            .select("id_categorias,total.sum(), id.count()")
            .eq("estado", "procesado")
            .execute()
        )

        return cast(list[dict[str, Any]], response.data)
