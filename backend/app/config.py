"""Settings from environment variables (or backend/.env). Defaults are safe for real Instagram use."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    db_path: str = "data/insta_lite.db"
    source: Literal["fake", "timeline"] = "fake"

    # Freshness vs. ban risk: worst-case staleness equals this interval.
    poll_interval_minutes: int = 60
    # Re-fetch a little before the last poll, to catch posts Instagram shows late.
    # Duplicates are harmless because posts are upserted.
    poll_overlap_minutes: int = 10
    # How far back the very first poll goes, when there is no last_polled_at yet.
    initial_lookback_hours: int = 24
    # Tests turn this off and call run_poll() directly.
    scheduler_enabled: bool = True

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:4173"]
