"""Use case: answer a user turn as a stream of text deltas."""

from collections.abc import AsyncIterator, Sequence

from ai_api.domain.models import ChatTrace, Message
from ai_api.domain.ports import LLMProvider, Retriever
from ai_api.prompts import RAG_CONTEXT_PROMPT


class StreamChat:
    def __init__(
        self,
        provider: LLMProvider,
        system_prompt: str,
        retriever: Retriever | None = None,
    ) -> None:
        self._provider = provider
        self._system_prompt = system_prompt
        self._retriever = retriever

    async def __call__(
        self,
        message: str,
        history: Sequence[Message] = (),
        *,
        trace: ChatTrace | None = None,
    ) -> AsyncIterator[str]:
        """Stream the answer; `trace`, when given, collects what it was built from."""
        messages = [Message("system", self._system_prompt)]
        if self._retriever is not None:
            documents = await self._retriever.search(message)
            if documents:
                if trace is not None:
                    trace.documents.extend(documents)
                context = "\n\n".join(doc.content for doc in documents)
                messages.append(
                    Message("system", RAG_CONTEXT_PROMPT.format(context=context))
                )
        messages.extend(history)
        messages.append(Message("user", message))

        usage = trace.usage if trace is not None else None
        async for delta in self._provider.stream(messages, usage=usage):
            yield delta
