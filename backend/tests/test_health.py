from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.deps import get_ai_client
from app.main import create_app
from app.services.ai_client import AiClient


def test_health_endpoint():
    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_ai_health_endpoint():
    app = create_app()
    fake = AsyncMock(spec=AiClient)
    fake.health_check = AsyncMock(return_value=True)
    app.dependency_overrides[get_ai_client] = lambda: fake
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/health/ai")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
