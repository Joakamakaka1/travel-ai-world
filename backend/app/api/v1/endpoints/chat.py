"""AI chat proxy with streaming support.

Thin controller: delegates to ChatService for streaming logic.
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import ProviderUnavailable
from app.core.principal import Principal
from app.schemas.chat import ChatRequest
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton — no DB dependency, just an upstream provider proxy
_chat_service = ChatService()


@router.post("")
async def chat(
    request: ChatRequest,
    principal: Principal = Depends(get_current_user),
) -> StreamingResponse:
    """Stream a chat completion for the authenticated user.

    Wire format, one JSON object per `data:` line, terminated by `[DONE]`:

        data: {"content": "Hola"}
        data: {"error": "..."}
        data: [DONE]

    The `system` prompt is inserted by the backend; clients may only send
    `user` and `assistant` turns.
    """
    if not settings.NVIDIA_API_KEY:
        raise ProviderUnavailable("AI chat service not configured")

    logger.info(
        "Chat request from user %s (%d history turns)",
        principal.id,
        len(request.history),
    )

    messages: list[dict[str, str]] = [
        {"role": msg.role, "content": msg.content} for msg in request.history
    ]
    messages.append({"role": "user", "content": request.message})

    return StreamingResponse(
        _chat_service.stream_completion(messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
