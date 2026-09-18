"""Ports: what the use cases need from the outside world.

Adapters in `infrastructure/` implement these; tests substitute fakes.
"""

from collections.abc import AsyncIterator, Sequence
from typing import Any, Protocol

from ai_api.domain.models import (
    ChatTurn,
    Document,
    Message,
    RetrievalFilters,
    Usage,
)


class LLMProvider(Protocol):
    def stream(
        self, messages: Sequence[Message], *, usage: Usage | None = None
    ) -> AsyncIterator[str]:
        """Yield text deltas. Raise `ProviderUnavailable` when the upstream fails.

        When `usage` is given, fill in the model and the token counts the
        upstream reports, by the time the stream ends.
        """
        ...


class Embedder(Protocol):
    """Turns text into the vectors a store compares.

    One model embeds both sides of a search, so a question and a passage end
    up in the same space. Raises `ProviderUnavailable` when the upstream fails.
    When `usage` is given, the input tokens the upstream bills are added to it.
    """

    @property
    def model_id(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    async def embed_query(
        self, text: str, *, usage: Usage | None = None
    ) -> list[float]: ...

    async def embed_documents(
        self, texts: Sequence[str], *, usage: Usage | None = None
    ) -> list[list[float]]: ...


class Retriever(Protocol):
    async def search(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: RetrievalFilters | None = None,
    ) -> list[Document]: ...


class TripGateway(Protocol):
    """The slice of core_api the AI service needs, acting as the caller."""

    async def create_trip(
        self, bearer_token: str, trip: dict[str, Any]
    ) -> dict[str, Any]: ...


class ConversationGateway(Protocol):
    """Where the chat keeps its conversations: core_api, acting as the caller.

    Raises `EntityNotFound` / `Forbidden` for a thread the caller cannot use
    and `ProviderUnavailable` when core_api cannot be reached (ADR 0013).
    """

    async def start_thread(self, bearer_token: str) -> str: ...

    async def append_turn(
        self, bearer_token: str, thread_id: str, turn: ChatTurn
    ) -> None: ...
