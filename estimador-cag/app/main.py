from fastapi import FastAPI

app = FastAPI(
    title="Estimador CAG",
    description="Recibe la transcripción de una reunión y devuelve una estimación de software "
    "generada por un LLM con arquitectura CAG.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
