import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.tasks.trade_tasks.record_trade", queue="trading")
def record_trade(trade_id: str):
    logger.info("record_trade called for trade_id=%s", trade_id)
