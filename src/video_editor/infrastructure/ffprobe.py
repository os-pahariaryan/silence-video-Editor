"""FFprobe wrapper for video metadata."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from video_editor.domain.exceptions import VideoProcessingError

logger = logging.getLogger(__name__)


def get_duration(input_path: Path) -> float:
    """Return video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        str(input_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        return duration
    except (subprocess.CalledProcessError, KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.error("ffprobe failed for %s: %s", input_path, exc)
        raise VideoProcessingError(f"Failed to probe video duration: {exc}") from exc


def has_audio_stream(input_path: Path) -> bool:
    """Check whether the input file contains an audio stream."""
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "csv=p=0",
        str(input_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return "audio" in result.stdout
    except subprocess.CalledProcessError as exc:
        logger.error("ffprobe audio check failed for %s: %s", input_path, exc)
        raise VideoProcessingError(f"Failed to check audio stream: {exc}") from exc
