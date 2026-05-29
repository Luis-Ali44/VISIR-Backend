from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.routers.auth_router import router as auth_router
from app.routers.documents_router import router as documents_router
from app.routers.test_supabase import router as test_router

app = FastAPI(
    title="VISIR API",
    version="0.1.0",
)

security = HTTPBearer()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
def welcome(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:

    token = credentials.credentials
    print(token)
    return "Oli desde visir"


app.include_router(test_router)
app.include_router(documents_router)
app.include_router(auth_router)
