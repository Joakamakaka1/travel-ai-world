"""LLMProvider adapter for NVIDIA's OpenAI-compatible chat completions API."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator, Callable, Sequence
from dataclasses import asdict

import httpx

from ai_api.domain.models import Message
from ai_api.infrastructure.retry import RetryPolicy
from ai_api.infrastructure.sse import SSEParser
from travel_common.exceptions import ProviderUnavailable

logger = logging.getLogger(__name__)

ClientFactory = Callable[..., httpx.AsyncClient]


class NvidiaProvider:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        connect_timeout: float = 10.0,
        read_timeout: float = 120.0,
        retry: RetryPolicy = RetryPolicy(),
        client_factory: ClientFactory = httpx.AsyncClient,
    ) -> None:
        self._api_key = api_key
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._model = model
        self._timeout = httpx.Timeout(
            connect=connect_timeout, read=read_timeout, write=10.0, pool=10.0
        )
        self._retry = retry
        self._client_factory = client_factory

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    async def stream(self, messages: Sequence[Message]) -> AsyncIterator[str]:
        if not self.is_configured:
            raise ProviderUnavailable("AI provider not configured")

        yielded = False
        for delay in self._retry.delays():
            try:
                async for delta in self._stream_once(messages):
                    yielded = True
                    yield delta
                return
            except httpx.HTTPError as exc:
                # Retrying after partial output would duplicate text.
                if yielded or delay is None:
                    raise ProviderUnavailable(f"AI provider error: {exc}") from exc
                logger.warning("NVIDIA API error (%s); retrying in %.0fs", exc, delay)
                await asyncio.sleep(delay)

    async def _stream_once(self, messages: Sequence[Message]) -> AsyncIterator[str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [asdict(m) for m in messages],
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 0.95,
            "stream": True,
        }
        parser = SSEParser()
        async with (
            self._client_factory(timeout=self._timeout) as client,
            client.stream("POST", self._url, headers=headers, json=payload) as resp,
        ):
            if resp.status_code != 200:
                body = (await resp.aread()).decode("utf-8", errors="replace")
                raise httpx.HTTPStatusError(
                    f"NVIDIA API returned {resp.status_code}: {body}",
                    request=resp.request,
                    response=resp,
                )
            async for chunk in resp.aiter_text():
                for data in parser.feed(chunk):
                    delta = _extract_delta(data)
                    if delta:
                        yield delta


def _extract_delta(data: str) -> str | None:
    if data == "[DONE]":
        return None
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        logger.debug("Skipping malformed SSE data: %s", data)
        return None
    choices = parsed.get("choices") or []
    if not choices:
        return None
    delta = choices[0].get("delta") or {}
    # Some models emit "content", others "text".
    return delta.get("content") or delta.get("text")
