from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError

from app.context.models import EstimationExample, RateCard
from app.data_files import DataFileError, read_yaml

DATA_DIR = Path(__file__).parent / "data"


class ContextDataError(DataFileError):
    pass


def load_rate_card(path: Path = DATA_DIR / "rates.yaml") -> RateCard:
    try:
        return RateCard.model_validate(read_yaml(path))
    except ValidationError as error:
        raise ContextDataError(f"{path.name}: {error}") from error


def load_examples(
    directory: Path = DATA_DIR / "examples", rate_card: RateCard | None = None
) -> list[EstimationExample]:
    rate_card = rate_card or load_rate_card()
    examples = []
    for path in sorted(directory.glob("*.yaml")):
        try:
            example = EstimationExample.model_validate(read_yaml(path))
            example.check_roles(rate_card)
            issues = example.capacity_issues(rate_card)
            if issues:
                raise ValueError("; ".join(issues))
        except (ValidationError, ValueError) as error:
            raise ContextDataError(f"{path.name}: {error}") from error
        examples.append(example)

    if not examples:
        raise ContextDataError(f"no hay ejemplos en {directory}")
    ids = [example.id for example in examples]
    if len(ids) != len(set(ids)):
        raise ContextDataError(f"ids de ejemplo repetidos: {ids}")
    return examples


@lru_cache
def get_rate_card() -> RateCard:
    return load_rate_card()


@lru_cache
def get_examples() -> tuple[EstimationExample, ...]:
    return tuple(load_examples(rate_card=get_rate_card()))
