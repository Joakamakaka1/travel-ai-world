from fastapi import APIRouter, Depends

from ai_api.api.deps import get_llm_provider
from ai_api.domain.ports import LLMProvider

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "ok", "api": "healthy"}


@router.get("/provider")
async def provider_health(_: LLMProvider = Depends(get_llm_provider)):
    """503 (via ProviderUnavailable) when the AI provider is not configured."""
    return {"status": "ok", "provider": "configured"}
