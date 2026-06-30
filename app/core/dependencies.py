from typing import Any, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import supabase
from app.schemas.user_schema import UsuarioActual

security = HTTPBearer()


async def get_user(credenciales: HTTPAuthorizationCredentials = Depends(security)) -> UsuarioActual:

    try:
        jwt_token = credenciales.credentials

        response = supabase.auth.get_user(jwt_token)
        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido o expirado"
            )

        org_response = (
            supabase.table("usuarios")
            .select("id_organizacion")
            .eq("id", str(response.user.id))
            .execute()
        )

        org_id: str | None = None
        if org_response.data and len(org_response.data) > 0:
            row = cast(dict[str, Any], org_response.data[0])

            value = row.get("id_organizacion")
            if value is not None:
                org_id = str(value)

        return UsuarioActual(id=str(response.user.id), id_organizacion=org_id)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token invalido o mal formado"
        ) from e
