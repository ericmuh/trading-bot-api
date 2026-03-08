import pytest

from app.trading.strategies import get_strategy
from app.trading.strategies.base import BaseStrategy


def test_get_known_strategy_returns_instance():
    strategy = get_strategy("ScalpingStrategy", {})
    assert isinstance(strategy, BaseStrategy)


def test_get_unknown_strategy_raises():
    with pytest.raises(ValueError):
        get_strategy("UnknownStrategy", {})
