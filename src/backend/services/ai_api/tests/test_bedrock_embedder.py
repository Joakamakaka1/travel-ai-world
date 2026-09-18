"""TitanEmbedder against a fake `bedrock-runtime` client: no network, no credentials."""

import io
import json
from typing import Any

import pytest
from ai_api.config import AISettings
from ai_api.domain.models import Usage
from ai_api.infrastructure.bedrock_embedder import (
    MAX_INPUT_CHARS,
    UPSTREAM_ERROR_MESSAGE,
    TitanEmbedder,
)
from ai_api.infrastructure.retry import RetryPolicy
from botocore.exceptions import ClientError, EndpointConnectionError
from travel_common.exceptions import ProviderUnavailable

MODEL = "amazon.titan-embed-text-v2:0"


def _response(vector: list[float], tokens: int = 3) -> dict[str, Any]:
    body = json.dumps({"embedding": vector, "inputTextTokenCount": tokens})
    return {"body": io.BytesIO(body.encode())}


def _client_error(code: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": code, "Message": "upstream detail"}}, "InvokeModel"
    )


class FakeClient:
    """Answers each call with the next outcome (a vector or an exception to
    raise); with no outcomes left, a vector made from the text's length."""

    def __init__(self, *outcomes: Any, dimensions: int = 4) -> None:
        self.outcomes = list(outcomes)
        self.dimensions = dimensions
        self.calls: list[dict[str, Any]] = []

    def invoke_model(self, **kwargs: Any) -> Any:
        self.calls.append({**kwargs, "body": json.loads(kwargs["body"])})
        if self.outcomes:
            outcome = self.outcomes.pop(0)
            if isinstance(outcome, BaseException):
                raise outcome
            return _response(outcome)
        text = self.calls[-1]["body"]["inputText"]
        return _response([float(len(text))] * self.dimensions)


def _embedder(client: FakeClient, retries: int = 0, **kwargs: Any) -> TitanEmbedder:
    return TitanEmbedder(
        client=client,
        model=MODEL,
        dimensions=client.dimensions,
        retry=RetryPolicy(max_retries=retries, base_delay=0),
        **kwargs,
    )


async def test_sends_the_titan_v2_body_and_nothing_else():
    """Titan V2 refuses keys it does not know (`inputType` is Cohere's)."""
    client = FakeClient([0.5, 0.5, 0.5, 0.5])

    vector = await _embedder(client).embed_query("baños termales")

    assert vector == [0.5, 0.5, 0.5, 0.5]
    assert client.calls == [
        {
            "modelId": MODEL,
            "body": {"inputText": "baños termales", "dimensions": 4, "normalize": True},
        }
    ]


async def test_a_batch_keeps_its_order_and_adds_up_the_tokens():
    client = FakeClient()
    usage = Usage()

    vectors = await _embedder(client, concurrency=2).embed_documents(
        ["a", "bbb", "cc"], usage=usage
    )

    assert [v[0] for v in vectors] == [1.0, 3.0, 2.0]
    assert usage == Usage(model=MODEL, input_tokens=9)


async def test_an_overlong_question_is_cut_rather_than_refused():
    client = FakeClient()

    await _embedder(client).embed_query("x" * (MAX_INPUT_CHARS + 50))

    assert len(client.calls[0]["body"]["inputText"]) == MAX_INPUT_CHARS


async def test_retries_throttling_then_succeeds():
    client = FakeClient(_client_error("ThrottlingException"), [1.0, 0.0, 0.0, 0.0])

    vector = await _embedder(client, retries=1).embed_query("q")

    assert vector == [1.0, 0.0, 0.0, 0.0]
    assert len(client.calls) == 2


async def test_retries_a_dropped_connection():
    client = FakeClient(
        EndpointConnectionError(endpoint_url="https://bedrock"), [1.0, 0.0, 0.0, 0.0]
    )

    assert await _embedder(client, retries=1).embed_query("q") == [1.0, 0.0, 0.0, 0.0]


@pytest.mark.parametrize("code", ["ValidationException", "AccessDeniedException"])
async def test_a_permanent_error_is_not_retried_nor_leaked(code: str):
    client = FakeClient(_client_error(code))

    with pytest.raises(ProviderUnavailable) as info:
        await _embedder(client, retries=3).embed_query("q")

    assert info.value.message == UPSTREAM_ERROR_MESSAGE
    assert "upstream detail" not in str(info.value)
    assert len(client.calls) == 1


async def test_a_vector_of_the_wrong_length_stops_the_caller():
    """The index was created for one length; anything else cannot be stored."""
    client = FakeClient([1.0, 0.0])

    with pytest.raises(ProviderUnavailable):
        await _embedder(client).embed_query("q")


def test_from_settings_reads_model_dimensions_and_concurrency():
    embedder = TitanEmbedder.from_settings(
        AISettings(
            EMBEDDINGS_MODEL="m",
            EMBEDDINGS_DIMENSIONS=256,
            EMBEDDINGS_CONCURRENCY=16,
            EMBEDDINGS_REGION="eu-west-1",
        )
    )

    assert (embedder.model_id, embedder.dimensions) == ("m", 256)
    assert embedder._concurrency == 16
    # One pooled connection per call in flight (a real boto3 client here).
    client: Any = embedder._client
    assert client.meta.config.max_pool_connections == 16
