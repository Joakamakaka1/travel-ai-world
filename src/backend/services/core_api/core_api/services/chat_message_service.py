from pydantic import BaseModel

from core_api.models.chat_message import ChatMessage
from core_api.models.chat_thread import ChatThread
from core_api.pagination import Page
from core_api.repositories.chat_message_repository import ChatMessageRepository
from core_api.schemas.chat_message import ChatMessageCreate
from core_api.services.base import BaseService


class ChatMessageService(BaseService[ChatMessage, ChatMessageCreate, BaseModel]):
    """Messages are an append-only log inside a thread the caller owns."""

    repository: ChatMessageRepository
    entity_name = "Chat message"

    async def list_in(
        self, thread: ChatThread, page: Page = Page()
    ) -> list[ChatMessage]:
        return await self.repository.list_in_thread(thread.id, page)

    async def append(self, thread: ChatThread, data: ChatMessageCreate) -> ChatMessage:
        message = ChatMessage(**data.model_dump(), thread_id=thread.id)
        message.check_invariants()
        return await self.repository.append(message)
