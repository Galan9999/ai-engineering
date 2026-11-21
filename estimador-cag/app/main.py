from fastapi import FastAPI

from app.config import get_settings
from app.routers import estimations

get_settings()

app = FastAPI(
    title="Estimador CAG",
    description="Recibe la transcripción de una reunión y devuelve una estimación de software "
    "generada por un LLM con arquitectura CAG.",
    version="0.1.0",
)

app.include_router(estimations.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
