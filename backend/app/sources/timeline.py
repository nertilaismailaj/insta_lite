"""The real source: your Instagram home timeline via instagrapi. Not implemented yet."""

from datetime import datetime
from typing import Literal

from app.models import FetchedPost


class TimelineSource:
    name: Literal["timeline"] = "timeline"

    def fetch_posts(self, since: datetime) -> list[FetchedPost]:
        raise NotImplementedError("TimelineSource is not built yet; set SOURCE=fake")
