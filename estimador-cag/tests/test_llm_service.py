import asyncio

import pytest

from app.context.examples import get_examples, get_rate_card
from app.services.llm_service import LLMOutputError, generate_estimation
from app.services.markdown import render_markdown
from app.services.prompt import build_system_prompt, build_user_message, estimation_schema
from tests.fakes import GOOD_ESTIMATION, FakeProvider

TRANSCRIPTION = "El cliente quiere una web de reservas para su escuela de surf con pagos online."


def run(provider: FakeProvider):
    return asyncio.run(generate_estimation(TRANSCRIPTION, provider=provider))


def test_system_prompt_wraps_every_example_in_xml():
    prompt = build_system_prompt(get_examples(), get_rate_card())

    assert prompt.count("<example id=") == len(get_examples())
    for example in get_examples():
        assert f'<example id="{example.id}">' in prompt
    assert (
        prompt.index("<instructions>") < prompt.index("<examples>") < prompt.index("<constraints>")
    )


def test_examples_in_prompt_do_not_carry_costs_or_ids():
    prompt = build_system_prompt(get_examples(), get_rate_card())

    assert '"cost"' not in prompt
    assert '"id"' not in prompt


def test_user_message_contains_only_the_transcription():
    assert build_user_message(f"  {TRANSCRIPTION}\n") == (
        f"<transcription>\n{TRANSCRIPTION}\n</transcription>"
    )


def test_schema_limits_roles_to_the_rate_card():
    schema = estimation_schema(get_rate_card())

    roles = schema["$defs"]["Task"]["properties"]["role"]["enum"]
    assert roles == sorted(get_rate_card().rates)


def test_service_sends_system_and_user_and_computes_costs():
    provider = FakeProvider(GOOD_ESTIMATION)

    result = run(provider)

    [call] = provider.calls
    assert "<examples>" in call["system"]
    assert TRANSCRIPTION in call["user"]
    assert result.total_hours == 110
    assert result.total_cost == 30 * 50 + 80 * 65
    assert result.warnings == []


def test_capacity_problem_is_a_warning_not_an_error():
    provider = FakeProvider({**GOOD_ESTIMATION, "duration_weeks": {"min": 1, "max": 1}})

    result = run(provider)

    assert any("no llega en backend" in warning for warning in result.warnings)


@pytest.mark.parametrize(
    ("provider", "message"),
    [
        (FakeProvider(None), "no devolvió"),
        (FakeProvider(GOOD_ESTIMATION, truncated=True), "límite de tokens"),
        (FakeProvider({**GOOD_ESTIMATION, "tasks": []}), "no es válida"),
        (
            FakeProvider(
                {
                    **GOOD_ESTIMATION,
                    "tasks": [{"name": "Magia", "role": "wizard", "hours": 10}],
                    "team": [{"role": "wizard"}],
                }
            ),
            "roles sin tarifa",
        ),
    ],
    ids=["no-tool-call", "truncated", "empty-tasks", "unknown-role"],
)
def test_bad_model_output_raises(provider, message):
    with pytest.raises(LLMOutputError, match=message):
        run(provider)


def test_markdown_shows_tasks_totals_team_and_duration():
    result = run(FakeProvider(GOOD_ESTIMATION))

    markdown = render_markdown(result.estimation, result.rate_card)

    assert markdown.startswith("## Estimación: Web de reservas")
    assert "| Reservas y pagos | backend | 80 | 5.200 EUR |" in markdown
    assert "**Total estimado: 110 horas · 6.700 EUR**" in markdown
    assert "- 1 × product_designer (50% de dedicación)" in markdown
    assert "**Duración estimada: 3-4 semanas**" in markdown


def test_markdown_shows_a_single_number_when_min_equals_max():
    result = run(FakeProvider({**GOOD_ESTIMATION, "duration_weeks": {"min": 4, "max": 4}}))

    assert "**Duración estimada: 4 semanas**" in render_markdown(
        result.estimation, result.rate_card
    )
