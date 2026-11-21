import pytest
from pydantic import ValidationError

from app.config import Settings

ENV_EXAMPLE_KEYS = [
    "LLM_PROVIDER",
    "LLM_MODEL",
    "ANTHROPIC_API_KEY",
    "LLM_TEMPERATURE",
    "LLM_MAX_TOKENS",
]


def test_empty_variables_fall_back_to_defaults(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ENV_EXAMPLE_KEYS:
        monkeypatch.setenv(key, "")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    settings = Settings()

    assert settings.llm_provider == "openai"
    assert settings.llm_model == "gpt-4o-mini"
    assert settings.llm_temperature == 0.3
    assert settings.llm_max_tokens == 3000


def test_empty_api_key_still_fails_fast(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    with pytest.raises(ValidationError, match="Falta la API key de openai"):
        Settings()
