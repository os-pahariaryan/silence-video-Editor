"""Job management endpoints."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from video_editor.api.dependencies import get_job_service, get_settings
from video_editor.api.schemas import EditConfigSchema, JobCreateResponse, JobStatusResponse
from video_editor.application.job_service import JobService
from video_editor.config import Settings
from video_editor.domain.exceptions import (
    InvalidConfigError,
    JobNotFoundError,
    JobNotReadyError,
)
from video_editor.domain.models import EditConfig

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/jobs", response_model=JobCreateResponse, status_code=202)
async def create_job(
    file: UploadFile = File(...),
    min_silence_duration: float = Form(1.0),
    silence_threshold_db: float = Form(-35.0),
    padding_before: float = Form(0.1),
    padding_after: float = Form(0.1),
    min_segment_duration: float = Form(0.05),
    job_service: JobService = Depends(get_job_service),
    settings: Settings = Depends(get_settings),
) -> JobCreateResponse:
    """Upload a video and start silence-removal processing."""
    _validate_upload(file, settings)

    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
        )

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        config_schema = EditConfigSchema(
            min_silence_duration=min_silence_duration,
            silence_threshold_db=silence_threshold_db,
            padding_before=padding_before,
            padding_after=padding_after,
            min_segment_duration=min_segment_duration,
        )
        config = EditConfig(**config_schema.model_dump())
        config.validate()
    except (ValueError, InvalidConfigError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename = file.filename or "upload.mp4"
    job = job_service.create_job(filename, content, config)

    asyncio.create_task(job_service.process_job_async(job.id))

    return JobCreateResponse(job_id=job.id, status=job.status.value)


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
) -> JobStatusResponse:
    """Poll job processing status."""
    try:
        job = job_service.get_job(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        progress=job.progress,
        stage=job.stage,
        error=job.error,
        download_ready=job.download_ready,
        original_filename=job.original_filename,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/jobs/{job_id}/download")
async def download_job(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
) -> FileResponse:
    """Download the edited video when processing is complete."""
    try:
        output_path = job_service.get_download_path(job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except JobNotReadyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    stem = Path(job_service.get_job(job_id).original_filename).stem
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=f"{stem}_edited.mp4",
    )


def _validate_upload(file: UploadFile, settings: Settings) -> None:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    ext = Path(file.filename).suffix.lower()
    if ext not in settings.allowed_extension_set:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {settings.allowed_extensions}",
        )
