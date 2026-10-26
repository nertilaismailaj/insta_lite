"""App factory: wires settings, DB, source, scheduler and routes together.

Run with a single worker: each worker process would start its own scheduler (two pollers).
    uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.config import Settings
from app.db import init_db
from app.poller import run_poll
from app.sources.base import Source
from app.sources.fake import FakeSource
from app.sources.timeline import TimelineSource

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def build_source(settings: Settings) -> Source:
    return FakeSource() if settings.source == "fake" else TimelineSource()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db(settings.db_path)
        scheduler = None
        if settings.scheduler_enabled:
            scheduler = BackgroundScheduler(timezone=UTC)
            scheduler.add_job(
                run_poll,
                "interval",
                minutes=settings.poll_interval_minutes,
                kwargs={
                    "db_path": settings.db_path,
                    "source": build_source(settings),
                    "overlap": timedelta(minutes=settings.poll_overlap_minutes),
                    "initial_lookback": timedelta(hours=settings.initial_lookback_hours),
                },
                max_instances=1,  # never two polls at once
                coalesce=True,  # missed runs (e.g. laptop asleep) collapse into one
                next_run_time=datetime.now(UTC),  # poll once right at startup
            )
            scheduler.start()
        yield
        if scheduler:
            scheduler.shutdown(wait=False)

    app = FastAPI(title="Insta Lite", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
