FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml .
COPY src/ src/
COPY static/ static/

RUN pip install --no-cache-dir -e .

ENV DATA_DIR=/app/data
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "video_editor.main:app", "--host", "0.0.0.0", "--port", "8000"]
