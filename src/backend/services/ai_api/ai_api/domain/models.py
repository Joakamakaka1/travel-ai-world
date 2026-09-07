"""Pure domain types. No framework imports."""

from dataclasses import dataclass, field
from typing import Literal

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True, slots=True)
class Message:
    role: Role
    content: str


@dataclass(frozen=True, slots=True)
class Document:
    """A retrieved passage that can ground an answer (RAG)."""

    id: str
    content: str
    metadata: dict[str, str] = field(default_factory=dict)
