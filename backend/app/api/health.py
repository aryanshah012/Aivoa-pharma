from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.complaint import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health():
    settings = get_settings()
    return {
        "status": "ok",
        "model": settings.GROQ_MODEL,
        "llm_configured": bool(settings.GROQ_API_KEY),
    }
