from typing import Any

from app.services.providers import GenerationParams, ProviderError, ProviderResponse, ToolSpec

GOOD_ESTIMATION = {
    "title": "Web de reservas para una escuela de surf",
    "tasks": [
        {"name": "Diseño de la web", "role": "product_designer", "hours": 30},
        {"name": "Reservas y pagos", "role": "backend", "hours": 80},
    ],
    "team": [{"role": "product_designer", "dedication": 0.5}, {"role": "backend"}],
    "duration_weeks": {"min": 3, "max": 4},
    "notes": "Supone un único idioma.",
}


class FakeProvider:
    name = "fake"

    def __init__(
        self,
        arguments: dict[str, Any] | None = None,
        truncated: bool = False,
        model: str = "fake-model",
        error: Exception | None = None,
    ):
        self.arguments = arguments
        self.truncated = truncated
        self.model = model
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def call_tool(
        self, system: str, user: str, tool: ToolSpec, params: GenerationParams
    ) -> ProviderResponse:
        self.calls.append({"system": system, "user": user, "tool": tool, "params": params})
        if self.error:
            raise self.error
        return ProviderResponse(
            arguments=self.arguments,
            provider=self.name,
            model=self.model,
            stop_reason="length" if self.truncated else "tool_use",
            truncated=self.truncated,
            input_tokens=4000,
            output_tokens=300,
            cached_input_tokens=3000,
        )


def failing_provider() -> FakeProvider:
    return FakeProvider(error=ProviderError("openai: Connection error."))
