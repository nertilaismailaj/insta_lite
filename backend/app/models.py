"""Pydantic models. `Post` is the API contract and mirrors frontend/src/types.ts."""

from datetime import datetime

from pydantic import BaseModel


class FetchedPost(BaseModel):
    """What a source returns: a post normalized into our shape, not yet stored (no id)."""

    external_id: str  # IG shortcode
    username: str
    taken_at: datetime  # timezone-aware
    caption: str | None = None
    media_url: str | None = None
    permalink: str


class Post(FetchedPost):
    """A stored post, as returned by GET /posts."""

    id: int


class Status(BaseModel):
    last_polled_at: datetime | None
