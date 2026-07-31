from typing import Any, cast

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase.client import create_client

from app.core.config import settings
from app.schemas.user_schema import UsuarioActual

security = HTTPBearer()


async def get_user(credenciales: HTTPAuthorizationCredentials = Depends(security)) -> UsuarioActual:

    try:
        jwt_token = credenciales.credentials

        temp_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_PUBLIC_KEY)
        temp_client.postgrest.auth(jwt_token)

        auth_response = temp_client.auth.get_user(jwt_token)
        if not auth_response or not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido o expirado"
            )

        user_id = str(auth_response.user.id)

        org_response = (
            temp_client.table("usuarios").select("id_organizacion").eq("id", user_id).execute()
        )

        if not org_response.data or len(org_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario sin organización asignada"
            )

        row = cast(dict[str, Any], org_response.data[0])
        org_id = str(row.get("id_organizacion"))

        return UsuarioActual(id=user_id, id_organizacion=org_id, jwt=jwt_token)

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error atrapado: {type(e).__name__} - {e!s}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token invalido o mal formado"
        ) from e
