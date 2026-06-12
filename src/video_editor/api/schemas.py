"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EditConfigSchema(BaseModel):
    min_silence_duration: float = Field(default=1.0, gt=0, description="Minimum silence length to cut (seconds)")
    silence_threshold_db: float = Field(default=-35.0, lt=0, description="dB threshold for silence detection")
    padding_before: float = Field(default=0.1, ge=0, description="Audio padding before speech resumes (seconds)")
    padding_after: float = Field(default=0.1, ge=0, description="Audio padding after speech ends (seconds)")
    min_segment_duration: float = Field(default=0.05, gt=0, description="Drop segments shorter than this (seconds)")


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int
    stage: str
    error: str | None = None
    download_ready: bool
    original_filename: str
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    ffmpeg_available: bool
    version: str
