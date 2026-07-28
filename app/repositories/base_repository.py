from app.core.database import ExecCtx, cliente_for
from app.schemas.user_schema import UsuarioActual


class BaseRepository:
    def __init__(self, user: UsuarioActual, jwt: str | None = None):
        self.ctx = ExecCtx.from_user(user, jwt)
        self.db = cliente_for(self.ctx)

    def scoped(self, table: str):
        # Garantiza el multi-tenant en automático para repositorios que lo requieran
        return self.db.table(table).eq("id_organizacion", self.ctx.id_organizacion)
