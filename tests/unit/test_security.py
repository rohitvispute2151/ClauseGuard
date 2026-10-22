import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_key_not_required_when_unset(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "")
    assert client.post("/api/v1/documents", files={"file": ("a.txt", b"x", "text/plain")}).status_code == 400


def test_api_key_enforced_when_set(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "s3cret")
    files = {"file": ("a.txt", b"x", "text/plain")}
    assert client.post("/api/v1/documents", files=files).status_code == 401
    assert client.post("/api/v1/documents", files=files, headers={"X-API-Key": "wrong"}).status_code == 401
    # valid key gets past auth and reaches the handler (which rejects the non-PDF)
    assert client.post("/api/v1/documents", files=files, headers={"X-API-Key": "s3cret"}).status_code == 400


def test_health_stays_public(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "s3cret")
    assert client.get("/api/v1/health").status_code == 200


def test_upload_quota_returns_429_with_cors_headers(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "")
    monkeypatch.setattr(settings, "QUOTA_UPLOADS", 2)
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)
    files = {"file": ("a.txt", b"x", "text/plain")}
    hdr = {"X-Forwarded-For": "203.0.113.77", "Origin": "http://localhost:5173"}
    codes = [client.post("/api/v1/documents", files=files, headers=hdr).status_code for _ in range(3)]
    assert codes == [400, 400, 429]
    blocked = client.post("/api/v1/documents", files=files, headers=hdr)
    assert "Retry-After" in blocked.headers
    assert blocked.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_spoofed_forwarded_entries_do_not_evade_quota(client, monkeypatch):
    monkeypatch.setattr(settings, "API_KEY", "")
    monkeypatch.setattr(settings, "QUOTA_UPLOADS", 1)
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 1)
    files = {"file": ("a.txt", b"x", "text/plain")}
    # Same real IP (right-most), different spoofed left-most entries.
    first = client.post("/api/v1/documents", files=files, headers={"X-Forwarded-For": "1.1.1.1, 198.51.100.9"})
    second = client.post("/api/v1/documents", files=files, headers={"X-Forwarded-For": "2.2.2.2, 198.51.100.9"})
    assert (first.status_code, second.status_code) == (400, 429)


def test_cors_rejects_unlisted_origin(client):
    res = client.get("/api/v1/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in res.headers


def test_production_rejects_wildcard_cors():
    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production", CORS_ORIGINS="*", _env_file=None)
