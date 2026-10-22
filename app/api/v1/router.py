from fastapi import APIRouter, Depends

from app.core.security import require_api_key

from app.api.v1.routes.documents import router as documents_router
from app.api.v1.routes.extractions import router as extractions_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.questions import router as questions_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(health_router)
# /health stays public (uptime probes); everything else honours API_KEY when configured.
protected = [Depends(require_api_key)]
v1_router.include_router(documents_router, dependencies=protected)
v1_router.include_router(extractions_router, dependencies=protected)
v1_router.include_router(questions_router, dependencies=protected)
