from functools import lru_cache
from typing import Literal

from pydantic import Field, PositiveInt, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: Literal["openai", "anthropic"] = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = Field(default=0.3, ge=0, le=2)
    llm_max_tokens: PositiveInt = 3000
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    @model_validator(mode="after")
    def check_api_key(self) -> "Settings":
        key = self.openai_api_key if self.llm_provider == "openai" else self.anthropic_api_key
        if not key:
            raise ValueError(f"Falta la API key de {self.llm_provider} en el .env")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
