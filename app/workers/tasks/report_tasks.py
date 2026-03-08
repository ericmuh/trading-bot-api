import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.report_tasks.generate_daily_reports", queue="admin")
def generate_daily_reports():
    logger.info("generate_daily_reports running")
