"""Database layer: schema creation, SQLite configuration, connections and the time format.

The DB path is passed in rather than read from config, so tests can use a temporary DB.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
  id       INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  source   TEXT NOT NULL CHECK (source IN ('fake', 'timeline'))
);

CREATE TABLE IF NOT EXISTS posts (
  id          INTEGER PRIMARY KEY,                       -- surrogate key
  external_id TEXT NOT NULL UNIQUE,                      -- IG shortcode: natural key, dedup
  account_id  INTEGER NOT NULL REFERENCES accounts(id),
  taken_at    TEXT NOT NULL,                             -- UTC, see to_db_time()
  caption     TEXT,
  media_url   TEXT,
  permalink   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_posts_taken_at ON posts(taken_at);

CREATE TABLE IF NOT EXISTS poll_state (
  id             INTEGER PRIMARY KEY CHECK (id = 1),     -- singleton row
  last_polled_at TEXT
);
INSERT OR IGNORE INTO poll_state (id, last_polled_at) VALUES (1, NULL);
"""

# The one canonical time format stored in the DB. Fixed width and always UTC,
# so comparing the strings gives the same order as comparing the times.
DB_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def to_db_time(dt: datetime) -> str:
    """The only way times are written to the DB."""
    if dt.tzinfo is None:
        raise ValueError("naive datetime: timezone unknown, refusing to guess")
    return dt.astimezone(UTC).strftime(DB_TIME_FORMAT)


def from_db_time(value: str) -> datetime:
    return datetime.strptime(value, DB_TIME_FORMAT).replace(tzinfo=UTC)


def init_db(db_path: str | Path) -> None:
    """Create tables if missing. Safe to run on every startup (idempotent)."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with connection(db_path) as conn:
        # WAL is stored in the DB file, so setting it once is enough.
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    """A new connection with per-connection settings applied.

    Use one connection per request/poll, never a shared global: the poller runs in a
    background thread and sqlite3 connections must not be shared across threads.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # rows behave like dicts: row["taken_at"]
    conn.execute("PRAGMA foreign_keys = ON")  # off by default in SQLite
    conn.execute("PRAGMA busy_timeout = 5000")  # wait up to 5 s if locked
    return conn


@contextmanager
def connection(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Connection as a unit of work: commit on success, roll back on error, always close."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
