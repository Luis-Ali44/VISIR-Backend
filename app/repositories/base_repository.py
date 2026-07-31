from typing import Any

from app.core.database import ExecCtx, cliente_for
from app.schemas.user_schema import UsuarioActual


class BaseRepository:
    def __init__(self, user_or_ctx: UsuarioActual | ExecCtx):
        if isinstance(user_or_ctx, ExecCtx):
            self.ctx = user_or_ctx
        else:
            self.ctx = ExecCtx.from_user(user_or_ctx, user_or_ctx.jwt)
        self.db = cliente_for(self.ctx)

    def scoped(self, table: str) -> Any:
        # Garantiza el multi-tenant en automático para lecturas (select + filtro)
        return self.db.table(table).select("*").eq("id_organizacion", self.ctx.id_organizacion)

    def table(self, table: str) -> Any:
        # Acceso directo a la tabla, para insert/update/delete
        return self.db.table(table)
