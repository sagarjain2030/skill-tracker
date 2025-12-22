from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_get():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_head():
    response = client.head("/")
    assert response.status_code == 200


def test_favicon():
    response = client.get("/favicon.ico")
    assert response.status_code == 204


def test_version():
    response = client.get("/version")
    assert response.status_code == 200

    data = response.json()
    assert "commit" in data
    assert "service" in data
