"""Local filesystem storage for job workspaces."""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path

from video_editor.domain.exceptions import VideoProcessingError

logger = logging.getLogger(__name__)

_SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]")


class LocalFileStorage:
    """Manages per-job directories on the local filesystem."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._jobs_dir = data_dir / "jobs"
        self._jobs_dir.mkdir(parents=True, exist_ok=True)

    def create_job_workspace(self, job_id: str) -> Path:
        workspace = self._jobs_dir / job_id
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def save_upload(self, job_id: str, filename: str, content: bytes) -> Path:
        workspace = self.create_job_workspace(job_id)
        safe_name = _sanitize_filename(filename)
        dest = workspace / f"input{Path(safe_name).suffix.lower()}"
        dest.write_bytes(content)
        logger.info("Saved upload for job %s to %s", job_id, dest)
        return dest

    def get_output_path(self, job_id: str) -> Path:
        return self._jobs_dir / job_id / "output.mp4"

    def cleanup_job(self, job_id: str) -> None:
        workspace = self._jobs_dir / job_id
        if workspace.exists():
            shutil.rmtree(workspace)
            logger.info("Cleaned up workspace for job %s", job_id)


def _sanitize_filename(filename: str) -> str:
    """Strip path components and unsafe characters from a filename."""
    name = Path(filename).name
    if not name or name in (".", ".."):
        raise VideoProcessingError("Invalid filename")
    return _SAFE_FILENAME_RE.sub("_", name)
