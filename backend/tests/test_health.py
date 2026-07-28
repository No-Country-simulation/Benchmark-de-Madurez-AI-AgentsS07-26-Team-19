from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint():
    app = create_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
