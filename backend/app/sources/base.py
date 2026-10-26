"""The source interface. The poller depends on this, never on a concrete source."""

from datetime import datetime
from typing import Literal, Protocol

from app.models import FetchedPost


class Source(Protocol):
    # Stored in accounts.source.
    name: Literal["fake", "timeline"]

    def fetch_posts(self, since: datetime) -> list[FetchedPost]:
        """Posts taken at or after `since`, normalized to FetchedPost (the Adapter's job)."""
        ...
