from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check endpoint")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "primary_provider": f"gemini ({settings.GEMINI_MODEL_ID})",
        "fallback_provider": f"groq ({settings.GROQ_MODEL_ID})",
    }
