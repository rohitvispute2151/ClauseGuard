import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.redis import close_redis_client
from app.middleware.quota import QuotaMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("clauseguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    yield

    logger.info("Shutting down ClauseGuard...")
    await close_redis_client()


app = FastAPI(
    title="ClauseGuard API",
    version=settings.APP_VERSION,
    description="Grounded Contract Review API with Structured Extraction, Hybrid Retrieval & Verifiable Citations",
    lifespan=lifespan,
)

# Register middlewares. Starlette runs the LAST one added first, so CORS goes last (outermost):
# that way 401/429 responses produced by the layers below still carry CORS headers.
app.add_middleware(QuotaMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    expose_headers=["Retry-After", "X-Request-ID"],
)

# Mount Routes
app.include_router(v1_router)

# Mount Prometheus metrics
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
