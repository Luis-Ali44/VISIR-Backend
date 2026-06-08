from fastapi import FastAPI

from app.routers.auth_router import router as auth_router
from app.routers.documents_router import router as documents_router

app = FastAPI(title="VISIR API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
def welcome() -> str:
    return "Oli desde visir"


app.include_router(documents_router)
app.include_router(auth_router)
