# insta_lite

A personal Instagram client that limits how much time you spend on Instagram. Instead of an endless algorithmic feed, you pick a time range (e.g. "last hour") and see only posts from accounts you follow that were posted in that range.

Runs on a laptop and on an Android phone (as a PWA).

**Stack:** React (frontend), FastAPI (backend), SQLite (database)

## Architecture

```
                    ┌──────────────── Backend (FastAPI process) ─────────────────┐
                    │                                                            │
 React PWA  ──HTTP──▶  API layer                                                 │
 (laptop/phone)     │   GET  /posts?from=&to=   (UTC, offset-aware ISO in)       │
                    │   POST /refresh           (queues a poll, with cooldown)     │
                    │        │                                                   │
                    │        ▼ reads                                             │
                    │   SQLite  ◀── upserts ──  Poller (APScheduler,             │
                    │                            max_instances=1, every ~60 min) │
                    │                                  │                         │
                    │                       Source interface: fetch_posts()      │
                    │                         ├─ FakeSource       (dev/seed)     │
                    │                         ├─ OfficialSource   (Graph API)    │
                    │                         └─ UnofficialSource (instagrapi)   │
                    └──────────────────────────────────┼─────────────────────────┘
                                                       ▼
                                                   Instagram
```

## Design decisions

| Decision | Reason |
|---|---|
| **Ingestion decoupled from serving** | Fast reads, the app works when Instagram is down, and opening the app costs 0 Instagram calls |
| **Hybrid sources behind one interface (Adapter pattern)** | Followed accounts are a mix. Creators/brands go through the official Graph API (Business Discovery), and personal accounts go through instagrapi. The rest of the system sees only one `Post` shape. |
| **instagrapi (sync), not aiograpi** | The bottleneck is Instagram's rate limits, not I/O, so async gains nothing. instagrapi also has a bigger community. |
| **Polling every ~60 min + "Refresh now" with cooldown** | Trades data freshness against ban risk. Worst-case staleness is the poll interval (eventual consistency). |
| **One poller at a time (`max_instances=1`)** | Simplest mutual exclusion for a single-process app. Move to a DB lease with heartbeat only if more processes are added. |
| **Idempotent upserts on a `UNIQUE` natural key** | No duplicates. A crash just means rerunning the poller, and retries are safe. The DB enforces the invariant, which avoids check-then-act races. |
| **UTC in the core, local time only in React** | Convert at the boundaries, keep one canonical form |
| **Index on `taken_at`** | The time-range query uses a B-tree range scan instead of a full table scan |

## Schema (v1)

```sql
CREATE TABLE accounts (
  id             INTEGER PRIMARY KEY,
  username       TEXT NOT NULL UNIQUE,
  source         TEXT NOT NULL CHECK (source IN ('fake','official','unofficial')),
  last_polled_at TEXT                          -- UTC
);

CREATE TABLE posts (
  id          INTEGER PRIMARY KEY,             -- surrogate key
  external_id TEXT NOT NULL UNIQUE,            -- IG shortcode (natural key, dedup)
  account_id  INTEGER NOT NULL REFERENCES accounts(id),
  taken_at    TEXT NOT NULL,                   -- UTC
  caption     TEXT,
  media_url   TEXT,
  permalink   TEXT
);
CREATE INDEX idx_posts_taken_at ON posts(taken_at);
```

Core query:

```sql
SELECT * FROM posts
WHERE taken_at BETWEEN :from AND :to
ORDER BY taken_at DESC;
```

## Build order

1. Core: schema, API, React date-range UI, with `FakeSource` and seed data
2. `OfficialSource` (Graph API Business Discovery)
3. `UnofficialSource` (instagrapi)

## Open questions

- **Hosting:** home Wi-Fi only, Tailscale, or a cloud VM
- **Phone:** PWA (suggested) or a native APK
- **Content:** feed posts only, or stories and reels too; show media in-app or link out to Instagram
- **Number of followed accounts:** decides whether to poll per account or read the timeline feed

## Risks

- `UnofficialSource` breaks Instagram's Terms of Service, and the account could be flagged or banned. Keep polling slow and reuse sessions (see instagrapi's best-practices docs).
- The unofficial API breaks whenever Instagram changes its private endpoints.

## References

- instagrapi: https://github.com/subzeroid/instagrapi ([docs](https://subzeroid.github.io/instagrapi/))
- Graph API Business Discovery: https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/business_discovery
