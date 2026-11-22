# AI Engineering 2026/11 (LIDR) — fork de ejercicios

Fork de `LIDR-academy-temp/ai-engineering`. Aquí crece el proyecto del máster: el **estimador de software**
(CAG en la Sesión 2 → RAG → agentes → producción).

## Organización

- El proyecto vive en `estimador-cag/`. Todos los comandos, desde esa carpeta.
- `estimator/` es la solución de referencia de LIDR: no se toca ni se copia.
- **Una rama por ejercicio** (`ejercicio/s<N>-<slug>`) que sale de la rama `session_<N>` de LIDR, con un PR
  dentro del fork contra esa rama.

## Comandos

```bash
cd estimador-cag
uv sync                                   # dependencias (.venv)
uv run uvicorn app.main:app --reload      # API en http://localhost:8000 (Swagger en /docs)
uv run pytest                             # tests: estructura + /health
uv run ruff check . && uv run ruff format .
docker compose up --build                 # lo mismo en contenedor
```

## Arquitectura (Sesión 2)

`routers/` (HTTP, finos) → `services/llm_service.py` (prompt + contexto + llamada al LLM) ← `context/examples.py`
(estimaciones de referencia: el punto que cambiará por RAG). Config en `app/config.py` con pydantic-settings:
`LLM_PROVIDER` elige proveedor y la app no arranca sin su API key.

## Reglas

- **El código de los ejercicios lo escribe el alumno**; Claude guía y revisa, salvo que se le pida la solución.
- **Sin comentarios ni docstrings en el código.** El porqué de una decisión va en el commit o en el README.
- Commits atómicos en inglés con Conventional Commits. Commit, push y PR solo con OK explícito.
- **Antes de abrir el PR de cada ejercicio**: `uv run ruff check . && uv run pytest` en verde y `/code-review`
  sobre el diff; se corrige lo que salga (lo corrige el alumno) antes de mandar el enlace.
- Nada de secretos: claves en `estimador-cag/.env` (ignorado) y `.env.example` sin valores. Datos de ejemplo,
  siempre inventados.
- CI (`.github/workflows/estimador-cag.yml`): ruff, pytest y build de la imagen Docker en cada PR.
