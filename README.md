# AI Video Editor — Silence Removal

A web application that removes long silent periods from videos using FFmpeg silence detection. Upload a video, configure silence parameters, and download the edited result.

## Features

- **Web UI** — drag-and-drop upload with configurable settings
- **Silence detection** — FFmpeg `silencedetect` filter with user-defined threshold and minimum duration
- **Smart cutting** — preserves padding around speech boundaries to avoid abrupt cuts
- **Background processing** — non-blocking job queue with status polling
- **Clean Architecture** — domain-driven design with swappable infrastructure adapters

## Requirements

- Python 3.11+
- FFmpeg and FFprobe on `PATH`

```bash
# Fedora
sudo dnf install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

## Quick Start

```bash
# Clone and enter project
cd Video_Editor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment config (optional)
cp .env.example .env

# Run the server
uvicorn video_editor.main:app --reload --host 0.0.0.0 --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Docker

```bash
docker compose up --build
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server port |
| `DATA_DIR` | `./data` | Job storage directory |
| `MAX_UPLOAD_SIZE_MB` | `500` | Maximum upload size |
| `ALLOWED_EXTENSIONS` | `.mp4,.webm,.mov,.mkv` | Permitted file types |

## API

### Create job

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -F "file=@video.mp4" \
  -F "min_silence_duration=1.0" \
  -F "silence_threshold_db=-35" \
  -F "padding_before=0.1" \
  -F "padding_after=0.1" \
  -F "min_segment_duration=0.05"
```

### Poll status

```bash
curl http://localhost:8000/api/v1/jobs/{job_id}
```

### Download result

```bash
curl -O -J http://localhost:8000/api/v1/jobs/{job_id}/download
```

### Health check

```bash
curl http://localhost:8000/api/v1/health
```

## Silence Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_silence_duration` | `1.0` s | Silence longer than this is removed |
| `silence_threshold_db` | `-35` dB | Audio below this level counts as silence |
| `padding_before` | `0.1` s | Brief audio kept before speech resumes |
| `padding_after` | `0.1` s | Brief audio kept after speech ends |
| `min_segment_duration` | `0.05` s | Fragments shorter than this are dropped |

## Architecture

```
Presentation  →  FastAPI routes + static web UI
Application   →  RemoveSilenceUseCase, JobService
Domain        →  Models, ports, segment logic
Infrastructure → FFmpeg adapters, local storage
```

## Testing

```bash
pytest
```

## Project Structure

```
src/video_editor/
├── domain/          # Models, ports, exceptions
├── application/     # Use cases and job orchestration
├── infrastructure/  # FFmpeg, storage, repository
├── api/             # FastAPI routes and schemas
└── main.py          # App entry point
static/              # Web UI
tests/               # Unit tests
```

## License

MIT
