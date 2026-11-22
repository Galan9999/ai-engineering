from datetime import date

import pytest

from app.config import DEFAULT_MODELS
from app.services.pricing import ModelPrice, PricingTable, get_pricing

PRICE = ModelPrice(
    provider="openai",
    input_per_mtok=0.15,
    cached_input_per_mtok=0.075,
    output_per_mtok=0.60,
    source="https://example.com",
)


def test_real_pricing_file_loads_and_covers_the_default_models():
    for model in DEFAULT_MODELS.values():
        assert get_pricing().price_for(model) is not None


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("gpt-4o-mini", "gpt-4o-mini"),
        ("gpt-4o-mini-2024-07-18", "gpt-4o-mini"),
        ("claude-haiku-4-5", "claude-haiku-4-5"),
        ("claude-haiku-4-5-20251001", "claude-haiku-4-5"),
    ],
)
def test_price_lookup_accepts_dated_snapshots(model, expected):
    pricing = get_pricing()

    assert pricing.price_for(model) == pricing.models[expected]


def test_unknown_model_has_no_price():
    assert get_pricing().price_for("modelo-inventado") is None


def test_only_a_date_suffix_is_ignored():
    table = PricingTable(currency="USD", checked_at=date(2026, 11, 21), models={"gpt-4o": PRICE})

    assert table.price_for("gpt-4o-mini") is None
    assert table.price_for("gpt-4o-2024-08-06") == PRICE


def test_cost_charges_cached_tokens_at_the_cached_rate():
    cost = PRICE.cost(input_tokens=4000, cached_input_tokens=3000, output_tokens=500)

    assert cost == pytest.approx((1000 * 0.15 + 3000 * 0.075 + 500 * 0.60) / 1_000_000)


def test_cache_writes_use_the_write_rate_or_fall_back_to_input():
    with_write = ModelPrice(
        provider="anthropic",
        input_per_mtok=1.0,
        cached_input_per_mtok=0.1,
        cache_write_per_mtok=1.25,
        output_per_mtok=5.0,
        source="https://example.com",
    )

    assert with_write.cost(6000, 0, 1000, cache_write_tokens=5000) == pytest.approx(
        (1000 * 1.0 + 5000 * 1.25 + 1000 * 5.0) / 1_000_000
    )
    assert PRICE.cost(4000, 0, 0, cache_write_tokens=4000) == pytest.approx(4000 * 0.15 / 1_000_000)


def test_free_cache_writes_are_not_charged_at_the_input_rate():
    free_write = PRICE.model_copy(update={"cache_write_per_mtok": 0.0})

    assert free_write.cost(4000, 0, 0, cache_write_tokens=4000) == 0
