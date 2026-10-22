"""What the vector store's writer and reader share: client, keys and metadata shape.

`indexing` writes and `s3vectors_retriever` reads; both must agree with each other and
with `infra/aws/vectors.tf`, which freezes the non-filterable keys when the index is
created (ADR 0014).
"""

import uuid
from typing import Any, Protocol, cast

import boto3
from botocore.config import Config

from ai_api.config import AISettings

# Small values a search narrows by, counted against a 2 KB budget per vector.
# Only the non-filterable list is frozen by the index, so a key can join this
# one without recreating anything.
FILTERABLE_KEYS = (
    "city",
    "category",
    "district",
    "kind",
    "lang",
    "source",
    "price_tier",
    "lat",
    "lon",
    "tour_type",
    "price_model",
)

# What an answer shows but never filters on. Fixed when the index is created
# and limited to ten, so `extra` carries the rest of what a card shows (images
# and their licence, address, hours, price, tour details) as JSON.
NON_FILTERABLE_KEYS = (
    "text",
    "doc_id",
    "name",
    "url",
    "source_url",
    "heading_path",
    "extra",
)

_KEY_NAMESPACE = uuid.NAMESPACE_URL


class S3VectorsClient(Protocol):
    """The five operations we use; boto3's `s3vectors` client satisfies it."""

    def put_vectors(self, **kwargs: Any) -> Any: ...

    def query_vectors(self, **kwargs: Any) -> Any: ...

    def get_vectors(self, **kwargs: Any) -> Any: ...

    def list_vectors(self, **kwargs: Any) -> Any: ...

    def delete_vectors(self, **kwargs: Any) -> Any: ...


def build_client(settings: AISettings) -> S3VectorsClient:
    """The process-wide client; credentials come from the environment."""
    config = Config(
        region_name=settings.VECTOR_REGION,
        connect_timeout=settings.BEDROCK_CONNECT_TIMEOUT,
        read_timeout=settings.BEDROCK_READ_TIMEOUT,
        retries={"mode": "standard", "total_max_attempts": 3},
    )
    # boto3 builds clients at runtime; the Protocol is the static contract.
    return cast(S3VectorsClient, boto3.client("s3vectors", config=config))


def vector_key(doc_id: str) -> str:
    """The key a document is stored under.

    Not the `doc_id` itself, which may carry accents (`wv:en:Andrássy út#...`).
    This is ASCII, stable across runs — so re-indexing overwrites instead of
    duplicating — and the `doc_id` travels in the metadata.
    """
    return str(uuid.uuid5(_KEY_NAMESPACE, doc_id))
