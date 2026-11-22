from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.context.models import DurationWeeks, TeamMember
from app.services.llm_service import EstimationResult
from app.services.markdown import render_markdown

EXAMPLE_TRANSCRIPTION = (
    "En la reunión con el equipo de marketing, el cliente explicó que necesita una landing page "
    "con formulario de contacto, integración con su CRM actual (HubSpot), y una sección de blog "
    "con editor WYSIWYG. El plazo ideal sería tenerlo listo en 4 semanas. El diseño ya existe en "
    "Figma."
)


class EstimationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    transcription: str = Field(
        min_length=50,
        max_length=20_000,
        description="Transcripción de la reunión con el cliente.",
        examples=[EXAMPLE_TRANSCRIPTION],
    )


class TaskOut(BaseModel):
    name: str
    role: str
    hours: float
    cost: float


class EstimationDetails(BaseModel):
    title: str
    tasks: list[TaskOut]
    team: list[TeamMember]
    duration_weeks: DurationWeeks
    notes: str | None
    total_hours: float
    total_cost: float
    currency: str


class Usage(BaseModel):
    input_tokens: int
    cached_input_tokens: int
    cache_write_tokens: int
    output_tokens: int
    cost_usd: float | None


class EstimationResponse(BaseModel):
    estimation: str
    model: str
    provider: str
    details: EstimationDetails
    warnings: list[str]
    usage: Usage
    latency_ms: int
    created_at: datetime

    @classmethod
    def from_result(
        cls, result: EstimationResult, latency_ms: int, created_at: datetime
    ) -> "EstimationResponse":
        estimation, rate_card, response = result.estimation, result.rate_card, result.response
        return cls(
            estimation=render_markdown(estimation, rate_card),
            model=response.model,
            provider=response.provider,
            details=EstimationDetails(
                title=estimation.title,
                tasks=[
                    TaskOut(
                        name=task.name,
                        role=task.role,
                        hours=task.hours,
                        cost=task.cost(rate_card),
                    )
                    for task in estimation.tasks
                ],
                team=estimation.team,
                duration_weeks=estimation.duration_weeks,
                notes=estimation.notes,
                total_hours=result.total_hours,
                total_cost=result.total_cost,
                currency=rate_card.currency,
            ),
            warnings=result.warnings,
            usage=Usage(
                input_tokens=response.input_tokens,
                cached_input_tokens=response.cached_input_tokens,
                cache_write_tokens=response.cache_write_tokens,
                output_tokens=response.output_tokens,
                cost_usd=None if result.llm_cost_usd is None else round(result.llm_cost_usd, 6),
            ),
            latency_ms=latency_ms,
            created_at=created_at,
        )
