import pytest

from app.trading.risk_manager import RiskBreachError, RiskManager
from app.trading.strategies.base import Action, TradeDecision


@pytest.mark.asyncio
async def test_hold_always_passes():
    manager = RiskManager({"lot_size": 0.01, "max_trades": 1, "max_drawdown_pct": 5})
    await manager.validate(
        TradeDecision(Action.HOLD, 0.01, 0, 0),
        open_trade_count=999,
        account_info={"equity": 0, "free_margin": 0},
        day_start_balance=1,
    )


@pytest.mark.asyncio
async def test_max_trades_breach():
    manager = RiskManager({"lot_size": 0.01, "max_trades": 1, "max_drawdown_pct": 5})
    with pytest.raises(RiskBreachError) as error:
        await manager.validate(
            TradeDecision(Action.BUY, 0.01, 10, 20),
            open_trade_count=1,
            account_info={"equity": 1000, "free_margin": 1000},
            day_start_balance=1000,
        )
    assert error.value.code == "MAX_TRADES"


@pytest.mark.asyncio
async def test_stop_loss_required_breach():
    manager = RiskManager({"lot_size": 0.01, "max_trades": 3, "max_drawdown_pct": 5})
    with pytest.raises(RiskBreachError) as error:
        await manager.validate(
            TradeDecision(Action.BUY, 0.01, 0, 20),
            open_trade_count=0,
            account_info={"equity": 1000, "free_margin": 1000},
            day_start_balance=1000,
        )
    assert error.value.code == "NO_STOP_LOSS"
