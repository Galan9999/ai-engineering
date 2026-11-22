import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol

import anthropic
import openai
from anthropic import AsyncAnthropic
from anthropic.types import ToolUseBlock
from openai import AsyncOpenAI

from app.config import Settings, get_settings


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class GenerationParams:
    max_tokens: int
    temperature: float | None = None


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    schema: dict[str, Any]


@dataclass(frozen=True)
class ProviderResponse:
    arguments: dict[str, Any] | None
    provider: str
    model: str
    stop_reason: str | None
    truncated: bool
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int = 0
    cache_write_tokens: int = 0


class LLMProvider(Protocol):
    name: str

    async def call_tool(
        self, system: str, user: str, tool: ToolSpec, params: GenerationParams
    ) -> ProviderResponse: ...


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def call_tool(
        self, system: str, user: str, tool: ToolSpec, params: GenerationParams
    ) -> ProviderResponse:
        try:
            response = await self._create(system, user, tool, params)
        except openai.APIError as error:
            raise ProviderError(f"openai: {error}") from error
        choice = response.choices[0]
        arguments = None
        for call in choice.message.tool_calls or []:
            if call.type == "function" and call.function.name == tool.name:
                arguments = _parse_json(call.function.arguments)
        usage = response.usage
        details = usage.prompt_tokens_details if usage else None
        return ProviderResponse(
            arguments=arguments,
            provider=self.name,
            model=response.model,
            stop_reason=choice.finish_reason,
            truncated=choice.finish_reason == "length",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            cached_input_tokens=(details.cached_tokens or 0) if details else 0,
        )

    async def _create(self, system: str, user: str, tool: ToolSpec, params: GenerationParams):
        return await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.schema,
                    },
                }
            ],
            tool_choice={"type": "function", "function": {"name": tool.name}},
            temperature=params.temperature,
            max_tokens=params.max_tokens,
        )


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def call_tool(
        self, system: str, user: str, tool: ToolSpec, params: GenerationParams
    ) -> ProviderResponse:
        try:
            response = await self._create(system, user, tool, params)
        except anthropic.APIError as error:
            raise ProviderError(f"anthropic: {error}") from error
        arguments = None
        for block in response.content:
            if isinstance(block, ToolUseBlock) and block.name == tool.name:
                arguments = block.input if isinstance(block.input, dict) else None
        usage = response.usage
        cache_read = usage.cache_read_input_tokens or 0
        cache_write = usage.cache_creation_input_tokens or 0
        return ProviderResponse(
            arguments=arguments,
            provider=self.name,
            model=response.model,
            stop_reason=response.stop_reason,
            truncated=response.stop_reason == "max_tokens",
            input_tokens=usage.input_tokens + cache_read + cache_write,
            output_tokens=usage.output_tokens,
            cached_input_tokens=cache_read,
            cache_write_tokens=cache_write,
        )

    async def _create(self, system: str, user: str, tool: ToolSpec, params: GenerationParams):
        return await self._client.messages.create(
            model=self._model,
            max_tokens=params.max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            tools=[
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.schema,
                }
            ],
            tool_choice={"type": "tool", "name": tool.name},
        )


def _parse_json(raw: str) -> dict[str, Any] | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def build_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "anthropic":
        assert settings.anthropic_api_key
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model,
        )
    assert settings.openai_api_key
    return OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.llm_model,
    )


@lru_cache
def get_provider() -> LLMProvider:
    return build_provider(get_settings())
