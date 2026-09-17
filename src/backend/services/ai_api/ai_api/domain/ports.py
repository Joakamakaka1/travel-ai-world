"""Ports: what the use cases need from the outside world.

Adapters in `infrastructure/` implement these; tests substitute fakes.
"""

from collections.abc import AsyncIterator, Sequence
from typing import Any, Protocol

from ai_api.domain.models import ChatTurn, Document, Message, Usage


class LLMProvider(Protocol):
    def stream(
        self, messages: Sequence[Message], *, usage: Usage | None = None
    ) -> AsyncIterator[str]:
        """Yield text deltas. Raise `ProviderUnavailable` when the upstream fails.

        When `usage` is given, fill in the model and the token counts the
        upstream reports, by the time the stream ends.
        """
        ...


class Retriever(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> list[Document]: ...


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
