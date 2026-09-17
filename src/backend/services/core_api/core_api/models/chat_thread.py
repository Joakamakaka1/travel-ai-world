from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core_api.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ChatThread(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One conversation with the assistant, private to the user who owns it.

    `updated_at` moves with every appended message, so a user's list shows the
    most recent conversations first. The messages are not a relationship: a
    thread is returned without them and the database cascades the delete
    (ADR 0013).
    """

    __tablename__ = "chat_threads"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Corpus city slug ("madrid", "berlin", "budapest"); null for a general chat.
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
