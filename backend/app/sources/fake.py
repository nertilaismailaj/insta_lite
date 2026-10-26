"""A fake source for development and tests: no network, no Instagram, no ban risk."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.models import FetchedPost

USERNAMES = ["anna", "marco", "sofia", "liam", "elena", "noah"]
SLOT = timedelta(minutes=20)
MAX_LOOKBACK = timedelta(hours=24)


class FakeSource:
    """One post every 20 minutes, aligned to the clock (xx:00, xx:20, xx:40).

    Each post's ID comes from its time slot, so the same post gets the same ID on every
    poll. Overlapping polls therefore return duplicates, which the upsert must absorb.
    """

    name: Literal["fake"] = "fake"

    def __init__(self, clock: Callable[[], datetime] = lambda: datetime.now(UTC)) -> None:
        self._clock = clock

    def fetch_posts(self, since: datetime) -> list[FetchedPost]:
        now = self._clock()
        since = max(since, now - MAX_LOOKBACK)

        slot_seconds = int(SLOT.total_seconds())
        first = -(-int(since.timestamp()) // slot_seconds) * slot_seconds  # round up to a slot
        posts = []
        for ts in range(first, int(now.timestamp()) + 1, slot_seconds):
            shortcode = f"FAKE{ts}"
            posts.append(
                FetchedPost(
                    external_id=shortcode,
                    username=USERNAMES[(ts // slot_seconds) % len(USERNAMES)],
                    taken_at=datetime.fromtimestamp(ts, UTC),
                    caption=f"Fake post from slot {ts}",
                    media_url=f"https://picsum.photos/seed/{shortcode}/600/600",
                    permalink=f"https://www.instagram.com/p/{shortcode}/",
                )
            )
        return posts
