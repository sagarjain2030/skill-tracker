from fastapi.testclient import TestClient
from app.main import app   # adjust ONLY if your path is different

client = TestClient(app)

def test_health():
    response = client.get("/")
    assert response.status_code == 200
