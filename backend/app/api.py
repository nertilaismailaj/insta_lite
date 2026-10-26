"""HTTP routes. Validates input at the boundary, then hands off to the repository."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request

from app import repository
from app.db import connection
from app.models import Post, Status

router = APIRouter()


def _require_timezone(name: str, value: datetime) -> datetime:
    # A time without an offset is ambiguous (whose local time?), so refuse to guess.
    if value.tzinfo is None:
        raise HTTPException(400, f"'{name}' must include a timezone, e.g. 2026-10-25T13:00:00Z")
    return value.astimezone(UTC)


@router.get("/posts")
def get_posts(
    request: Request,
    from_: Annotated[datetime, Query(alias="from")],
    to: datetime,
) -> list[Post]:
    from_ = _require_timezone("from", from_)
    to = _require_timezone("to", to)
    if from_ > to:
        raise HTTPException(400, "'from' must be before 'to'")

    with connection(request.app.state.settings.db_path) as conn:
        return repository.get_posts(conn, from_, to)


@router.get("/status")
def get_status(request: Request) -> Status:
    with connection(request.app.state.settings.db_path) as conn:
        return Status(last_polled_at=repository.get_last_polled_at(conn))
