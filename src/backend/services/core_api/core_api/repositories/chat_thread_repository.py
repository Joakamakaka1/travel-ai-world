from sqlalchemy import select

from core_api.models.chat_thread import ChatThread
from core_api.pagination import Page
from core_api.repositories.base import BaseRepository


class ChatThreadRepository(BaseRepository[ChatThread]):
    model = ChatThread

    async def list_for_user(
        self, user_id: int, page: Page = Page()
    ) -> list[ChatThread]:
        """The user's threads, most recent activity first."""
        stmt = (
            select(ChatThread)
            .where(ChatThread.user_id == user_id)
            .order_by(ChatThread.updated_at.desc(), ChatThread.id)
            .offset(page.skip)
            .limit(page.limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
