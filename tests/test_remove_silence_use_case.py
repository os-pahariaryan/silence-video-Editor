"""Tests for RemoveSilenceUseCase with mocked ports."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from video_editor.application.remove_silence import RemoveSilenceUseCase
from video_editor.domain.exceptions import VideoProcessingError
from video_editor.domain.models import EditConfig, JobStatus, SilenceSegment, VideoJob


@pytest.fixture
def config() -> EditConfig:
    return EditConfig(min_silence_duration=1.0)


@pytest.fixture
def job(config: EditConfig, tmp_path: Path) -> VideoJob:
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake")
    return VideoJob(
        input_path=input_file,
        config=config,
        status=JobStatus.QUEUED,
    )


def test_execute_happy_path(job: VideoJob, tmp_path: Path, config: EditConfig):
    output_path = tmp_path / "output.mp4"

    detector = MagicMock()
    detector.detect_silence.return_value = [
        SilenceSegment(start=2.0, end=5.0),
    ]

    editor = MagicMock()
    editor.get_duration.return_value = 10.0
    editor.cut_and_concat.return_value = output_path

    storage = MagicMock()
    storage.get_output_path.return_value = output_path

    use_case = RemoveSilenceUseCase(detector, editor, storage)
    progress_updates: list[JobStatus] = []

    def on_progress(j: VideoJob) -> None:
        progress_updates.append(j.status)

    result = use_case.execute(job, on_progress=on_progress)

    assert result == output_path
    assert job.status == JobStatus.COMPLETED
    assert JobStatus.DETECTING in progress_updates
    assert JobStatus.EDITING in progress_updates
    detector.detect_silence.assert_called_once_with(job.input_path, config)
    editor.cut_and_concat.assert_called_once()


def test_execute_all_silent_raises(job: VideoJob):
    detector = MagicMock()
    detector.detect_silence.return_value = [
        SilenceSegment(start=0.0, end=10.0),
    ]

    editor = MagicMock()
    editor.get_duration.return_value = 10.0

    storage = MagicMock()

    use_case = RemoveSilenceUseCase(detector, editor, storage)

    with pytest.raises(VideoProcessingError, match="entirely silent"):
        use_case.execute(job)
