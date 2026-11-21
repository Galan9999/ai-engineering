# Estimador CAG

Servicio FastAPI que recibe la transcripción de una reunión con un cliente y devuelve una estimación de
software generada por un LLM. Arquitectura **CAG**: las estimaciones de referencia viajan enteras en el
prompt en cada llamada, sin base de datos ni búsqueda.

## Puesta en marcha

```bash
cd estimador-cag
uv sync
cp .env.example .env   # y rellena la API key del proveedor que uses
uv run uvicorn app.main:app --reload
```

- Salud: `GET http://localhost:8000/health`
- Documentación: http://localhost:8000/docs

## Estructura

```
app/
├── main.py                  app, routers y /health
├── config.py                configuración con pydantic-settings (falla si falta la key)
├── routers/estimations.py   POST /api/v1/estimate
├── services/llm_service.py  prompt + contexto + llamada al LLM
└── context/examples.py      estimaciones de referencia (contexto CAG)
```
