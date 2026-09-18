"""Test doubles for the ports. Shipped with the package so any consumer's
tests (and this service's own) can run without a network or an API key."""

import hashlib
import math
import uuid
from collections.abc import AsyncIterator, Sequence

from travel_common.exceptions import DomainError, EntityNotFound

from ai_api.config import AISettings
from ai_api.domain.models import (
    ChatTurn,
    Document,
    Message,
    RetrievalFilters,
    Usage,
)


def settings_for_tests() -> AISettings:
    return AISettings(SECRET_KEY="unit-test-secret-key-with-32-bytes-min")  # noqa: S106


class FakeProvider:
    """Records what it was asked and streams a canned answer."""

    name = "fake"

    def __init__(
        self,
        deltas: Sequence[str] = ("Hola", " mundo"),
        usage: Usage | None = None,
    ) -> None:
        self.deltas = list(deltas)
        self.usage = usage or Usage(model="fake-model", input_tokens=3, output_tokens=2)
        self.calls: list[list[Message]] = []

    async def stream(
        self, messages: Sequence[Message], *, usage: Usage | None = None
    ) -> AsyncIterator[str]:
        self.calls.append(list(messages))
        for delta in self.deltas:
            yield delta
        if usage is not None:
            usage.model = self.usage.model
            usage.input_tokens = self.usage.input_tokens
            usage.output_tokens = self.usage.output_tokens


class FakeConversations:
    """An in-memory core_api for conversations; `fail_with` makes every call raise."""

    def __init__(self, fail_with: DomainError | None = None) -> None:
        self.threads: dict[str, list[ChatTurn]] = {}
        self.tokens: list[str] = []
        self.fail_with = fail_with

    async def start_thread(self, bearer_token: str) -> str:
        self._check(bearer_token)
        thread_id = str(uuid.UUID(int=len(self.threads) + 1))
        self.threads[thread_id] = []
        return thread_id

    async def append_turn(
        self, bearer_token: str, thread_id: str, turn: ChatTurn
    ) -> None:
        self._check(bearer_token)
        if thread_id not in self.threads:
            raise EntityNotFound("Chat thread", thread_id)
        self.threads[thread_id].append(turn)

    def _check(self, bearer_token: str) -> None:
        self.tokens.append(bearer_token)
        if self.fail_with is not None:
            raise self.fail_with


class FakeEmbedder:
    """Deterministic unit vectors from a hash of the text: equal texts get
    equal vectors, and each call reports one token per word."""

    def __init__(self, dimensions: int = 8, model_id: str = "fake-embedder") -> None:
        self._dimensions = dimensions
        self._model_id = model_id
        self.calls: list[str] = []

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed_query(
        self, text: str, *, usage: Usage | None = None
    ) -> list[float]:
        return self._embed(text, usage)

    async def embed_documents(
        self, texts: Sequence[str], *, usage: Usage | None = None
    ) -> list[list[float]]:
        return [self._embed(text, usage) for text in texts]

    def _embed(self, text: str, usage: Usage | None) -> list[float]:
        self.calls.append(text)
        if usage is not None:
            usage.model = self._model_id
            usage.input_tokens = (usage.input_tokens or 0) + len(text.split())
        digest = hashlib.sha256(text.encode()).digest()
        raw = [digest[i % len(digest)] - 127.5 for i in range(self._dimensions)]
        norm = math.sqrt(sum(x * x for x in raw))
        return [x / norm for x in raw]


class FakeRetriever:
    """Returns canned passages and records every search; `fail_with` makes
    each search raise instead."""

    def __init__(
        self,
        documents: Sequence[Document] = (),
        fail_with: DomainError | None = None,
    ) -> None:
        self.documents = list(documents)
        self.fail_with = fail_with
        self.searches: list[tuple[str, int, RetrievalFilters | None]] = []

    async def search(
        self,
        query: str,
        *,
        limit: int = 5,
        filters: RetrievalFilters | None = None,
    ) -> list[Document]:
        self.searches.append((query, limit, filters))
        if self.fail_with is not None:
            raise self.fail_with
        return self.documents[:limit]
