"""One poll: fetch from the source, save to the DB, record when."""

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app import repository
from app.db import connection
from app.sources.base import Source

log = logging.getLogger(__name__)


def run_poll(
    db_path: str | Path,
    source: Source,
    overlap: timedelta,
    initial_lookback: timedelta,
    now: datetime | None = None,
) -> int:
    """Returns how many new posts were saved. Safe to rerun after a crash (idempotent)."""
    # Captured before fetching: posts made during a slow fetch are covered by the next poll.
    started_at = now or datetime.now(UTC)

    with connection(db_path) as conn:
        last = repository.get_last_polled_at(conn)
    since = last - overlap if last else started_at - initial_lookback

    # The network call happens outside any transaction, so a slow Instagram
    # never holds the DB's write lock.
    posts = source.fetch_posts(since)

    # Saving the posts and moving last_polled_at forward is one unit of work:
    # either both happen or neither does.
    with connection(db_path) as conn:
        new = repository.upsert_posts(conn, posts, source.name)
        repository.set_last_polled_at(conn, started_at)

    log.info("poll done: fetched=%d new=%d since=%s", len(posts), new, since.isoformat())
    return new
