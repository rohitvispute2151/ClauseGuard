from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "primary_provider" in data
    assert "gemini" in data["primary_provider"]
    assert "groq" in data["fallback_provider"]


def test_upload_rejects_non_pdf():
    response = client.post(
        "/api/v1/documents",
        files={"file": ("contract.txt", b"plain text contract", "text/plain")},
    )
    assert response.status_code == 400
    assert "Only PDF files" in response.json()["detail"]


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "python_gc_collections_total" in response.text or "clauseguard" in response.text
