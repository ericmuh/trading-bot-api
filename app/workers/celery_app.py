from celery import Celery

from app.config import settings

celery_app = Celery(
    "trading_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.bot_tasks",
        "app.workers.tasks.trade_tasks",
        "app.workers.tasks.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.bot_tasks.*": {"queue": "trading"},
        "app.workers.tasks.trade_tasks.*": {"queue": "trading"},
        "app.workers.tasks.report_tasks.*": {"queue": "admin"},
    },
    task_queue_max_priority=10,
    task_default_priority=5,
)

celery_app.conf.beat_schedule = {}
