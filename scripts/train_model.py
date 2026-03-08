import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.ai.feature_engineering import FeatureEngineer

FORWARD_BARS = 10
MIN_MOVE_PIPS = 10


def create_labels(df: pd.DataFrame) -> pd.Series:
    future_close = df["close"].shift(-FORWARD_BARS)
    pips = (future_close - df["close"]) / (df["close"].replace(0, np.nan).mean()) * 10000
    labels = pd.Series(0, index=df.index)
    labels[pips > MIN_MOVE_PIPS] = 1
    labels[pips < -MIN_MOVE_PIPS] = 2
    return labels


def train(ohlcv_csv_path: str, symbol: str):
    data_frame = pd.read_csv(ohlcv_csv_path)
    fe = FeatureEngineer()
    rows = []
    labels = create_labels(data_frame)

    for index in range(210, len(data_frame) - FORWARD_BARS):
        features = fe.extract(data_frame.iloc[index - 210 : index])
        rows.append(features.values[0])

    x_data = np.array(rows)
    y_data = labels.iloc[210 : len(data_frame) - FORWARD_BARS].values

    x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, test_size=0.2, shuffle=False)

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    model = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    model.fit(x_train_scaled, y_train)

    score = model.score(x_test_scaled, y_test)
    print(f"Model accuracy: {score:.4f}")

    os.makedirs("app/ai/models", exist_ok=True)
    joblib.dump(model, f"app/ai/models/{symbol}_model.pkl")
    joblib.dump(scaler, f"app/ai/models/{symbol}_scaler.pkl")
    print(f"Model saved for {symbol}")


if __name__ == "__main__":
    train(sys.argv[1], sys.argv[2])
