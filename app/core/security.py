import hmac

from fastapi import Header, HTTPException, Request, status

from app.core.config import settings
from app.core.messages import MSG_INVALID_API_KEY


def client_ip(request: Request) -> str:
    """Best-effort real client IP.

    Only trusts `X-Forwarded-For` when TRUSTED_PROXY_HOPS > 0, reading from the right so that
    entries a client prepends itself are ignored.
    """
    hops = settings.TRUSTED_PROXY_HOPS
    if hops > 0:
        forwarded = request.headers.get("x-forwarded-for", "")
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if len(parts) >= hops:
            return parts[-hops]
    return request.client.host if request.client else "unknown"


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Route dependency. No-op unless API_KEY is configured."""
    expected = settings.API_KEY
    if not expected:
        return
    if not x_api_key or not hmac.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MSG_INVALID_API_KEY)
