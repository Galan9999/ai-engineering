from fastapi.testclient import TestClient

from app.context.examples import get_examples, get_rate_card
from app.main import app
from app.services.pricing import get_pricing

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_docs_are_available():
    assert client.get("/docs").status_code == 200


def test_context_and_pricing_are_loaded_when_the_app_starts():
    for loader in (get_rate_card, get_examples, get_pricing):
        assert loader.cache_info().currsize == 1
