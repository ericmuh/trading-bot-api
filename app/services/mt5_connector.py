from __future__ import annotations

import random
import socket
import time
from dataclasses import dataclass


@dataclass
class MT5ValidationResult:
    status: str
    provider: str
    latency_ms: int
    message: str


class MT5Connector:
    def __init__(self) -> None:
        try:
            import MetaTrader5 as mt5

            self._mt5 = mt5
            self._provider = "MetaTrader5"
        except Exception:
            self._mt5 = None
            self._provider = "unavailable"

    def validate_credentials(
        self,
        *,
        login: str,
        password: str,
        server: str,
        timeout_ms: int,
    ) -> MT5ValidationResult:
        started = time.perf_counter()

        if self._mt5 is None:
            reachable = self._basic_server_check(server, timeout_ms)
            status = "provider_unavailable"
            message = (
                "MetaTrader5 provider is not available in this runtime"
                if reachable
                else "MetaTrader5 provider unavailable and server is unreachable"
            )
            return MT5ValidationResult(
                status=status,
                provider=self._provider,
                latency_ms=int((time.perf_counter() - started) * 1000),
                message=message,
            )

        mt5 = self._mt5
        attempts = 3
        last_error_code = -1
        last_error_message = "unknown"

        for attempt in range(attempts):
            ok = mt5.initialize(
                login=int(login),
                password=password,
                server=server,
                timeout=timeout_ms,
            )
            if ok:
                mt5.shutdown()
                return MT5ValidationResult(
                    status="validated",
                    provider=self._provider,
                    latency_ms=int((time.perf_counter() - started) * 1000),
                    message="MT5 credentials validated",
                )

            last_error_code, last_error_message = mt5.last_error()
            mt5.shutdown()
            if attempt < attempts - 1:
                base_delay = 0.15 * (2**attempt)
                jitter = random.uniform(0.01, 0.09)
                time.sleep(base_delay + jitter)

        return MT5ValidationResult(
            status="failed",
            provider=self._provider,
            latency_ms=int((time.perf_counter() - started) * 1000),
            message=f"MT5 initialize failed ({last_error_code}): {last_error_message}",
        )

    def _basic_server_check(self, server: str, timeout_ms: int) -> bool:
        host = server.split(":")[0].strip()
        if not host:
            return False
        try:
            socket.setdefaulttimeout(timeout_ms / 1000)
            socket.gethostbyname(host)
            return True
        except Exception:
            return False
