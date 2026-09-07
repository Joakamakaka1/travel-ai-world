"""FastAPI wiring for ai_api: settings, identity and use cases."""

from fastapi import Depends

from ai_api.application.stream_chat import StreamChat
from ai_api.config import AISettings, get_settings
from ai_api.domain.ports import LLMProvider, TripGateway
from ai_api.infrastructure.core_api_client import CoreApiClient
from ai_api.infrastructure.nvidia_provider import NvidiaProvider
from ai_api.infrastructure.retry import RetryPolicy
from ai_api.prompts import CHAT_SYSTEM_PROMPT
from travel_common.exceptions import ProviderUnavailable
from travel_common.http.auth import extract_bearer_token
from travel_common.principal import Principal
from travel_common.security import principal_from_token


async def get_current_user(
    token: str = Depends(extract_bearer_token),
    settings: AISettings = Depends(get_settings),
) -> Principal:
    """Stateless: the JWT alone identifies the caller (no database here)."""
    return principal_from_token(token, settings)


def get_llm_provider(settings: AISettings = Depends(get_settings)) -> LLMProvider:
    provider = NvidiaProvider(
        api_key=settings.NVIDIA_API_KEY,
        base_url=settings.NVIDIA_BASE_URL,
        model=settings.NVIDIA_CHAT_MODEL,
        connect_timeout=settings.NVIDIA_CONNECT_TIMEOUT,
        read_timeout=settings.NVIDIA_READ_TIMEOUT,
        retry=RetryPolicy(max_retries=settings.NVIDIA_MAX_RETRIES),
    )
    if not provider.is_configured:
        raise ProviderUnavailable("AI chat service not configured")
    return provider


def get_stream_chat(provider: LLMProvider = Depends(get_llm_provider)) -> StreamChat:
    return StreamChat(provider, CHAT_SYSTEM_PROMPT)


def get_trip_gateway(settings: AISettings = Depends(get_settings)) -> TripGateway:
    return CoreApiClient(settings.CORE_API_URL, settings.API_V1_STR)
