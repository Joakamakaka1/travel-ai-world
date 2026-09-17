import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from travel_common.exceptions import UnprocessableEntity

from core_api.models.base import Base, UUIDPrimaryKeyMixin
from core_api.models.enums import ChatRole


class ChatMessage(UUIDPrimaryKeyMixin, Base):
    """One turn of a conversation: appended, never edited.

    An assistant answer keeps what it was grounded on (`sources`), the model
    that wrote it and what it cost (`input_tokens`, `output_tokens`,
    `latency_ms`), so a conversation can be reviewed afterwards.
    """

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_thread_id_created_at", "thread_id", "created_at"),
    )

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_threads.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # ChatRole
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # [{"doc_id", "score", "title", "url"}, ...] for answers built on the corpus.
    sources: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)
    model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # clock_timestamp(), not now(): two messages written in one transaction
    # (the question and its answer) still get distinct, ordered times.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.clock_timestamp(),
        nullable=False,
    )

    def check_invariants(self) -> None:
        if self.role == ChatRole.USER and any(
            value is not None
            for value in (
                self.sources,
                self.model,
                self.input_tokens,
                self.output_tokens,
                self.latency_ms,
            )
        ):
            raise UnprocessableEntity(
                "A user message has no sources, model or usage: only answers do"
            )
