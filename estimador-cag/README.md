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

## Uso

```bash
curl -X POST http://localhost:8000/api/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{"transcription": "En la reunión con el equipo de marketing, el cliente explicó que necesita una landing page con formulario de contacto, integración con su CRM actual (HubSpot), y una sección de blog con editor WYSIWYG. El plazo ideal sería tenerlo listo en 4 semanas. El diseño ya existe en Figma."}'
```

La respuesta trae `estimation` (Markdown), `model` y `provider`, y además `details` (tareas con coste,
equipo, duración y totales), `warnings` (incoherencias de capacidad), `usage` (tokens y coste en USD),
`latency_ms` y `created_at`. Errores: `422` si la transcripción no es válida (50-20.000 caracteres) y
`502` si el modelo o el proveedor fallan.

## Cómo funciona

1. `context/` carga y valida al arrancar las estimaciones de referencia (`data/examples/*.yaml`) y las
   tarifas por rol (`data/rates.yaml`).
2. `services/prompt.py` monta el system prompt con los ejemplos en `<example>` y la transcripción como
   mensaje de usuario.
3. `services/providers.py` llama a OpenAI o Anthropic (`LLM_PROVIDER`) forzando la herramienta
   `submit_estimation`, cuyo esquema es el modelo `Estimation`.
4. `services/llm_service.py` valida la respuesta con Pydantic; horas, costes y totales los calcula el
   código, no el modelo. `services/pricing.py` calcula el coste de la llamada con `data/pricing.yaml`.

## Estructura

```
app/
├── main.py                  app, routers y /health
├── config.py                configuración con pydantic-settings (falla si falta la key)
├── schemas/estimation.py    contratos de entrada y salida de la API
├── routers/estimations.py   POST /api/v1/estimate
├── services/                prompt, adapter de proveedores, servicio, Markdown y precios
└── context/                 modelos, loader y datos YAML (ejemplos y tarifas)
```

## Mejoras pendientes

- **Productividad con IA.** Los ejemplos reflejan horas de proyectos hechos sin agentes de IA y hoy se
  sobrestimaría. Propuesta: un campo `delivery: traditional | ai_assisted` en cada ejemplo (el hecho) y un
  factor `ai_productivity` por rol en `rates.yaml` (la suposición) que ajuste las horas de los ejemplos
  `traditional` al cargarlos. Con RAG, `delivery` y la fecha del proyecto servirán para filtrar la búsqueda.
- **Autocorrección de la estimación.** Hoy, si el equipo propuesto no llega a las horas de algún rol, la
  respuesta lo devuelve en `warnings`. Propuesta: cuando haya avisos, reenviar al modelo su estimación con
  los avisos para que la corrija (máximo un reintento), decidiendo él si añade personas o alarga el plazo.
  Es el patrón validar → feedback → reintentar: el código comprueba y el modelo corrige.
- **Robustez del adapter.** Pendientes de la revisión de código: dar a los clientes de OpenAI y Anthropic un
  timeout corto (hoy usan el del SDK, 10 minutos con reintentos) y devolver `502` si OpenAI responde sin
  `choices`; enviar `max_completion_tokens` en lugar de `max_tokens`, para que funcionen los modelos de
  razonamiento de OpenAI; y mostrar las horas con un decimal en el Markdown, para que las filas sumen el
  total.
