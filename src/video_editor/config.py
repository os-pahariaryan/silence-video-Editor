"""Application settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    data_dir: Path = Path("./data")
    max_upload_size_mb: int = 500
    job_ttl_hours: int = 24
    allowed_extensions: str = ".mp4,.webm,.mov,.mkv"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_extension_set(self) -> set[str]:
        return {ext.strip().lower() for ext in self.allowed_extensions.split(",")}
