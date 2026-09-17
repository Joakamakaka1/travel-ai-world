"""Pure domain types. No framework imports."""

from dataclasses import dataclass, field
from typing import Literal

ChatRole = Literal["system", "user", "assistant"]
"""Who speaks in a chat turn (not to be confused with a user's account Role)."""


@dataclass(frozen=True, slots=True)
class Message:
    role: ChatRole
    content: str


@dataclass(frozen=True, slots=True)
class Document:
    """A retrieved passage that can ground an answer (RAG)."""

    id: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class Usage:
    """What a provider reports about one answer; adapters fill what they know."""

    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(slots=True)
class ChatTrace:
    """What one answer was built from, filled in while it streams."""

    documents: list[Document] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)


@dataclass(frozen=True, slots=True)
class Source:
    """A document an answer was grounded on, as a conversation keeps it."""

    doc_id: str
    title: str | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class ChatTurn:
    """One message of a recorded conversation (ADR 0013)."""

    role: Literal["user", "assistant"]
    content: str
    sources: tuple[Source, ...] = ()
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None


@dataclass(frozen=True, slots=True)
class ThreadSaved:
    """Stream event: the exchange was recorded in this conversation."""

    thread_id: str


@dataclass(frozen=True, slots=True)
class GenerationParams:
    """Sampling settings handed to whichever provider answers."""

    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 0.95
