"""Health check endpoint."""

import shutil

from fastapi import APIRouter

from video_editor import __version__
from video_editor.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    ffmpeg_available = shutil.which("ffmpeg") is not None
    return HealthResponse(
        status="ok" if ffmpeg_available else "degraded",
        ffmpeg_available=ffmpeg_available,
        version=__version__,
    )
