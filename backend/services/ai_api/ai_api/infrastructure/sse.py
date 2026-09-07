"""Server-Sent Events, both directions.

- `SSEParser` reads an upstream provider's byte stream into `data:` payloads.
- `sse_stream` writes our own wire format for the browser:

      data: {"content": "Hola"}
      data: {"error": "..."}
      data: [DONE]
"""

import json
import logging
from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)

DONE = "data: [DONE]\n\n"


def encode_event(payload: dict[str, str]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


class SSEParser:
    """Incremental line parser; call `feed` per chunk, get complete `data:` bodies."""

    def __init__(self) -> None:
        self._buffer = ""

    def feed(self, chunk: str) -> list[str]:
        self._buffer += chunk
        lines = self._buffer.split("\n")
        self._buffer = lines.pop()
        events: list[str] = []
        for raw in lines:
            line = raw.strip()
            if line.startswith("data:"):
                events.append(line[5:].strip())
        return events


async def sse_stream(deltas: AsyncIterator[str]) -> AsyncIterator[str]:
    """Wrap text deltas into our SSE format; errors become a final event."""
    try:
        async for delta in deltas:
            yield encode_event({"content": delta})
    except Exception as exc:  # the response has started: report in-band
        logger.error("Chat stream failed: %s", exc)
        yield encode_event({"error": str(exc)})
    yield DONE
