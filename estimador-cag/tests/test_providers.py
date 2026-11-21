import asyncio
from types import SimpleNamespace
from typing import Any

from anthropic.types import ToolUseBlock

from app.services.providers import AnthropicProvider, GenerationParams, ToolSpec

TOOL = ToolSpec(name="submit_estimation", description="d", schema={"type": "object"})
PARAMS = GenerationParams(max_tokens=3000, temperature=0.3)


class FakeMessages:
    def __init__(self, response: Any):
        self.response = response
        self.kwargs: dict[str, Any] = {}

    async def create(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        return self.response


def anthropic_response() -> SimpleNamespace:
    block = ToolUseBlock.model_construct(
        id="toolu_1", name="submit_estimation", input={"title": "x"}, type="tool_use"
    )
    usage = SimpleNamespace(
        input_tokens=100,
        output_tokens=50,
        cache_read_input_tokens=4000,
        cache_creation_input_tokens=0,
    )
    return SimpleNamespace(
        content=[block], usage=usage, model="claude-haiku-4-5-20251001", stop_reason="tool_use"
    )


def call(monkeypatch) -> tuple[Any, FakeMessages]:
    provider = AnthropicProvider(api_key="test", model="claude-haiku-4-5")
    messages = FakeMessages(anthropic_response())
    monkeypatch.setattr(provider, "_client", SimpleNamespace(messages=messages))
    result = asyncio.run(provider.call_tool("SYSTEM", "USER", TOOL, PARAMS))
    return result, messages


def test_anthropic_request_caches_prompt_and_forces_the_tool(monkeypatch):
    _, messages = call(monkeypatch)

    assert messages.kwargs["cache_control"] == {"type": "ephemeral"}
    assert messages.kwargs["tool_choice"] == {"type": "tool", "name": "submit_estimation"}
    assert messages.kwargs["system"] == "SYSTEM"
    assert messages.kwargs["messages"] == [{"role": "user", "content": "USER"}]
    assert messages.kwargs["max_tokens"] == 3000
    assert "temperature" not in messages.kwargs


def test_anthropic_usage_counts_cached_tokens_in_the_input(monkeypatch):
    result, _ = call(monkeypatch)

    assert result.arguments == {"title": "x"}
    assert result.input_tokens == 4100
    assert result.cached_input_tokens == 4000
    assert result.cache_write_tokens == 0
