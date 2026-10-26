from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import connection, to_db_time
from app.main import create_app
from app.poller import run_poll
from app.sources.fake import FakeSource

NOW = datetime(2026, 10, 25, 14, 5, tzinfo=UTC)
OVERLAP = timedelta(minutes=10)
LOOKBACK = timedelta(hours=24)


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def client(db_path):
    # Fresh DB per test, no scheduler: tests call run_poll() themselves.
    app = create_app(Settings(db_path=str(db_path), scheduler_enabled=False, _env_file=None))
    with TestClient(app) as c:  # `with` runs the lifespan, which creates the schema
        yield c


def poll(db_path, now=NOW):
    return run_poll(db_path, FakeSource(clock=lambda: now), OVERLAP, LOOKBACK, now=now)


def count_posts(db_path):
    with connection(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]


def test_last_hour_returns_posts_newest_first_in_contract_shape(client, db_path):
    poll(db_path)

    res = client.get("/posts", params={"from": "2026-10-25T13:05:00Z", "to": "2026-10-25T14:05:00Z"})

    assert res.status_code == 200
    posts = res.json()
    # Fake posts are on :00/:20/:40, so 13:20, 13:40, 14:00 fall in the range.
    assert [p["taken_at"] for p in posts] == [
        "2026-10-25T14:00:00Z",
        "2026-10-25T13:40:00Z",
        "2026-10-25T13:20:00Z",
    ]
    assert set(posts[0]) == {"id", "external_id", "username", "taken_at", "caption", "media_url", "permalink"}


def test_offset_timestamps_are_normalized_to_utc(client, db_path):
    poll(db_path)
    # 15:05+01:00 is 14:05Z: the same range as the test above.
    res = client.get("/posts", params={"from": "2026-10-25T14:05:00+01:00", "to": "2026-10-25T15:05:00+01:00"})
    assert len(res.json()) == 3


def test_polling_twice_is_idempotent(db_path, client):
    first = poll(db_path)
    second = poll(db_path)  # same clock: everything is a duplicate
    assert first > 0
    assert second == 0
    assert count_posts(db_path) == first


def test_overlapping_polls_add_only_new_posts(db_path, client):
    poll(db_path)
    total = count_posts(db_path)
    # One hour later: the overlap window refetches some known posts, plus 3 new slots.
    new = poll(db_path, now=NOW + timedelta(hours=1))
    assert new == 3
    assert count_posts(db_path) == total + 3


def test_status_reports_last_poll(client, db_path):
    assert client.get("/status").json() == {"last_polled_at": None}
    poll(db_path)
    assert client.get("/status").json() == {"last_polled_at": "2026-10-25T14:05:00Z"}


@pytest.mark.parametrize(
    "params",
    [
        {"from": "2026-10-25T13:00:00", "to": "2026-10-25T14:00:00Z"},  # no timezone
        {"from": "2026-10-25T15:00:00Z", "to": "2026-10-25T14:00:00Z"},  # from > to
    ],
)
def test_invalid_ranges_are_rejected(client, params):
    assert client.get("/posts", params=params).status_code == 400


def test_db_time_strings_sort_like_times():
    plus2 = datetime(2026, 10, 25, 14, 0, tzinfo=UTC).astimezone()  # any local offset
    assert to_db_time(plus2) == "2026-10-25T14:00:00Z"
    with pytest.raises(ValueError):
        to_db_time(datetime(2026, 10, 25, 14, 0))
