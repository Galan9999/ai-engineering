from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_MODELS = {"openai": "gpt-4o-mini", "anthropic": "claude-haiku-4-5"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)

    llm_provider: Literal["openai", "anthropic"] = "openai"
    llm_model: str = ""
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    @model_validator(mode="after")
    def check_api_key(self) -> "Settings":
        key = self.openai_api_key if self.llm_provider == "openai" else self.anthropic_api_key
        if not key:
            raise ValueError(f"Falta la API key de {self.llm_provider} en el .env")
        if not self.llm_model:
            self.llm_model = DEFAULT_MODELS[self.llm_provider]
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
