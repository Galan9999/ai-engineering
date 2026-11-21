import re
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, ValidationError

from app.data_files import DataFileError, read_yaml

PRICING_FILE = Path(__file__).parent / "data" / "pricing.yaml"
PER_MILLION = 1_000_000
DATE_SUFFIX = re.compile(r"-\d{4}-?\d{2}-?\d{2}$")


class ModelPrice(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: Literal["openai", "anthropic"]
    input_per_mtok: NonNegativeFloat
    cached_input_per_mtok: NonNegativeFloat
    output_per_mtok: NonNegativeFloat
    source: str

    def cost(self, input_tokens: int, cached_input_tokens: int, output_tokens: int) -> float:
        uncached = max(input_tokens - cached_input_tokens, 0)
        return (
            uncached * self.input_per_mtok
            + cached_input_tokens * self.cached_input_per_mtok
            + output_tokens * self.output_per_mtok
        ) / PER_MILLION


class PricingTable(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    currency: str
    checked_at: date
    models: dict[str, ModelPrice] = Field(min_length=1)

    def price_for(self, model: str) -> ModelPrice | None:
        return self.models.get(model) or self.models.get(DATE_SUFFIX.sub("", model))


def load_pricing(path: Path = PRICING_FILE) -> PricingTable:
    try:
        return PricingTable.model_validate(read_yaml(path))
    except ValidationError as error:
        raise DataFileError(f"{path.name}: {error}") from error


@lru_cache
def get_pricing() -> PricingTable:
    return load_pricing()
