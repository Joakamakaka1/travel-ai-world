"""Exponential backoff schedule, separated from what is being retried."""

from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_retries: int = 2
    base_delay: float = 1.0

    def delays(self) -> Iterator[float | None]:
        """One entry per attempt: the delay to wait *after* it fails, or None
        when it is the last attempt."""
        for attempt in range(self.max_retries + 1):
            yield None if attempt == self.max_retries else self.base_delay * 2**attempt
