from app.core.dependencies import get_user
from app.main import app
from app.schemas.user_schema import UsuarioActual


def fake_user():
    return UsuarioActual(
        id="83bfd116-2276-43d7-9c17-25d7bd6700d3",
        id_organizacion="22222222-2222-2222-2222-222222222222",
    )


app.dependency_overrides[get_user] = fake_user
