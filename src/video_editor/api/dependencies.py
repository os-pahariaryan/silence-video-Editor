"""Dependency injection wiring."""

from __future__ import annotations

from functools import lru_cache

from video_editor.application.job_service import JobService
from video_editor.application.remove_silence import RemoveSilenceUseCase
from video_editor.config import Settings
from video_editor.infrastructure.ffmpeg_detector import FFmpegSilenceDetector
from video_editor.infrastructure.ffmpeg_editor import FFmpegVideoEditor
from video_editor.infrastructure.job_repository import InMemoryJobRepository
from video_editor.infrastructure.local_storage import LocalFileStorage


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_job_service() -> JobService:
    settings = get_settings()
    storage = LocalFileStorage(settings.data_dir)
    detector = FFmpegSilenceDetector()
    editor = FFmpegVideoEditor()
    use_case = RemoveSilenceUseCase(detector, editor, storage)
    repository = InMemoryJobRepository()
    return JobService(repository, storage, use_case)
