from supabase import Client, create_client

from app.core.config import settings

# Cliente administrativo: usa SUPABASE_SECRET_KEY y bypassea RLS. Se usa
# para TODAS las operaciones de datos (SELECT/INSERT/UPDATE en
# documentos, extracciones, usuarios, etc.) y para validar tokens vía
# auth.get_user(jwt) — eso es seguro porque get_user(jwt) con argumento
# explícito NO dispara un evento de auth (no llama _save_session
# internamente, ver supabase_auth/_sync/gotrue_client.py).
#
# Lo que NUNCA debe hacerse con este cliente es sign_in_with_password(),
# sign_up() o set_session(): la librería supabase-py registra un
# listener global (Client._listen_to_auth_events) que, al recibir un
# evento SIGNED_IN/TOKEN_REFRESHED/SIGNED_OUT, REEMPLAZA el header
# Authorization de TODO el cliente (incluyendo el cliente postgrest
# usado por supabase.table(...)) con el access_token de la sesión que
# acaba de iniciar. Como `supabase` es un singleton importado por todos
# los repositorios, cualquier login/registro de CUALQUIER usuario deja
# el cliente "pegado" con ESE token para TODAS las llamadas siguientes
# de TODOS los usuarios, hasta el próximo evento de auth — lo cual
# rompe los INSERT administrativos haciendo que respeten las políticas
# RLS del usuario logueado en vez de bypassearlas con el secret key.
# Por eso login/registro/logout usan get_auth_client() abajo: un cliente
# nuevo y efímero, descartado al terminar el request, que nunca toca
# este singleton.
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SECRET_KEY,
)


def get_auth_client() -> Client:
    """
    Crea un cliente de Supabase nuevo, exclusivo para una sola operación
    de auth (sign_up, sign_in_with_password, set_session + sign_out).
    Se inicializa con la public/publishable key, igual que lo haría un
    cliente real sin privilegios elevados, y se descarta después de usarse
    — nunca se comparte entre requests ni se reutiliza como el `supabase`
    administrativo de arriba.
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_PUBLIC_KEY,
    )
