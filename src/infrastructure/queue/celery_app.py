from celery import Celery
from src.config import settings

celery_app = Celery(
    "ocr_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Dead Letter Queue / Retry options can be configured here
    task_acks_late=True,
    worker_prefetch_multiplier=1
)

# Auto-discover tasks from the queue module
celery_app.autodiscover_tasks(["src.infrastructure.queue"])
