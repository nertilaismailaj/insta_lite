"""The ONLY module with SQL.

Functions take a connection instead of opening one, so the caller decides what forms
one transaction (see db.connection()).
"""

import sqlite3
from datetime import datetime

from app.db import from_db_time, to_db_time
from app.models import FetchedPost, Post


def upsert_account(conn: sqlite3.Connection, username: str, source: str) -> int:
    row = conn.execute(
        """
        INSERT INTO accounts (username, source) VALUES (?, ?)
        ON CONFLICT(username) DO UPDATE SET source = excluded.source
        RETURNING id
        """,
        (username, source),
    ).fetchone()
    return row["id"]


def upsert_posts(conn: sqlite3.Connection, posts: list[FetchedPost], source: str) -> int:
    """Insert new posts and update known ones. Returns how many were new.

    Idempotent: saving the same posts twice leaves the DB as if saved once.
    """
    before = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    account_ids: dict[str, int] = {}
    for post in posts:
        if post.username not in account_ids:
            account_ids[post.username] = upsert_account(conn, post.username, source)
        conn.execute(
            """
            INSERT INTO posts (external_id, account_id, taken_at, caption, media_url, permalink)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(external_id) DO UPDATE SET
              caption   = excluded.caption,
              media_url = excluded.media_url,   -- refreshes expiring CDN URLs
              permalink = excluded.permalink
            """,
            (
                post.external_id,
                account_ids[post.username],
                to_db_time(post.taken_at),
                post.caption,
                post.media_url,
                post.permalink,
            ),
        )
    after = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    return after - before


def get_posts(conn: sqlite3.Connection, from_: datetime, to: datetime) -> list[Post]:
    """Posts taken in [from_, to], newest first. Uses idx_posts_taken_at for the range."""
    rows = conn.execute(
        """
        SELECT p.id, p.external_id, a.username, p.taken_at, p.caption, p.media_url, p.permalink
        FROM posts p
        JOIN accounts a ON a.id = p.account_id
        WHERE p.taken_at BETWEEN ? AND ?
        ORDER BY p.taken_at DESC
        """,
        (to_db_time(from_), to_db_time(to)),
    ).fetchall()
    return [Post(**{**dict(row), "taken_at": from_db_time(row["taken_at"])}) for row in rows]


def get_last_polled_at(conn: sqlite3.Connection) -> datetime | None:
    value = conn.execute("SELECT last_polled_at FROM poll_state WHERE id = 1").fetchone()[0]
    return from_db_time(value) if value else None


def set_last_polled_at(conn: sqlite3.Connection, when: datetime) -> None:
    conn.execute("UPDATE poll_state SET last_polled_at = ? WHERE id = 1", (to_db_time(when),))
