import os
import redis
from celery import Celery
from src.config import settings

# Determine Redis connection details
redis_host = settings.REDIS_HOST
redis_url = settings.CELERY_BROKER_URL

# Self-healing Redis host fallback for local development outside Docker
if settings.REDIS_HOST == "redis" and not os.path.exists("/.dockerenv"):
    print("Notice: Redis container host 'redis' is configured, but running outside Docker. Falling back to localhost.")
    redis_host = "localhost"
    redis_url = f"redis://localhost:{settings.REDIS_PORT}/0"

# Check if Redis is actually running
redis_offline = False
try:
    r = redis.Redis(host=redis_host, port=settings.REDIS_PORT, socket_timeout=1)
    r.ping()
except Exception as e:
    redis_offline = True
    print(f"Warning: Redis server is offline or unreachable: {e}. Celery tasks will execute synchronously (eager mode).")

celery_app = Celery("ocr_tasks")

# Base configurations
celery_config = {
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "UTC",
    "enable_utc": True,
    "task_track_started": True,
    "task_acks_late": True,
    "worker_prefetch_multiplier": 1
}

if redis_offline:
    # Eager mode: tasks run synchronously in the same process
    celery_config["task_always_eager"] = True
    celery_config["task_eager_propagates"] = True
else:
    celery_config["broker_url"] = redis_url
    celery_config["result_backend"] = redis_url

celery_app.conf.update(celery_config)

# Auto-discover tasks from the queue module
celery_app.autodiscover_tasks(["src.infrastructure.queue"])
