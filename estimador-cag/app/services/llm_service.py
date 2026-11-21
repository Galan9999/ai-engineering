from dataclasses import dataclass

from pydantic import ValidationError

from app.context.examples import get_examples, get_rate_card
from app.context.models import Estimation, RateCard
from app.services.prompt import (
    TOOL_DESCRIPTION,
    TOOL_NAME,
    build_system_prompt,
    build_user_message,
    estimation_schema,
)
from app.services.providers import LLMProvider, ProviderResponse, ToolSpec, get_provider


class LLMOutputError(RuntimeError):
    pass


@dataclass(frozen=True)
class EstimationResult:
    estimation: Estimation
    rate_card: RateCard
    warnings: list[str]
    response: ProviderResponse

    @property
    def total_hours(self) -> float:
        return self.estimation.total_hours

    @property
    def total_cost(self) -> float:
        return self.estimation.total_cost(self.rate_card)


async def generate_estimation(
    transcription: str, provider: LLMProvider | None = None
) -> EstimationResult:
    rate_card = get_rate_card()
    provider = provider or get_provider()
    tool = ToolSpec(
        name=TOOL_NAME, description=TOOL_DESCRIPTION, schema=estimation_schema(rate_card)
    )

    response = await provider.call_tool(
        system=build_system_prompt(get_examples(), rate_card),
        user=build_user_message(transcription),
        tool=tool,
    )

    if response.truncated:
        raise LLMOutputError("la respuesta del modelo se cortó por el límite de tokens")
    if response.arguments is None:
        raise LLMOutputError("el modelo no devolvió la estimación")

    try:
        estimation = Estimation.model_validate(response.arguments)
        estimation.check_roles(rate_card)
    except (ValidationError, ValueError) as error:
        raise LLMOutputError(f"la estimación del modelo no es válida: {error}") from error

    return EstimationResult(
        estimation=estimation,
        rate_card=rate_card,
        warnings=estimation.capacity_issues(rate_card),
        response=response,
    )
