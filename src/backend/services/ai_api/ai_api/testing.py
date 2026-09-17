"""Test doubles for the ports. Shipped with the package so any consumer's
tests (and this service's own) can run without a network or an API key."""

import uuid
from collections.abc import AsyncIterator, Sequence

from travel_common.exceptions import DomainError, EntityNotFound

from ai_api.config import AISettings
from ai_api.domain.models import ChatTurn, Message, Usage


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
