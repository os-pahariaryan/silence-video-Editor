"""Job lifecycle management and background processing."""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from video_editor.application.remove_silence import RemoveSilenceUseCase
from video_editor.domain.exceptions import JobNotFoundError, JobNotReadyError, VideoEditorError
from video_editor.domain.models import EditConfig, JobStatus, VideoJob
from video_editor.domain.ports import JobRepositoryPort, StoragePort

logger = logging.getLogger(__name__)


class JobService:
    """Creates jobs, runs processing in background, and tracks status."""

    def __init__(
        self,
        repository: JobRepositoryPort,
        storage: StoragePort,
        use_case: RemoveSilenceUseCase,
        executor: ThreadPoolExecutor | None = None,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._use_case = use_case
        self._executor = executor or ThreadPoolExecutor(max_workers=2)

    def create_job(
        self,
        filename: str,
        content: bytes,
        config: EditConfig,
    ) -> VideoJob:
        """Create a new job, persist upload, and return the job."""
        config.validate()

        job = VideoJob(
            config=config,
            original_filename=filename,
            status=JobStatus.QUEUED,
            progress=0,
            stage="queued",
        )

        input_path = self._storage.save_upload(job.id, filename, content)
        job.input_path = input_path
        self._repository.save(job)

        logger.info("Created job %s for file %s", job.id, filename)
        return job

    async def process_job_async(self, job_id: str) -> None:
        """Run job processing in a thread pool without blocking the event loop."""
        job = self._repository.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")

        loop = asyncio.get_event_loop()

        def on_progress(updated_job: VideoJob) -> None:
            self._repository.update(updated_job)

        try:
            output_path = await loop.run_in_executor(
                self._executor,
                lambda: self._use_case.execute(job, on_progress=on_progress),
            )
            job.output_path = output_path
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.stage = "completed"
            self._repository.update(job)
            logger.info("Job %s completed: %s", job_id, output_path)
        except VideoEditorError as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
            job.stage = "failed"
            self._repository.update(job)
            logger.error("Job %s failed: %s", job_id, exc)
        except Exception as exc:
            job.status = JobStatus.FAILED
            job.error = f"Unexpected error: {exc}"
            job.stage = "failed"
            self._repository.update(job)
            logger.exception("Job %s failed unexpectedly", job_id)

    def get_job(self, job_id: str) -> VideoJob:
        """Retrieve a job by ID."""
        job = self._repository.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job

    def get_download_path(self, job_id: str) -> Path:
        """Return output path if job is complete and file exists."""
        job = self.get_job(job_id)
        if not job.download_ready or job.output_path is None:
            raise JobNotReadyError(
                f"Job {job_id} is not ready for download (status={job.status})"
            )
        if not job.output_path.exists():
            raise JobNotReadyError(f"Output file missing for job {job_id}")
        return job.output_path
