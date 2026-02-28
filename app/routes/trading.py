from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Header

from app.db import store
from app.schemas.trading import (
    AIEvaluateRequest,
    AIEvaluateResponse,
    BotStatusResponse,
    TickRequest,
    TickResponse,
    TradingConfigResponse,
    TradingConfigUpsertRequest,
)
from app.services.ai_filter import AIFilterService
from app.services.latency_metrics import latency_metrics
from app.services.notification_service import NotificationService
from app.services.trading_engine import TradingEngine

router = APIRouter(tags=["trading"])
engine = TradingEngine()
ai_filter = AIFilterService()
notifier = NotificationService()


@router.put("/trading/config", response_model=TradingConfigResponse)
def upsert_trading_config(payload: TradingConfigUpsertRequest) -> TradingConfigResponse:
    store.upsert_trading_config(
        user_id=payload.user_id,
        assets=payload.assets,
        timeframe=payload.timeframe,
        max_trades_per_session=payload.max_trades_per_session,
        quantity=payload.quantity,
        profit_threshold=payload.profit_threshold,
        loss_threshold=payload.loss_threshold,
    )

    config = store.get_trading_config(payload.user_id)
    if config is None:
        raise HTTPException(status_code=500, detail="Failed to persist trading config")

    return TradingConfigResponse(
        user_id=config["user_id"],
        assets=[item for item in config["assets"].split(",") if item],
        timeframe=config["timeframe"],
        max_trades_per_session=int(config["max_trades_per_session"]),
        quantity=float(config["quantity"]),
        profit_threshold=float(config["profit_threshold"]),
        loss_threshold=float(config["loss_threshold"]),
        updated_at=config["updated_at"],
    )


