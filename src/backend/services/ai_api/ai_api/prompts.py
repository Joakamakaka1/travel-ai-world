"""Prompts. Kept out of code paths so they can be tuned in isolation."""

from collections.abc import Iterable

from ai_api.domain.models import Document

CHAT_SYSTEM_PROMPT = (
    "You are the Travel AI World planning assistant. Turn the user's trip idea "
    "into a concrete, day-by-day itinerary: ask for whatever is missing (dates, "
    "budget, number of travellers, pace) instead of guessing, and keep every "
    "suggestion specific and practical. Reply in the language the user writes in."
)

RAG_CONTEXT_PROMPT = (
    "Background information retrieved from the Travel AI World city corpus. "
    "Prefer it over your own knowledge, name the places it mentions, and never "
    "invent places, prices or opening hours it does not give. If it does not "
    "cover the question, say so briefly and answer from general knowledge.\n\n"
    "{context}"
)
"""Second system turn carrying retrieved passages; `{context}` is filled in."""


def format_context(documents: Iterable[Document]) -> str:
    """The passages as the model reads them.

    Each keeps the little that makes it usable — what it is called, what kind
    of place it is, where in the city, and where it came from — so the model
    can tell a bath from a museum and offer a link.
    """
    return "\n\n".join(_passage(document) for document in documents)


def _passage(document: Document) -> str:
    metadata = document.metadata
    heading = " · ".join(
        str(value)
        for value in (
            metadata.get("name") or metadata.get("heading_path"),
            metadata.get("category"),
            metadata.get("district"),
        )
        if value
    )
    source = metadata.get("url") or metadata.get("source_url")
    lines = [line for line in (heading, document.content) if line]
    if source:
        lines.append(f"Source: {source}")
    return "\n".join(lines)
