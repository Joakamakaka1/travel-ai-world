"""Load a city corpus into the vector index (ADR 0014).

    python -m ai_api.indexing src/backend/tools/city_corpus/data/budapest/documents.jsonl

Reads the JSONL that the `city_corpus` tool commits, embeds every document and
upserts it into the index Terraform created. The bucket and the index are never
created here: this command only fills one that already exists.

Re-running it is safe. A document always lands under the same key, so a second
run overwrites instead of duplicating, and keys the file no longer mentions are
deleted at the end — which is how a rebuilt corpus replaces the one in the index.

The corpus contract is mirrored, not imported: `city_corpus` is a tool and this
is a service, and they share a file format and nothing else. Fields this module
does not name travel in `extra` as they come, so the corpus can grow new ones
without a change here.
"""

import argparse
import asyncio
import json
import logging
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from ai_api.config import AISettings, get_settings
from ai_api.domain.models import Usage
from ai_api.domain.ports import Embedder
from ai_api.infrastructure.bedrock_embedder import TitanEmbedder
from ai_api.infrastructure.s3vectors import (
    FILTERABLE_KEYS,
    S3VectorsClient,
    build_client,
    vector_key,
)

logger = logging.getLogger(__name__)

# Per vector, from the S3 Vectors limits. Checked here because the service
# rejects the whole batch, and a run of thousands should not die on one line.
MAX_FILTERABLE_BYTES = 2_048
MAX_TOTAL_BYTES = 40 * 1_024

# Vectors per PutVectors call. The API allows 500; a 1024-dimension vector
# serialises to some 20 KB, so this keeps a request far from the 20 MiB ceiling.
DEFAULT_BATCH_SIZE = 200

# Keys per DeleteVectors call, the API's maximum.
DELETE_BATCH_SIZE = 500


class CorpusDocument(BaseModel):
    """One line of `documents.jsonl`, as much of it as this command names."""

    model_config = ConfigDict(extra="allow")

    doc_id: str
    city: str
    category: str
    kind: str
    text: str
    heading_path: str
    source: str
    source_url: str
    lang: str
    district: str | None = None
    name: str | None = None
    lat: float | None = None
    lon: float | None = None
    price_tier: int | None = None
    url: str | None = None
    tour_type: str | None = None
    price_model: str | None = None


@dataclass(slots=True)
class Report:
    documents: int = 0
    vectors_written: int = 0
    vectors_deleted: int = 0
    tokens: int = 0
    seconds: float = 0.0
    max_filterable_bytes: int = 0
    max_total_bytes: int = 0
    oversized: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"{self.documents} documents read, {self.vectors_written} vectors written, "
            f"{self.vectors_deleted} deleted, {self.tokens} tokens embedded, "
            f"{self.seconds:.1f}s. Largest metadata: {self.max_filterable_bytes} B "
            f"filterable of {MAX_FILTERABLE_BYTES}, {self.max_total_bytes} B total "
            f"of {MAX_TOTAL_BYTES}."
        )


def read_corpus(path: Path, *, limit: int | None = None) -> Iterator[CorpusDocument]:
    """Parse the file line by line.

    A malformed line names itself and stops the run: half an index, with no
    way to tell which half, is worse than none.
    """
    with path.open(encoding="utf-8") as lines:
        for number, line in enumerate(lines, start=1):
            if limit is not None and number > limit:
                return
            if not line.strip():
                continue
            try:
                yield CorpusDocument.model_validate_json(line)
            except ValidationError as exc:
                raise SystemExit(
                    f"{path}:{number} is not a corpus document: {exc}"
                ) from exc


def metadata_for(document: CorpusDocument) -> dict[str, Any]:
    """Split a document into what a search filters by and what an answer shows.

    Everything this module does not name — images and their licence, address,
    opening hours, price, tour details — becomes JSON in `extra`, which is why
    a new corpus field does not need a new index.
    """
    fields = document.model_dump(exclude_none=True)
    metadata: dict[str, Any] = {
        key: fields[key] for key in FILTERABLE_KEYS if key in fields
    }
    metadata["text"] = document.text
    metadata["doc_id"] = document.doc_id
    for key in ("name", "url", "source_url", "heading_path"):
        if key in fields:
            metadata[key] = fields[key]
    extra = {
        key: value
        for key, value in (document.model_extra or {}).items()
        if value is not None
    }
    if extra:
        metadata["extra"] = json.dumps(extra, ensure_ascii=False, separators=(",", ":"))
    return metadata


