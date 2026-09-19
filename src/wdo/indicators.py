"""Indicadores point-in-time usados pela estratégia (EMA H1/D1 e IFR/RSI).

Contrato point-in-time: o valor associado a uma barra M5 só usa informação que já
existia na abertura dessa barra (ver docs/agentic_documentation/05 §5).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config


def rsi_wilder(close: pd.Series, period: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return 100 - 100 / (1 + avg_gain / avg_loss.replace(0, np.nan))


def closed_candle_ema(close: pd.Series, rule: str, period: int) -> pd.Series:
    """EMA do último candle **fechado** de `rule` ("1h", "1D"), alinhada às barras M5.

    Correções em relação ao motor v0 (R1):
    - a EMA é calculada só sobre candles existentes (sem os buracos de madrugada/fim de semana,
      que faziam o `ewm` decair pesos e divergirem da EMA do MT5, calculada só sobre barras);
    - o deslocamento de 1 candle é feito no índice do timeframe maior, *antes* de reindexar
      para M5: a barra M5 dentro do candle k enxerga a EMA até o candle k-1 (já fechado).
    """
    candles = close.resample(rule, label="left", closed="left").last().dropna()
    ema = candles.ewm(span=period, adjust=False, min_periods=period).mean()
    return ema.shift(1).reindex(close.index, method="ffill")


def add_point_in_time_indicators(bars: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Adiciona `ema_h1_*`, `ema_d1_*` (candles fechados) e `rsi` (defasado 1 barra M5)."""
    data = bars.copy().set_index("datetime")
    for period in (13, 17, 21):
        data[f"ema_h1_{period}"] = closed_candle_ema(data["close"], "1h", period)
        data[f"ema_d1_{period}"] = closed_candle_ema(data["close"], "1D", period)
    data["rsi"] = rsi_wilder(data["close"], config.rsi_period).shift(1)
    return data.reset_index()
