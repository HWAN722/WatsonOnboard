"""Integration tests for health endpoint."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint returns expected response."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "WatsonOnboard API"
    assert data["version"] == "0.1.0"
    assert "docs" in data


def test_health_endpoint(client):
    """Test health endpoint returns ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "watsonx" in data

# Made with Bob
