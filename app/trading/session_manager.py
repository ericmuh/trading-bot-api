import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import pandas as pd

from app.core.redis import acquire_lock, get_redis, release_lock
from app.core.security import decrypt_credential

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover
    mt5 = None

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class MT5AccountConfig:
    account_id: str
    login: int
    password_enc: bytes
    server: str


class MT5ConnectionError(Exception):
    pass


class MT5DataError(Exception):
    pass


class MT5Session:
    MAX_RETRIES = 5
    BACKOFF_BASE = 2

    def __init__(self, config: MT5AccountConfig):
        self.config = config
        self.state = SessionState.DISCONNECTED
        self._lock = asyncio.Lock()

    async def connect(self) -> bool:
        if mt5 is None:
            self.state = SessionState.FAILED
            return False

        async with self._lock:
            self.state = SessionState.CONNECTING
            password = decrypt_credential(self.config.password_enc)
            loop = asyncio.get_event_loop()
            connected = await loop.run_in_executor(None, self._mt5_login, password)
            if connected:
                self.state = SessionState.CONNECTED
                logger.info("MT5 connected: account=%s", self.config.account_id)
                return True
            self.state = SessionState.FAILED
            return False

    def _mt5_login(self, password: str) -> bool:
        if mt5 is None:
            return False
        if not mt5.initialize():
            return False
        return bool(mt5.login(self.config.login, password=password, server=self.config.server))

    async def disconnect(self):
        if mt5 is not None:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, mt5.shutdown)
        self.state = SessionState.DISCONNECTED
        logger.info("MT5 disconnected: account=%s", self.config.account_id)

    async def reconnect(self):
        self.state = SessionState.RECONNECTING
        for attempt in range(self.MAX_RETRIES):
            wait = self.BACKOFF_BASE**attempt
            await asyncio.sleep(wait)
            if await self.connect():
                return
        self.state = SessionState.FAILED
        raise MT5ConnectionError(f"Max retries exceeded for account {self.config.account_id}")

    async def get_tick(self, symbol: str) -> dict[str, Any] | None:
        if not self.is_connected:
            raise MT5ConnectionError("Session is not connected")
        if mt5 is None:
            return None
        loop = asyncio.get_event_loop()
        tick = await loop.run_in_executor(None, mt5.symbol_info_tick, symbol)
        if tick is None:
            return None
        return {"bid": tick.bid, "ask": tick.ask, "time": tick.time, "symbol": symbol}

    async def get_ohlcv(self, symbol: str, timeframe: str, count: int = 200) -> pd.DataFrame:
        if not self.is_connected:
            raise MT5ConnectionError("Session is not connected")
        if mt5 is None:
            raise MT5DataError("MetaTrader5 module unavailable")

        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
        loop = asyncio.get_event_loop()
        rates = await loop.run_in_executor(None, mt5.copy_rates_from_pos, symbol, tf, 0, count)
        if rates is None:
            raise MT5DataError(f"No OHLCV data for {symbol}/{timeframe}")
        data_frame = pd.DataFrame(rates)
        data_frame["time"] = pd.to_datetime(data_frame["time"], unit="s")
        data_frame.attrs["symbol"] = symbol
        return data_frame

    async def get_account_info(self) -> dict[str, Any]:
        if not self.is_connected:
            raise MT5ConnectionError("Session is not connected")
        if mt5 is None:
            raise MT5ConnectionError("MetaTrader5 module unavailable")
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, mt5.account_info)
        if info is None:
            raise MT5ConnectionError("Cannot get account info")
        return {
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "leverage": info.leverage,
            "currency": info.currency,
        }

    async def get_positions(self) -> list[dict[str, Any]]:
        if not self.is_connected:
            raise MT5ConnectionError("Session is not connected")
        if mt5 is None:
            return []
        loop = asyncio.get_event_loop()
        positions = await loop.run_in_executor(None, mt5.positions_get)
        if positions is None:
            return []
        return [
            {
                "ticket": position.ticket,
                "symbol": position.symbol,
                "type": "BUY" if position.type == 0 else "SELL",
                "volume": position.volume,
                "open_price": position.price_open,
                "sl": position.sl,
                "tp": position.tp,
                "profit": position.profit,
            }
            for position in positions
        ]

    async def start_heartbeat(self):
        while self.is_connected:
            redis = await get_redis()
            await redis.setex(f"mt5:heartbeat:{self.config.account_id}", 30, "alive")
            await asyncio.sleep(10)

    @property
    def is_connected(self) -> bool:
        return self.state == SessionState.CONNECTED


class MT5SessionRegistry:
    TTL = 3600

    @staticmethod
    async def register(account_id: str, metadata: dict):
        redis = await get_redis()
        await redis.setex(f"mt5:session:{account_id}", MT5SessionRegistry.TTL, json.dumps(metadata))

    @staticmethod
    async def is_active(account_id: str) -> bool:
        redis = await get_redis()
        return bool(await redis.exists(f"mt5:session:{account_id}"))

    @staticmethod
    async def deregister(account_id: str):
        redis = await get_redis()
        await redis.delete(f"mt5:session:{account_id}")

    @staticmethod
    async def refresh_ttl(account_id: str):
        redis = await get_redis()
        await redis.expire(f"mt5:session:{account_id}", MT5SessionRegistry.TTL)


class MT5SessionPool:
    def __init__(self):
        self._sessions: dict[str, MT5Session] = {}
        self._acquiring: dict[str, asyncio.Lock] = {}

    async def acquire(self, account_id: str, config: MT5AccountConfig) -> MT5Session:
        if account_id not in self._acquiring:
            self._acquiring[account_id] = asyncio.Lock()

        async with self._acquiring[account_id]:
            if account_id in self._sessions and self._sessions[account_id].is_connected:
                await MT5SessionRegistry.refresh_ttl(account_id)
                return self._sessions[account_id]

            for _ in range(10):
                acquired = await acquire_lock(f"mt5:session:lock:{account_id}", ttl_seconds=30)
                if acquired:
                    break
                await asyncio.sleep(0.1)
            else:
                raise RuntimeError(f"Could not acquire session lock for account {account_id}")

            try:
                session = MT5Session(config)
                if not await session.connect():
                    raise MT5ConnectionError(f"Failed to connect account {account_id}")
                self._sessions[account_id] = session
                await MT5SessionRegistry.register(
                    account_id,
                    {"account_id": account_id, "connected_at": datetime.now(timezone.utc).isoformat()},
                )
                return session
            finally:
                await release_lock(f"mt5:session:lock:{account_id}")

    async def release(self, account_id: str):
        session = self._sessions.pop(account_id, None)
        if session:
            await session.disconnect()
        await MT5SessionRegistry.deregister(account_id)

    async def get(self, account_id: str) -> MT5Session | None:
        return self._sessions.get(account_id)


session_pool = MT5SessionPool()
