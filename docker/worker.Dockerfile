FROM python:3.12-slim

# Install system dependencies for OpenCV and PDF rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run Celery worker
CMD ["celery", "-A", "src.infrastructure.queue.celery_app", "worker", "--loglevel=info"]
