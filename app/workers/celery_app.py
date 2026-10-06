from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "clauseguard",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks.ingest"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_pool="solo",
)
