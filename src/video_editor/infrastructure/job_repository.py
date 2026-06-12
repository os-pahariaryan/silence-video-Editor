"""In-memory job repository."""

from __future__ import annotations

import threading
from datetime import datetime, timezone

from video_editor.domain.models import VideoJob


class InMemoryJobRepository:
    """Thread-safe in-memory store for job state."""

    def __init__(self) -> None:
        self._jobs: dict[str, VideoJob] = {}
        self._lock = threading.Lock()

    def save(self, job: VideoJob) -> None:
        with self._lock:
            self._jobs[job.id] = job

    def get(self, job_id: str) -> VideoJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job: VideoJob) -> None:
        job.updated_at = datetime.now(timezone.utc)
        with self._lock:
            self._jobs[job.id] = job
