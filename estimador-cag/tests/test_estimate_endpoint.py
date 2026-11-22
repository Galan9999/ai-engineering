from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.estimation import EXAMPLE_TRANSCRIPTION
from app.services.providers import get_provider
from tests.fakes import GOOD_ESTIMATION, FakeProvider, failing_provider


@pytest.fixture
def use_provider() -> Iterator:
    def install(provider: FakeProvider) -> TestClient:
        app.dependency_overrides[get_provider] = lambda: provider
        return TestClient(app)

    yield install
    app.dependency_overrides.clear()


def post(client: TestClient, transcription: str = EXAMPLE_TRANSCRIPTION):
    return client.post("/api/v1/estimate", json={"transcription": transcription})


def test_returns_estimation_with_contract_fields(use_provider):
    client = use_provider(FakeProvider(GOOD_ESTIMATION, model="gpt-4o-mini-2024-07-18"))

    response = post(client)

    assert response.status_code == 200
    body = response.json()
    assert body["estimation"].startswith("## Estimación: Web de reservas")
    assert body["model"] == "gpt-4o-mini-2024-07-18"
    assert body["provider"] == "fake"


def test_returns_details_usage_and_timing(use_provider):
    client = use_provider(FakeProvider(GOOD_ESTIMATION, model="gpt-4o-mini-2024-07-18"))

    body = post(client).json()

    assert body["details"]["total_hours"] == 110
    assert body["details"]["total_cost"] == 6700
    assert body["details"]["currency"] == "EUR"
    assert body["details"]["tasks"][1] == {
        "name": "Reservas y pagos",
        "role": "backend",
        "hours": 80,
        "cost": 5200,
    }
    assert body["usage"] == {
        "input_tokens": 4000,
        "cached_input_tokens": 3000,
        "cache_write_tokens": 0,
        "output_tokens": 300,
        "cost_usd": 0.000555,
    }
    assert body["latency_ms"] >= 0
    assert body["created_at"].endswith("Z")


def test_sends_the_transcription_to_the_provider(use_provider):
    provider = FakeProvider(GOOD_ESTIMATION)
    client = use_provider(provider)

    post(client, f"   {EXAMPLE_TRANSCRIPTION}   ")

    [call] = provider.calls
    assert EXAMPLE_TRANSCRIPTION in call["user"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"transcription": "demasiado corta"},
        {"transcription": " " * 60},
        {"transcription": "x" * 20_001},
        {"transcription": EXAMPLE_TRANSCRIPTION, "extra": True},
    ],
    ids=["missing", "too-short", "only-spaces", "too-long", "unknown-field"],
)
def test_invalid_request_is_422_and_never_calls_the_llm(use_provider, payload):
    provider = FakeProvider(GOOD_ESTIMATION)
    client = use_provider(provider)

    response = client.post("/api/v1/estimate", json=payload)

    assert response.status_code == 422
    assert provider.calls == []


@pytest.mark.parametrize(
    "provider",
    [FakeProvider(None), FakeProvider(GOOD_ESTIMATION, truncated=True), failing_provider()],
    ids=["no-estimation", "truncated", "provider-down"],
)
def test_llm_failures_are_502(use_provider, provider):
    response = post(use_provider(provider))

    assert response.status_code == 502
    assert response.json()["detail"]


def test_endpoint_is_documented_in_openapi(use_provider):
    schema = use_provider(FakeProvider(GOOD_ESTIMATION)).get("/openapi.json").json()

    assert "/api/v1/estimate" in schema["paths"]