@router.get("/trading/config", response_model=TradingConfigResponse)
def get_trading_config(user_id: str) -> TradingConfigResponse:
    config = store.get_trading_config(user_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Trading config not found")

    return TradingConfigResponse(
        user_id=config["user_id"],
        assets=[item for item in config["assets"].split(",") if item],
        timeframe=config["timeframe"],
        max_trades_per_session=int(config["max_trades_per_session"]),
        quantity=float(config["quantity"]),
        profit_threshold=float(config["profit_threshold"]),
        loss_threshold=float(config["loss_threshold"]),
        updated_at=config["updated_at"],
    )


@router.post("/bot/start", response_model=BotStatusResponse)
def start_bot(user_id: str) -> BotStatusResponse:
    valid_license, license_message = store.is_license_valid_for_user(user_id)
    if not valid_license:
        raise HTTPException(status_code=403, detail=f"License validation failed: {license_message}")

    if store.get_trading_config(user_id) is None:
        raise HTTPException(status_code=400, detail="Trading config required before bot start")
    if store.get_risk_config(user_id) is None:
        raise HTTPException(status_code=400, detail="Risk config required before bot start")
    if store.get_session_config(user_id) is None:
        raise HTTPException(status_code=400, detail="Session config required before bot start")

    started_at = datetime.now(timezone.utc).isoformat()
    store.set_bot_session(
        user_id=user_id,
        is_running=True,
        started_at=started_at,
        trades_opened_this_session=0,
    )
    return BotStatusResponse(
        user_id=user_id,
        running=True,
        started_at=started_at,
        trades_opened_this_session=0,
        stop_reason=None,
    )


@router.post("/bot/stop", response_model=BotStatusResponse)
def stop_bot(user_id: str) -> BotStatusResponse:
    session = store.get_bot_session(user_id)
    trades_opened = int(session["trades_opened_this_session"]) if session else 0
    started_at = session["started_at"] if session else None

    store.set_bot_session(
        user_id=user_id,
        is_running=False,
        started_at=started_at,
        trades_opened_this_session=trades_opened,
    )
    notifier.publish(
        user_id=user_id,
        event_type="bot_stopped",
        title="Bot stopped",
        message="Bot stopped manually by user",
    )
    return BotStatusResponse(
        user_id=user_id,
        running=False,
        started_at=started_at,
        trades_opened_this_session=trades_opened,
        stop_reason="manual_stop",
    )


@router.get("/bot/status", response_model=BotStatusResponse)
def bot_status(user_id: str) -> BotStatusResponse:
    session = store.get_bot_session(user_id)
    if session is None:
        return BotStatusResponse(user_id=user_id, running=False)

    stop_reason = None
    if not bool(session["is_running"]):
        stop_reason = "stopped"

    return BotStatusResponse(
        user_id=user_id,
        running=bool(session["is_running"]),
        started_at=session["started_at"],
        trades_opened_this_session=int(session["trades_opened_this_session"]),
        stop_reason=stop_reason,
    )


@router.post("/engine/tick", response_model=TickResponse)
def ingest_tick(payload: TickRequest, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> TickResponse:
    route_started = time.perf_counter()
    if idempotency_key:
        cached = store.get_idempotent_response(
            idempotency_key=idempotency_key,
            endpoint="/engine/tick",
        )
        if cached is not None:
            return TickResponse(**cached)

    ai_started = time.perf_counter()
    ai_decision = ai_filter.evaluate(
        user_id=payload.user_id,
        symbol=payload.symbol,
        price=payload.price,
        news_spike=payload.news_spike,
        confidence_threshold=payload.confidence_threshold,
    )
    latency_metrics.record("ai_decision_ms", (time.perf_counter() - ai_started) * 1000)
    store.create_ai_decision(
        user_id=payload.user_id,
        symbol=payload.symbol,
        price=payload.price,
        approved=ai_decision.approved,
        confidence=ai_decision.confidence,
        reasons=ai_decision.reasons,
        trend_strength=ai_decision.trend_strength,
        volatility=ai_decision.volatility,
    )

    decision = engine.process_tick(
        user_id=payload.user_id,
        symbol=payload.symbol,
        price=payload.price,
        ai_approved=ai_decision.approved,
    )

    if decision.action == "opened":
        notifier.publish(
            user_id=payload.user_id,
            event_type="trade_opened",
            title="Trade opened",
            message=f"{decision.symbol} {decision.side} opened at {decision.entry_price}",
        )
    if decision.action == "closed":
        notifier.publish(
            user_id=payload.user_id,
            event_type="trade_closed",
            title="Trade closed",
            message=f"{decision.symbol} {decision.side} closed at {decision.close_price}, pnl={decision.pnl}",
        )

    if decision.message == "Bot stopped: daily profit target reached":
        notifier.publish(
            user_id=payload.user_id,
            event_type="profit_target_hit",
            title="Daily profit target reached",
            message="Bot stopped after reaching daily profit target",
        )
        notifier.publish(
            user_id=payload.user_id,
            event_type="bot_stopped",
            title="Bot stopped",
            message="Bot stopped due to daily profit target",
        )

    if decision.message == "Bot stopped: daily loss limit reached":
        notifier.publish(
            user_id=payload.user_id,
            event_type="loss_limit_hit",
            title="Daily loss limit reached",
            message="Bot stopped after hitting daily loss limit",
        )
        notifier.publish(
            user_id=payload.user_id,
            event_type="bot_stopped",
            title="Bot stopped",
            message="Bot stopped due to daily loss limit",
        )

    if decision.message == "Bot stopped: session duration expired":
        notifier.publish(
            user_id=payload.user_id,
            event_type="bot_stopped",
            title="Bot stopped",
            message="Bot stopped because session duration expired",
        )

    response_payload = {
        "action": decision.action,
        "message": decision.message,
        "symbol": decision.symbol,
        "ai_approved": ai_decision.approved,
        "ai_confidence": ai_decision.confidence,
        "ai_reasons": ai_decision.reasons,
        "side": decision.side,
        "pnl": decision.pnl,
        "entry_price": decision.entry_price,
        "close_price": decision.close_price,
    }

    if idempotency_key:
        store.save_idempotent_response(
            idempotency_key=idempotency_key,
            endpoint="/engine/tick",
            response=response_payload,
        )

    latency_metrics.record("trade_execution_ms", (time.perf_counter() - route_started) * 1000)

    return TickResponse(
        action=decision.action,
        message=decision.message,
        symbol=decision.symbol,
        ai_approved=ai_decision.approved,
        ai_confidence=ai_decision.confidence,
        ai_reasons=ai_decision.reasons,
        side=decision.side,
        pnl=decision.pnl,
        entry_price=decision.entry_price,
        close_price=decision.close_price,
    )


@router.post("/ai/evaluate", response_model=AIEvaluateResponse)
def evaluate_ai(payload: AIEvaluateRequest) -> AIEvaluateResponse:
    started = time.perf_counter()
    decision = ai_filter.evaluate(
        user_id=payload.user_id,
        symbol=payload.symbol,
        price=payload.price,
        news_spike=payload.news_spike,
        confidence_threshold=payload.confidence_threshold,
    )
    latency_metrics.record("ai_evaluate_route_ms", (time.perf_counter() - started) * 1000)
    store.create_ai_decision(
        user_id=payload.user_id,
        symbol=payload.symbol,
        price=payload.price,
        approved=decision.approved,
        confidence=decision.confidence,
        reasons=decision.reasons,
        trend_strength=decision.trend_strength,
        volatility=decision.volatility,
    )
    return AIEvaluateResponse(
        approved=decision.approved,
        confidence=decision.confidence,
        reasons=decision.reasons,
        trend_strength=decision.trend_strength,
        volatility=decision.volatility,
    )
