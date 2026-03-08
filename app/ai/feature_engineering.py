import pandas as pd


class FeatureEngineer:
    REQUIRED_ROWS = 210

    def extract(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        if len(ohlcv) < self.REQUIRED_ROWS:
            raise ValueError(f"Need {self.REQUIRED_ROWS} rows, got {len(ohlcv)}")

        df = ohlcv.copy()
        df.columns = [column.lower() for column in df.columns]

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df.get("tick_volume", df.get("volume", pd.Series([1] * len(df))))

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 1e-9)
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        low_14 = low.rolling(14).min()
        high_14 = high.rolling(14).max()
        stoch_k = ((close - low_14) / (high_14 - low_14 + 1e-9)) * 100
        df["stoch_k"] = stoch_k
        df["stoch_d"] = stoch_k.rolling(3).mean()

        df["ema_20"] = close.ewm(span=20, adjust=False).mean()
        df["ema_50"] = close.ewm(span=50, adjust=False).mean()
        df["ema_200"] = close.ewm(span=200, adjust=False).mean()

        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd = ema_12 - ema_26
        signal = macd.ewm(span=9, adjust=False).mean()
        df["macd"] = macd
        df["macd_signal"] = signal
        df["macd_hist"] = macd - signal

        tr = pd.concat(
            [
                (high - low),
                (high - close.shift()).abs(),
                (low - close.shift()).abs(),
            ],
            axis=1,
        ).max(axis=1)
        df["atr"] = tr.rolling(14).mean()

        rolling_up = high.diff().clip(lower=0).rolling(14).mean()
        rolling_down = (-low.diff().clip(upper=0)).rolling(14).mean()
        dx = (rolling_up - rolling_down).abs() / (rolling_up + rolling_down + 1e-9) * 100
        df["adx"] = dx.rolling(14).mean()

        mid = close.rolling(20).mean()
        std = close.rolling(20).std().fillna(0)
        df["bb_upper"] = mid + 2 * std
        df["bb_lower"] = mid - 2 * std
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / (close.abs() + 1e-9)

        body = (close - df["open"]).abs()
        df["body"] = body / (df["atr"] + 1e-9)
        df["upper_wick"] = (high - pd.concat([close, df["open"]], axis=1).max(axis=1)) / (df["atr"] + 1e-9)
        df["lower_wick"] = (pd.concat([close, df["open"]], axis=1).min(axis=1) - low) / (df["atr"] + 1e-9)

        df["ema_aligned_bull"] = ((df["ema_20"] > df["ema_50"]) & (df["ema_50"] > df["ema_200"])).astype(int)
        df["ema_aligned_bear"] = ((df["ema_20"] < df["ema_50"]) & (df["ema_50"] < df["ema_200"])).astype(int)

        latest = df.iloc[-1][self.feature_columns()].fillna(0)
        output = latest.to_frame().T
        output.attrs["symbol"] = ohlcv.attrs.get("symbol", "EURUSD")
        output.attrs["atr"] = float(df["atr"].iloc[-1]) if not pd.isna(df["atr"].iloc[-1]) else 10.0
        return output

    def feature_columns(self) -> list[str]:
        return [
            "rsi",
            "stoch_k",
            "stoch_d",
            "ema_20",
            "ema_50",
            "ema_200",
            "macd",
            "macd_signal",
            "macd_hist",
            "adx",
            "atr",
            "bb_upper",
            "bb_lower",
            "bb_width",
            "body",
            "upper_wick",
            "lower_wick",
            "ema_aligned_bull",
            "ema_aligned_bear",
        ]
