"""FFmpeg silencedetect adapter."""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

from video_editor.domain.exceptions import VideoProcessingError
from video_editor.domain.models import EditConfig, SilenceSegment

logger = logging.getLogger(__name__)

_SILENCE_START_RE = re.compile(r"silence_start:\s*([\d.]+)")
_SILENCE_END_RE = re.compile(r"silence_end:\s*([\d.]+)")


def parse_silencedetect_output(stderr: str) -> list[SilenceSegment]:
    """
    Parse FFmpeg silencedetect filter output from stderr.

    FFmpeg emits pairs of silence_start and silence_end lines.
    An unclosed silence_start at EOF is closed at the last known position.
    """
    segments: list[SilenceSegment] = []
    pending_start: float | None = None

    for line in stderr.splitlines():
        start_match = _SILENCE_START_RE.search(line)
        if start_match:
            pending_start = float(start_match.group(1))
            continue

        end_match = _SILENCE_END_RE.search(line)
        if end_match and pending_start is not None:
            end_time = float(end_match.group(1))
            if end_time > pending_start:
                segments.append(SilenceSegment(start=pending_start, end=end_time))
            pending_start = None

    return segments


class FFmpegSilenceDetector:
    """Detects silence using FFmpeg's silencedetect audio filter."""

    def detect_silence(
        self, input_path: Path, config: EditConfig
    ) -> list[SilenceSegment]:
        """Run silencedetect and return segments meeting min duration."""
        threshold = config.silence_threshold_db
        min_duration = config.min_silence_duration

        cmd = [
            "ffmpeg",
            "-i",
            str(input_path),
            "-af",
            f"silencedetect=noise={threshold}dB:d={min_duration}",
            "-f",
            "null",
            "-",
        ]

        logger.info(
            "Running silence detection on %s (threshold=%sdB, min_duration=%ss)",
            input_path,
            threshold,
            min_duration,
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError as exc:
            raise VideoProcessingError(f"Failed to run ffmpeg: {exc}") from exc

        if result.returncode != 0 and not result.stderr:
            raise VideoProcessingError(
                f"FFmpeg silence detection failed (exit {result.returncode})"
            )

        segments = parse_silencedetect_output(result.stderr)
        logger.info("Detected %d silence segments in %s", len(segments), input_path)
        return segments
