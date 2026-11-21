from pathlib import Path

import pytest
import yaml

from app.context.examples import ContextDataError, get_examples, get_rate_card, load_examples
from app.context.models import RateCard

RATE_CARD = RateCard(currency="EUR", hours_per_week=35, rates={"backend": 65, "qa": 45})

VALID_EXAMPLE = {
    "id": "demo",
    "title": "Proyecto de prueba",
    "sector": "pruebas",
    "meeting_summary": (
        "El cliente necesita una API sencilla para gestionar reservas de salas de reuniones."
    ),
    "tasks": [
        {"name": "API de reservas", "role": "backend", "hours": 60},
        {"name": "Pruebas", "role": "qa", "hours": 20},
    ],
    "team": [{"role": "backend"}, {"role": "qa", "dedication": 0.5}],
    "duration_weeks": {"min": 2, "max": 3},
}


def write_example(directory: Path, data: dict, name: str = "demo.yaml") -> None:
    (directory / name).write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def with_changes(**changes) -> dict:
    return {**VALID_EXAMPLE, **changes}


def test_real_examples_load_and_are_diverse():
    examples = get_examples()

    assert len(examples) >= 2
    assert len({example.sector for example in examples}) == len(examples)


def test_real_examples_have_positive_totals():
    rate_card = get_rate_card()

    for example in get_examples():
        assert example.total_hours > 0
        assert example.total_cost(rate_card) > 0


def test_totals_are_computed_from_tasks(tmp_path):
    write_example(tmp_path, VALID_EXAMPLE)

    [example] = load_examples(tmp_path, RATE_CARD)

    assert example.total_hours == 80
    assert example.total_cost(RATE_CARD) == 60 * 65 + 20 * 45


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"tasks": [{"name": "API", "role": "backend", "hours": "cuarenta"}]}, "hours"),
        ({"tasks": [{"name": "API", "role": "backend", "hous": 10}]}, "hous"),
        ({"tasks": [{"name": "Diseño", "role": "designer", "hours": 10}]}, "designer"),
        ({"team": [{"role": "backend"}]}, "qa"),
        ({"duration_weeks": {"min": 4, "max": 2}}, "min"),
        ({"duration_weeks": {"min": 1, "max": 1}}, "no llega en backend"),
        (
            {
                "team": [{"role": "backend", "count": 3}, {"role": "qa", "dedication": 0.1}],
                "duration_weeks": {"min": 3, "max": 3},
            },
            "no llega en qa",
        ),
    ],
    ids=[
        "hours-not-number",
        "typo-in-field",
        "role-without-rate",
        "team-missing-role",
        "min-gt-max",
        "capacity",
        "bottleneck-in-one-role",
    ],
)
def test_invalid_example_fails_with_file_name(tmp_path, changes, message):
    write_example(tmp_path, with_changes(**changes), name="roto.yaml")

    with pytest.raises(ContextDataError, match="roto.yaml") as error:
        load_examples(tmp_path, RATE_CARD)

    assert message in str(error.value)


def test_empty_directory_fails(tmp_path):
    with pytest.raises(ContextDataError, match="no hay ejemplos"):
        load_examples(tmp_path, RATE_CARD)


def test_duplicated_ids_fail(tmp_path):
    write_example(tmp_path, VALID_EXAMPLE, name="a.yaml")
    write_example(tmp_path, VALID_EXAMPLE, name="b.yaml")

    with pytest.raises(ContextDataError, match="repetidos"):
        load_examples(tmp_path, RATE_CARD)
