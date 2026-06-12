"""Domain exceptions for video processing."""


class VideoEditorError(Exception):
    """Base exception for all video editor errors."""


class InvalidConfigError(VideoEditorError):
    """Raised when edit configuration is invalid."""


class VideoProcessingError(VideoEditorError):
    """Raised when video processing fails."""


class JobNotFoundError(VideoEditorError):
    """Raised when a job ID does not exist."""


class JobNotReadyError(VideoEditorError):
    """Raised when a job output is not yet available for download."""
