from celery.schedules import crontab

from app.workers.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "check-bot-heartbeats": {
        "task": "app.workers.tasks.bot_tasks.check_bot_heartbeats",
        "schedule": 30.0,
        "options": {"queue": "admin"},
    },
    "sync-account-balances": {
        "task": "app.workers.tasks.bot_tasks.sync_account_balances",
        "schedule": 60.0,
        "options": {"queue": "admin"},
    },
    "generate-daily-reports": {
        "task": "app.workers.tasks.report_tasks.generate_daily_reports",
        "schedule": crontab(hour=0, minute=0),
        "options": {"queue": "admin"},
    },
}
