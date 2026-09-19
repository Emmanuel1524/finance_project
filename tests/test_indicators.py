"""Indicadores point-in-time (docs 05 §5): EMA de candle fechado, IFR defasado, mutação do futuro."""
import numpy as np
import pandas as pd
from helpers import make_bars
from wdo import Config, add_point_in_time_indicators, closed_candle_ema, rsi_wilder, validate_bars


def legacy_indicators(bars, config):
    """Implementação do motor v0 (R1), mantida aqui só como controle negativo dos testes."""
    data = bars.copy().set_index("datetime")
    for period in (13, 17, 21):
        h1 = data["close"].resample("1h", label="left", closed="left").last().ewm(span=period, adjust=False, min_periods=period).mean()
        d1 = data["close"].resample("1D", label="left", closed="left").last().ewm(span=period, adjust=False, min_periods=period).mean()
        data[f"ema_h1_{period}"] = h1.reindex(data.index, method="ffill").shift(1)
        data[f"ema_d1_{period}"] = d1.reindex(data.index, method="ffill").shift(1)
    data["rsi"] = rsi_wilder(data.close, config.rsi_period).shift(1)
    return data.reset_index()


def valid(days=40, seed=3):
    return validate_bars(make_bars(days=days, seed=seed))


def test_daily_ema_is_the_ema_of_previous_closed_days_over_existing_days_only():
    bars = valid()
    close = bars.set_index("datetime")["close"]
    daily_close = close.groupby(close.index.date).last()                       # só pregões existentes (sem fins de semana)
    manual = daily_close.ewm(span=13, adjust=False, min_periods=13).mean()
    got = closed_candle_ema(close, "1D", 13)
    checked = 0
    for k, day in enumerate(daily_close.index):
        if k < 14:
            continue
        expected = manual.iloc[k - 1]                                          # EMA até o pregão anterior (fechado)
        values = got[got.index.date == day]
        assert np.allclose(values.to_numpy(), expected), f"dia {day}: EMA deve ser constante e igual à do pregão anterior"
        checked += 1
    assert checked > 10


def test_hourly_ema_is_the_ema_of_previous_closed_hours():
    bars = valid(days=12)
    close = bars.set_index("datetime")["close"]
    hourly = close.resample("1h", label="left", closed="left").last().dropna()
    manual = hourly.ewm(span=13, adjust=False, min_periods=13).mean()
    got = closed_candle_ema(close, "1h", 13)
    for k in range(14, len(hourly), 7):
        hour = hourly.index[k]
        in_hour = got[(got.index >= hour) & (got.index < hour + pd.Timedelta(hours=1))]
        assert np.allclose(in_hour.to_numpy(), manual.iloc[k - 1])


def test_rsi_column_is_the_rsi_through_the_previous_bar():
    bars = valid(days=10)
    data = add_point_in_time_indicators(bars, Config())
    raw = rsi_wilder(bars["close"], Config().rsi_period)
    assert np.allclose(data["rsi"].iloc[10:].to_numpy(), raw.shift(1).iloc[10:].to_numpy(), equal_nan=True)


def _mutate_after(bars: pd.DataFrame, t: pd.Timestamp, seed: int = 99) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    out = bars.copy()
    idx = out.index[out.datetime > t]
    shift = rng.normal(0, 30, len(idx)).round(1)
    for col in ("open", "high", "low", "close"):
        out.loc[idx, col] = (out.loc[idx, col] + shift).round(1)
    out.loc[idx, "high"] = out.loc[idx, ["open", "high", "low", "close"]].max(axis=1) + 0.5
    out.loc[idx, "low"] = out.loc[idx, ["open", "high", "low", "close"]].min(axis=1) - 0.5
    return out


def _indicator_cols(frame):
    return [c for c in frame.columns if c.startswith("ema_") or c == "rsi"]


def _future_dependent(fn, bars, t):
    base, mutated = fn(bars, Config()), fn(_mutate_after(bars, t), Config())
    cols = _indicator_cols(base)
    before = base.datetime <= t
    return not np.allclose(base.loc[before, cols].to_numpy(dtype=float), mutated.loc[before, cols].to_numpy(dtype=float), equal_nan=True)


def test_indicators_do_not_change_when_future_bars_are_mutated():
    bars = valid()
    for offset in (600, 800, 1000, 1500):                                      # T no meio de horas e de dias
        t = bars.datetime.iloc[offset] + pd.Timedelta(minutes=10)
        assert not _future_dependent(add_point_in_time_indicators, bars, t)


def test_negative_control_the_legacy_ema_did_leak_the_future():
    """O teste acima precisa ser capaz de falhar: o cálculo antigo (R1) depende de barras futuras."""
    bars = valid()
    t = bars.datetime.iloc[800] + pd.Timedelta(minutes=10)
    assert _future_dependent(legacy_indicators, bars, t)


def test_indicators_on_truncated_history_match_the_full_run():
    bars = valid()
    full = add_point_in_time_indicators(bars, Config())
    for offset in (700, 1200):
        t = bars.datetime.iloc[offset]
        part = add_point_in_time_indicators(bars[bars.datetime <= t].reset_index(drop=True), Config())
        cols = _indicator_cols(part)
        assert np.allclose(part[cols].to_numpy(dtype=float), full.loc[full.datetime <= t, cols].to_numpy(dtype=float), equal_nan=True)
