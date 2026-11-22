from fastapi import FastAPI

from app.config import get_settings
from app.context.examples import get_examples, get_rate_card
from app.routers import estimations
from app.services.pricing import get_pricing

get_settings()
get_rate_card()
get_examples()
get_pricing()

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