def measure(metadata: dict[str, Any], report: Report, doc_id: str) -> bool:
    """Record how big this document's metadata is; False when it cannot be sent."""
    filterable = {k: v for k, v in metadata.items() if k in FILTERABLE_KEYS}
    filterable_bytes = len(json.dumps(filterable, ensure_ascii=False).encode())
    total_bytes = len(json.dumps(metadata, ensure_ascii=False).encode())
    report.max_filterable_bytes = max(report.max_filterable_bytes, filterable_bytes)
    report.max_total_bytes = max(report.max_total_bytes, total_bytes)
    if filterable_bytes > MAX_FILTERABLE_BYTES or total_bytes > MAX_TOTAL_BYTES:
        report.oversized.append(doc_id)
        logger.error(
            "Skipping %s: %d B filterable, %d B total",
            doc_id,
            filterable_bytes,
            total_bytes,
        )
        return False
    return True


async def index_corpus(
    path: Path,
    *,
    settings: AISettings,
    embedder: Embedder,
    client: S3VectorsClient,
    batch_size: int = DEFAULT_BATCH_SIZE,
    prune: bool = True,
    limit: int | None = None,
    dry_run: bool = False,
) -> Report:
    report = Report()
    usage = Usage()
    started = time.perf_counter()
    keys_in_file: set[str] = set()
    batch: list[CorpusDocument] = []

    async def flush() -> None:
        if batch and not dry_run:
            await write_batch(batch, settings, embedder, client, report, usage)
        batch.clear()

    for document in read_corpus(path, limit=limit):
        report.documents += 1
        if not measure(metadata_for(document), report, document.doc_id):
            continue
        keys_in_file.add(vector_key(document.doc_id))
        batch.append(document)
        if len(batch) >= batch_size:
            await flush()
    await flush()

    # Only a complete, clean run knows what the index should no longer hold:
    # pruning after `--limit`, a dry run or a skipped document would delete
    # everything that run did not look at.
    if prune and not dry_run and limit is None and not report.oversized:
        report.vectors_deleted = await prune_stale(settings, client, keys_in_file)

    report.tokens = usage.input_tokens or 0
    report.seconds = time.perf_counter() - started
    return report


async def write_batch(
    documents: Sequence[CorpusDocument],
    settings: AISettings,
    embedder: Embedder,
    client: S3VectorsClient,
    report: Report,
    usage: Usage,
) -> None:
    embeddings = await embedder.embed_documents(
        [d.text for d in documents], usage=usage
    )
    vectors = [
        {
            "key": vector_key(document.doc_id),
            "data": {"float32": embedding},
            "metadata": metadata_for(document),
        }
        for document, embedding in zip(documents, embeddings, strict=True)
    ]
    await asyncio.to_thread(
        client.put_vectors,
        vectorBucketName=settings.VECTOR_BUCKET,
        indexName=settings.VECTOR_INDEX,
        vectors=vectors,
    )
    report.vectors_written += len(vectors)
    logger.info("Wrote %d vectors (%d so far)", len(vectors), report.vectors_written)


async def prune_stale(
    settings: AISettings, client: S3VectorsClient, keys_in_file: set[str]
) -> int:
    """Delete what the index holds and the file no longer mentions."""
    stale: list[str] = []
    token: str | None = None
    while True:
        request: dict[str, Any] = {
            "vectorBucketName": settings.VECTOR_BUCKET,
            "indexName": settings.VECTOR_INDEX,
            "maxResults": 1_000,
        }
        if token:
            request["nextToken"] = token
        page = await asyncio.to_thread(client.list_vectors, **request)
        stale.extend(
            vector["key"]
            for vector in page.get("vectors", [])
            if vector["key"] not in keys_in_file
        )
        token = page.get("nextToken")
        if not token:
            break

    for start in range(0, len(stale), DELETE_BATCH_SIZE):
        await asyncio.to_thread(
            client.delete_vectors,
            vectorBucketName=settings.VECTOR_BUCKET,
            indexName=settings.VECTOR_INDEX,
            keys=stale[start : start + DELETE_BATCH_SIZE],
        )
    if stale:
        logger.info("Deleted %d vectors no longer in the corpus", len(stale))
    return len(stale)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m ai_api.indexing",
        description="Load a city corpus into the vector index.",
    )
    parser.add_argument("corpus", type=Path, help="the documents.jsonl to load")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument(
        "--limit", type=int, default=None, help="only the first N lines (a smoke test)"
    )
    parser.add_argument(
        "--no-prune",
        action="store_true",
        help="keep vectors the file no longer mentions",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="parse and measure the corpus without calling AWS",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = get_settings()
    embedder = TitanEmbedder.from_settings(settings)
    client = build_client(settings)
    report = asyncio.run(
        index_corpus(
            args.corpus,
            settings=settings,
            embedder=embedder,
            client=client,
            batch_size=args.batch_size,
            prune=not args.no_prune,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    )
    logger.info(report.summary())
    if report.oversized:
        raise SystemExit(
            f"{len(report.oversized)} documents were skipped for their size: "
            + ", ".join(report.oversized[:5])
        )


if __name__ == "__main__":
    main()
