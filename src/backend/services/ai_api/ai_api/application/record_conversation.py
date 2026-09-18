"""Use case: keep every answered exchange in the caller's conversation (ADR 0013).

It wraps the answer stream. The text reaches the client as it is generated;
once the answer is complete, the question and the answer (with its sources,
model, tokens and latency) are appended to the conversation in core_api, and
a `ThreadSaved` event tells the client which thread to continue.

Recording never breaks the chat: if core_api fails, the answer has already
been delivered and the failure is only logged. A thread that no longer
exists, or is not the caller's, is replaced by a new one.
"""

import logging
import time
from collections.abc import AsyncIterator, Callable

from travel_common.exceptions import DomainError, EntityNotFound, Forbidden

from ai_api.domain.models import (
    ChatTrace,
    ChatTurn,
    Document,
    MetadataValue,
    Source,
    ThreadSaved,
)
from ai_api.domain.ports import ConversationGateway

logger = logging.getLogger(__name__)


class RecordConversation:
    def __init__(
        self,
        conversations: ConversationGateway,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._conversations = conversations
        self._clock = clock

    async def __call__(
        self,
        bearer_token: str,
        message: str,
        answer: AsyncIterator[str],
        trace: ChatTrace,
        *,
        thread_id: str | None = None,
    ) -> AsyncIterator[str | ThreadSaved]:
        started = self._clock()
        parts: list[str] = []
        async for delta in answer:
            parts.append(delta)
            yield delta
        if not parts:
            return

        latency_ms = round((self._clock() - started) * 1000)
        question = ChatTurn("user", message)
        reply = ChatTurn(
            "assistant",
            "".join(parts),
            sources=tuple(_source(doc) for doc in trace.documents),
            model=trace.usage.model,
            input_tokens=trace.usage.input_tokens,
            output_tokens=trace.usage.output_tokens,
            latency_ms=latency_ms,
        )
        try:
            saved_in = await self._save(bearer_token, thread_id, question, reply)
        except DomainError as exc:
            logger.warning(
                "Chat exchange not recorded (%s): %s", exc.error_code, exc.message
            )
            return
        yield ThreadSaved(saved_in)

    async def _save(
        self, token: str, thread_id: str | None, question: ChatTurn, reply: ChatTurn
    ) -> str:
        if thread_id is not None:
            try:
                await self._conversations.append_turn(token, thread_id, question)
            except (EntityNotFound, Forbidden):
                logger.info("Thread %s is not usable; starting a new one", thread_id)
            else:
                await self._conversations.append_turn(token, thread_id, reply)
                return thread_id
        thread_id = await self._conversations.start_thread(token)
        await self._conversations.append_turn(token, thread_id, question)
        await self._conversations.append_turn(token, thread_id, reply)
        return thread_id


def _source(document: Document) -> Source:
    metadata = document.metadata
    return Source(
        doc_id=document.id,
        title=_text(metadata.get("name") or metadata.get("heading_path")),
        url=_text(metadata.get("source_url") or metadata.get("url")),
    )


def _text(value: MetadataValue) -> str | None:
    return str(value) if value not in (None, "") else None
