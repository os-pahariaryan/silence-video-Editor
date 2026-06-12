"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from video_editor import __version__
from video_editor.api.dependencies import get_settings
from video_editor.api.routes import health, jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Video Editor v%s starting (data_dir=%s)", __version__, settings.data_dir)
    yield
    logger.info("Video Editor shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Video Editor",
        description="Remove long silence periods from videos",
        version=__version__,
        lifespan=lifespan,
    )

    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])

    if STATIC_DIR.exists():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


app = create_app()
