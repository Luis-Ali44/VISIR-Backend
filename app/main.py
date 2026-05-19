from fastapi import FastAPI

app = FastAPI(
    title="VISIR API",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/")
def welcome() -> str:
    return "Oli desde visir"
