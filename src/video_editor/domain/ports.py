"""Port interfaces (abstractions) for infrastructure adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from video_editor.domain.models import EditConfig, KeepSegment, SilenceSegment, VideoJob


class SilenceDetectorPort(Protocol):
    """Detects silent regions in a video's audio track."""

    def detect_silence(
        self, input_path: Path, config: EditConfig
    ) -> list[SilenceSegment]:
        """Return silent segments detected in the input video."""
        ...


class VideoEditorPort(Protocol):
    """Cuts and concatenates video segments."""

    def cut_and_concat(
        self,
        input_path: Path,
        segments: list[KeepSegment],
        output_path: Path,
    ) -> Path:
        """Produce an edited video keeping only the given segments."""
        ...

    def get_duration(self, input_path: Path) -> float:
        """Return total duration of the input video in seconds."""
        ...


class StoragePort(Protocol):
    """Manages file storage for jobs."""

    def create_job_workspace(self, job_id: str) -> Path:
        """Create and return the workspace directory for a job."""
        ...

    def save_upload(self, job_id: str, filename: str, content: bytes) -> Path:
        """Save uploaded file and return its path."""
        ...

    def get_output_path(self, job_id: str) -> Path:
        """Return the expected output path for a job."""
        ...

    def cleanup_job(self, job_id: str) -> None:
        """Remove job workspace files."""
        ...


class JobRepositoryPort(Protocol):
    """Persists and retrieves job state."""

    def save(self, job: VideoJob) -> None:
        ...

    def get(self, job_id: str) -> VideoJob | None:
        ...

    def update(self, job: VideoJob) -> None:
        ...
