from fastapi.testclient import TestClient

from app.main import app


def test_client() -> TestClient:
    return TestClient(app)
