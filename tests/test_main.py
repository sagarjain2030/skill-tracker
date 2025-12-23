from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_redirects_to_docs():
    """Test that root redirects to API documentation."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/docs"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_favicon():
    response = client.get("/favicon.ico")
    assert response.status_code == 204


def test_version():
    """Test version endpoint returns deployment info."""
    response = client.get("/version")
    assert response.status_code == 200

    data = response.json()
    assert "commit" in data
    assert "service" in data
    assert "version" in data
