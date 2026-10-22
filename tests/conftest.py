import pytest

from app.core.config import settings
from app.middleware import quota


@pytest.fixture(autouse=True)
def _isolate_security_settings(monkeypatch):
    """Tests must not depend on a developer's local .env (API_KEY, proxy hops, quotas)."""
    monkeypatch.setattr(settings, "API_KEY", "")
    monkeypatch.setattr(settings, "TRUSTED_PROXY_HOPS", 0)
    monkeypatch.setattr(settings, "QUOTA_ENABLED", True)
    monkeypatch.setattr(settings, "QUOTA_UPLOADS", 5)


@pytest.fixture(autouse=True)
def _isolated_quota_store(monkeypatch):
    """Never touch a real Redis from unit tests; start each test with empty counters."""
    def _no_redis():
        raise ConnectionError("redis disabled in unit tests")

    monkeypatch.setattr(quota, "get_redis_client", _no_redis)
    quota._memory.clear()
