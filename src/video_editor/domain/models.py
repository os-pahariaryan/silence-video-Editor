"""Domain models for the video editor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from uuid import uuid4


class JobStatus(str, Enum):
    QUEUED = "queued"
    DETECTING = "detecting"
    EDITING = "editing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class EditConfig:
    """User-configurable parameters for silence removal."""

    min_silence_duration: float = 1.0
    silence_threshold_db: float = -35.0
    padding_before: float = 0.1
    padding_after: float = 0.1
    min_segment_duration: float = 0.05

    def validate(self) -> None:
        """Validate configuration values."""
        from video_editor.domain.exceptions import InvalidConfigError

        if self.min_silence_duration <= 0:
            raise InvalidConfigError("min_silence_duration must be positive")
        if self.silence_threshold_db >= 0:
            raise InvalidConfigError("silence_threshold_db must be negative")
        if self.padding_before < 0 or self.padding_after < 0:
            raise InvalidConfigError("padding values must be non-negative")
        if self.min_segment_duration <= 0:
            raise InvalidConfigError("min_segment_duration must be positive")


@dataclass(frozen=True)
class SilenceSegment:
    """A detected silent region in the audio track."""

    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass(frozen=True)
class KeepSegment:
    """A segment of video/audio to retain after silence removal."""

    start: float
    end: float

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class VideoJob:
    """Represents a video processing job."""

    id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    stage: str = "queued"
    error: str | None = None
    input_path: Path | None = None
    output_path: Path | None = None
    config: EditConfig | None = None
    original_filename: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def download_ready(self) -> bool:
        return self.status == JobStatus.COMPLETED and self.output_path is not None
