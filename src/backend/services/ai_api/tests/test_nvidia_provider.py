"""NvidiaProvider against a mocked HTTP transport: no network, no key."""

import httpx
import pytest

from ai_api.domain.models import Message
from ai_api.infrastructure.nvidia_provider import NvidiaProvider
from ai_api.infrastructure.retry import RetryPolicy
from ai_api.infrastructure.sse import SSEParser
from travel_common.exceptions import ProviderUnavailable

UPSTREAM_STREAM = (
    'data: {"choices": [{"delta": {"content": "Ho"}}]}\n\n'
    'data: {"choices": [{"delta": {"text": "la"}}]}\n\n'
    "data: not-json\n\n"
    "data: [DONE]\n\n"
)


def _provider(handler, retries: int = 0) -> NvidiaProvider:
    transport = httpx.MockTransport(handler)
    return NvidiaProvider(
        api_key="k",
        base_url="https://nvidia.test/v1",
        model="m",
        retry=RetryPolicy(max_retries=retries, base_delay=0),
        client_factory=lambda **kw: httpx.AsyncClient(transport=transport, **kw),
    )


async def _collect(provider: NvidiaProvider) -> list[str]:
    return [d async for d in provider.stream([Message("user", "hi")])]


async def test_streams_deltas_from_content_and_text_fields():
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(__import__("json").loads(request.content))
        return httpx.Response(200, text=UPSTREAM_STREAM)

    assert await _collect(_provider(handler)) == ["Ho", "la"]
    assert seen[0]["model"] == "m"
    assert seen[0]["stream"] is True
    assert seen[0]["messages"] == [{"role": "user", "content": "hi"}]


async def test_retries_a_failed_connection_then_succeeds():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(502, text="bad gateway")
        return httpx.Response(200, text=UPSTREAM_STREAM)

    assert await _collect(_provider(handler, retries=1)) == ["Ho", "la"]
    assert attempts == 2


async def test_gives_up_after_last_retry():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(ProviderUnavailable):
        await _collect(_provider(handler, retries=1))


async def test_unconfigured_provider_refuses_immediately():
    provider = NvidiaProvider(api_key="", base_url="https://x", model="m")

    with pytest.raises(ProviderUnavailable):
        await _collect(provider)


def test_sse_parser_reassembles_lines_split_across_chunks():
    parser = SSEParser()

    assert parser.feed('data: {"a"') == []
    assert parser.feed(": 1}\n\ndata: [DO") == ['{"a": 1}']
    assert parser.feed("NE]\n") == ["[DONE]"]
