"""Embedder adapter for Amazon Bedrock's Titan Text Embeddings V2.

No API key: boto3 signs the calls with whatever credentials the process has,
the function's IAM role on Lambda and the SSO session on a laptop. The model
is a plain in-Region foundation model, not a cross-Region inference profile
like the chat models, so it is invoked by its bare id.

Titan embeds one text per call, so `embed_documents` fans out with a bounded
number of calls in flight. boto3 is synchronous: every call runs in a worker
thread through `asyncio.to_thread`, leaving the event loop free.

The same model embeds questions and passages — Titan V2 makes no distinction
between the two sides of a search — which is what keeps them comparable.
"""

import asyncio
import json
import logging
from collections.abc import Sequence
from typing import Any, Protocol, cast

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from travel_common.exceptions import ProviderUnavailable

from ai_api.config import AISettings
from ai_api.domain.models import Usage
from ai_api.infrastructure.bedrock import client_config, is_retryable
from ai_api.infrastructure.retry import RetryPolicy

logger = logging.getLogger(__name__)

# What the browser sees. Bedrock's codes and messages stay in the logs.
UPSTREAM_ERROR_MESSAGE = "Embeddings provider error"

# Titan V2 accepts about 8k tokens. A question long enough to reach that is a
# paste, not a question: embedding its beginning beats failing the search.
MAX_INPUT_CHARS = 20_000


class BedrockRuntimeClient(Protocol):
    """The one operation this adapter uses; tests pass a fake."""

    def invoke_model(self, **kwargs: Any) -> Any: ...


class TitanEmbedder:
    def __init__(
        self,
        *,
        client: BedrockRuntimeClient,
        model: str,
        dimensions: int = 1024,
        concurrency: int = 8,
        retry: RetryPolicy = RetryPolicy(),
    ) -> None:
        self._client = client
        self._model = model
        self._dimensions = dimensions
        self._concurrency = concurrency
        self._retry = retry

    @classmethod
    def from_settings(cls, settings: AISettings) -> "TitanEmbedder":
        config = client_config(
            region=settings.EMBEDDINGS_REGION,
            connect_timeout=settings.BEDROCK_CONNECT_TIMEOUT,
            read_timeout=settings.BEDROCK_READ_TIMEOUT,
            # One connection per call in flight, so indexing does not spend
            # its time reopening them.
            max_pool_connections=max(10, settings.EMBEDDINGS_CONCURRENCY),
        )
        # boto3 builds clients at runtime; the Protocol is the static contract.
        client = cast(
            BedrockRuntimeClient, boto3.client("bedrock-runtime", config=config)
        )
        return cls(
            client=client,
            model=settings.EMBEDDINGS_MODEL,
            dimensions=settings.EMBEDDINGS_DIMENSIONS,
            concurrency=settings.EMBEDDINGS_CONCURRENCY,
            retry=RetryPolicy(max_retries=settings.BEDROCK_MAX_RETRIES),
        )

    @property
    def model_id(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def aclose(self) -> None:
        """boto3 clients hold nothing that needs closing; here for symmetry."""
        return None

    async def embed_query(
        self, text: str, *, usage: Usage | None = None
    ) -> list[float]:
        return await self._embed(text, usage)

    async def embed_documents(
        self, texts: Sequence[str], *, usage: Usage | None = None
    ) -> list[list[float]]:
        """Embed a batch, at most `concurrency` calls in flight.

        Either every text comes back or the first failure propagates: a
        partially embedded batch would silently leave holes in an index.
        The calls finish before this returns, inside the caller's request.
        """
        limit = asyncio.Semaphore(self._concurrency)

        async def embed(text: str) -> list[float]:
            async with limit:
                return await self._embed(text, usage)

        return list(await asyncio.gather(*(embed(text) for text in texts)))

    async def _embed(self, text: str, usage: Usage | None) -> list[float]:
        body = json.dumps(
            {
                "inputText": text[:MAX_INPUT_CHARS],
                "dimensions": self._dimensions,
                # Cosine distance compares directions, so the vectors arrive
                # with length 1 and the store never has to normalise them.
                "normalize": True,
            }
        )
        for delay in self._retry.delays():
            try:
                response = await asyncio.to_thread(
                    self._client.invoke_model, modelId=self._model, body=body
                )
            except (ClientError, BotoCoreError) as exc:
                if delay is None or not is_retryable(exc):
                    logger.error("Titan embedding failed: %s", exc)
                    raise ProviderUnavailable(UPSTREAM_ERROR_MESSAGE) from exc
                logger.warning("Titan error (%s); retrying in %.0fs", exc, delay)
                await asyncio.sleep(delay)
            else:
                return self._vector(response, usage)
        raise ProviderUnavailable(UPSTREAM_ERROR_MESSAGE)  # pragma: no cover

    def _vector(self, response: Any, usage: Usage | None) -> list[float]:
        payload = json.loads(response["body"].read())
        if usage is not None:
            # Runs on the event loop once the worker thread is back, so the
            # concurrent calls of one batch never race on it.
            usage.model = self._model
            usage.input_tokens = (usage.input_tokens or 0) + int(
                payload.get("inputTextTokenCount") or 0
            )
        vector: list[float] = payload["embedding"]
        if len(vector) != self._dimensions:
            # An index is created for one length and cannot change it, so a
            # model answering with another one has to stop the caller.
            logger.error(
                "%s returned %d dimensions, expected %d",
                self._model,
                len(vector),
                self._dimensions,
            )
            raise ProviderUnavailable(UPSTREAM_ERROR_MESSAGE)
        return vector
