"""Indicadores point-in-time usados pela estratégia (EMA H1/D1 e IFR/RSI)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config


def rsi_wilder(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff(); gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return 100 - 100 / (1 + avg_gain / avg_loss.replace(0, np.nan))


def add_point_in_time_indicators(bars: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Valores deslocados 1 barra: só informação conhecida na abertura da barra M5."""
    data = bars.copy().set_index("datetime")
    for period in (13, 17, 21):
        h1 = data["close"].resample("1h", label="left", closed="left").last().ewm(span=period, adjust=False, min_periods=period).mean()
        d1 = data["close"].resample("1D", label="left", closed="left").last().ewm(span=period, adjust=False, min_periods=period).mean()
        data[f"ema_h1_{period}"] = h1.reindex(data.index, method="ffill").shift(1)
        data[f"ema_d1_{period}"] = d1.reindex(data.index, method="ffill").shift(1)
    data["rsi"] = rsi_wilder(data.close, config.rsi_period).shift(1)
    return data.reset_index()
