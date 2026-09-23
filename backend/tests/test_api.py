"""Smoke tests for the FastAPI application — Phase 0 acceptance criteria."""

# pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root():
    """Root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


def test_health_check():
    """Health endpoint returns 200 with status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


def test_chat_stub():
    """Chat endpoint returns stub response."""
    response = client.post("/api/v1/chat")
    assert response.status_code == 200
    assert "not_implemented" in response.json().get("status", "")


def test_scrape_trigger_stub():
    """Scrape trigger returns stub response."""
    response = client.post("/api/v1/scrape/trigger")
    assert response.status_code == 200


def test_scrape_status_stub():
    """Scrape status returns empty jobs."""
    response = client.get("/api/v1/scrape/status")
    assert response.status_code == 200
    assert response.json()["jobs"] == []


def test_citations_stub():
    """Citation lookup returns stub response."""
    response = client.get("/api/v1/citations/test-id")
    assert response.status_code == 200


def test_data_reviews_stub():
    """Data reviews returns empty list."""
    response = client.get("/api/v1/data/reviews")
    assert response.status_code == 200
    assert response.json()["total"] == 0
