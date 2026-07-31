from typing import Any

from app.core.database import ExecCtx, cliente_for
from app.schemas.user_schema import UsuarioActual


class BaseRepository:
    def __init__(self, user: UsuarioActual):
        self.ctx = ExecCtx.from_user(user, user.jwt)
        self.db = cliente_for(self.ctx)

    def scoped(self, table: str) -> Any:
        # Garantiza el multi-tenant en automático para repositorios que lo requieran
        return self.db.table(table).select("*").eq("id_organizacion", self.ctx.id_organizacion)
