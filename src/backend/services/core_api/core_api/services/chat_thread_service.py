import uuid

from travel_common.exceptions import Forbidden

from core_api.auth.principal import AccountPrincipal
from core_api.models.chat_thread import ChatThread
from core_api.pagination import Page
from core_api.repositories.chat_thread_repository import ChatThreadRepository
from core_api.schemas.chat_thread import ChatThreadCreate, ChatThreadUpdate
from core_api.services.base import BaseService


class ChatThreadService(BaseService[ChatThread, ChatThreadCreate, ChatThreadUpdate]):
    repository: ChatThreadRepository
    entity_name = "Chat thread"

    async def list_for(
        self, principal: AccountPrincipal, page: Page = Page()
    ) -> list[ChatThread]:
        return await self.repository.list_for_user(principal.id, page)

    async def get_owned(
        self, thread_id: uuid.UUID, principal: AccountPrincipal
    ) -> ChatThread:
        """A conversation is only visible to the user who owns it."""
        thread = await self.get(thread_id)
        if thread.user_id != principal.id:
            raise Forbidden()
        return thread
