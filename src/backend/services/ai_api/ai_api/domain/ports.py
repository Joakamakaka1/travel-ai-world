"""Ports: what the use cases need from the outside world.

Adapters in `infrastructure/` implement these; tests substitute fakes.
"""

from collections.abc import AsyncIterator, Sequence
from typing import Any, Protocol

from ai_api.domain.models import Document, Message


class LLMProvider(Protocol):
    def stream(self, messages: Sequence[Message]) -> AsyncIterator[str]:
        """Yield text deltas. Raise `ProviderUnavailable` when the upstream fails."""
        ...


class Retriever(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> list[Document]: ...


class TripGateway(Protocol):
    """The slice of core_api the AI service needs, acting as the caller."""

    async def create_trip(
        self, bearer_token: str, trip: dict[str, Any]
    ) -> dict[str, Any]: ...
