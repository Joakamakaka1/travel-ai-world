import uuid

from sqlalchemy import func, select, update

from core_api.models.chat_message import ChatMessage
from core_api.models.chat_thread import ChatThread
from core_api.pagination import Page
from core_api.repositories.base import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage]):
    model = ChatMessage

    async def list_in_thread(
        self, thread_id: uuid.UUID, page: Page = Page()
    ) -> list[ChatMessage]:
        """A thread's messages in the order they were written."""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.thread_id == thread_id)
            .order_by(ChatMessage.created_at, ChatMessage.id)
            .offset(page.skip)
            .limit(page.limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def append(self, message: ChatMessage) -> ChatMessage:
        """Insert the message and mark its thread as the most recently active."""
        created = await self.create(message)
        await self.db.execute(
            update(ChatThread)
            .where(ChatThread.id == message.thread_id)
            .values(updated_at=func.now())
        )
        return created
