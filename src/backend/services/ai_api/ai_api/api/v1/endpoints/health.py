from fastapi import APIRouter, Depends

from ai_api.api.deps import get_llm_provider
from ai_api.domain.ports import LLMProvider

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "ok", "api": "healthy"}


@router.get("/provider")
async def provider_health(provider: LLMProvider = Depends(get_llm_provider)):
    """503 (via ProviderUnavailable) when the AI provider is not configured.

    `name` says which adapter answers (`nvidia`, `bedrock`), so a deployed
    function can be checked without reading its environment.
    """
    return {
        "status": "ok",
        "provider": "configured",
        "name": getattr(provider, "name", "unknown"),
    }
