"""Use case: remove silence from a video."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from video_editor.application.segment_builder import compute_keep_segments
from video_editor.domain.exceptions import VideoProcessingError
from video_editor.domain.models import EditConfig, JobStatus, VideoJob
from video_editor.domain.ports import (
    SilenceDetectorPort,
    StoragePort,
    VideoEditorPort,
)

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[VideoJob], None]


class RemoveSilenceUseCase:
    """Orchestrates silence detection and video editing."""

    def __init__(
        self,
        detector: SilenceDetectorPort,
        editor: VideoEditorPort,
        storage: StoragePort,
    ) -> None:
        self._detector = detector
        self._editor = editor
        self._storage = storage

    def execute(
        self,
        job: VideoJob,
        on_progress: ProgressCallback | None = None,
    ) -> Path:
        """
        Run the full silence-removal pipeline for a job.

        Updates job status/progress via on_progress callback.
        Returns path to the edited output video.
        """
        if job.input_path is None or job.config is None:
            raise VideoProcessingError("Job is missing input path or config")

        config = job.config
        input_path = job.input_path
        output_path = self._storage.get_output_path(job.id)

        self._update(job, JobStatus.DETECTING, 10, "detecting", on_progress)

        total_duration = self._editor.get_duration(input_path)
        silence_segments = self._detector.detect_silence(input_path, config)

        logger.info(
            "Job %s: %d silence segments in %.1fs video",
            job.id,
            len(silence_segments),
            total_duration,
        )

        keep_segments = compute_keep_segments(
            silence_segments, total_duration, config
        )

        if not keep_segments:
            raise VideoProcessingError(
                "Video is entirely silent — nothing to keep after processing"
            )

        original_keep_duration = sum(s.duration for s in keep_segments)
        logger.info(
            "Job %s: keeping %d segments (%.1fs of %.1fs)",
            job.id,
            len(keep_segments),
            original_keep_duration,
            total_duration,
        )

        self._update(job, JobStatus.EDITING, 50, "editing", on_progress)

        result = self._editor.cut_and_concat(input_path, keep_segments, output_path)

        self._update(job, JobStatus.COMPLETED, 100, "completed", on_progress)
        job.output_path = result

        return result

    def _update(
        self,
        job: VideoJob,
        status: JobStatus,
        progress: int,
        stage: str,
        on_progress: ProgressCallback | None,
    ) -> None:
        job.status = status
        job.progress = progress
        job.stage = stage
        if on_progress:
            on_progress(job)
