"""FFmpeg video cutting and concatenation."""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from video_editor.domain.exceptions import VideoProcessingError
from video_editor.domain.models import KeepSegment
from video_editor.infrastructure import ffprobe

logger = logging.getLogger(__name__)


class FFmpegVideoEditor:
    """Cuts and concatenates video segments using FFmpeg."""

    def get_duration(self, input_path: Path) -> float:
        return ffprobe.get_duration(input_path)

    def cut_and_concat(
        self,
        input_path: Path,
        segments: list[KeepSegment],
        output_path: Path,
    ) -> Path:
        """Produce edited video by trimming and concatenating keep segments."""
        if not segments:
            raise VideoProcessingError(
                "No segments to keep — video appears to be entirely silent"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if len(segments) == 1:
            return self._single_trim(input_path, segments[0], output_path)

        return self._concat_segments(input_path, segments, output_path)

    def _single_trim(
        self, input_path: Path, segment: KeepSegment, output_path: Path
    ) -> Path:
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(segment.start),
            "-i",
            str(input_path),
            "-t",
            str(segment.duration),
            "-c",
            "copy",
            "-avoid_negative_ts",
            "make_zero",
            str(output_path),
        ]
        self._run_ffmpeg(cmd, "single trim")
        return output_path

    def _concat_segments(
        self,
        input_path: Path,
        segments: list[KeepSegment],
        output_path: Path,
    ) -> Path:
        """Extract each segment with stream copy, then concat via demuxer."""
        with tempfile.TemporaryDirectory(dir=output_path.parent) as tmp_dir:
            tmp = Path(tmp_dir)
            segment_files: list[Path] = []

            for i, seg in enumerate(segments):
                seg_path = tmp / f"seg_{i:04d}.mp4"
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-ss",
                    str(seg.start),
                    "-i",
                    str(input_path),
                    "-t",
                    str(seg.duration),
                    "-c",
                    "copy",
                    "-avoid_negative_ts",
                    "make_zero",
                    str(seg_path),
                ]
                self._run_ffmpeg(cmd, f"extract segment {i}")
                segment_files.append(seg_path)

            list_file = tmp / "concat_list.txt"
            list_file.write_text(
                "\n".join(f"file '{p.resolve()}'" for p in segment_files)
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c",
                "copy",
                str(output_path),
            ]
            self._run_ffmpeg(cmd, "concat segments")

        return output_path

    def _run_ffmpeg(self, cmd: list[str], operation: str) -> None:
        logger.info("FFmpeg %s: %s", operation, " ".join(cmd))
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except OSError as exc:
            raise VideoProcessingError(f"Failed to run ffmpeg: {exc}") from exc

        if result.returncode != 0:
            logger.error("FFmpeg stderr: %s", result.stderr[-2000:])
            raise VideoProcessingError(
                f"FFmpeg {operation} failed (exit {result.returncode}): "
                f"{result.stderr[-500:]}"
            )
