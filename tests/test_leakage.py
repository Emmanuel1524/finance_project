"""Testes de vazamento de dados futuros (docs 05 §11): mutação do futuro, histórico truncado,
reprodutibilidade do sinal e mutação da mesma barra. Cada teste tem um controle negativo."""
import numpy as np
import pandas as pd
import pytest
from helpers import equity_until, events_until, make_bars
from wdo import BaselineV0, Config, WDOReplayEngine, rsi_wilder, validate_bars
import wdo.engine as engine_module


class Spy:
    """Registra tudo que a estratégia enxerga (ponto de decisão) e delega ao V0."""
    name = "spy"

    def __init__(self, config):
        self.inner, self.log = BaselineV0(config), []

    @staticmethod
    def _num(x):
        return None if x is None or (isinstance(x, float) and np.isnan(x)) else x

    def on_session_open(self, ctx):
        self.log.append(("S", pd.Timestamp(ctx.date), ctx.open, ctx.pdh, ctx.pdl, tuple(self._num(e) for e in ctx.emas), self._num(ctx.rsi)))
        return self.inner.on_session_open(ctx)

    def on_bar_open(self, bar):
        prev = None if bar.prev_bar is None else (bar.prev_bar.datetime, bar.prev_bar.high, bar.prev_bar.low, bar.prev_bar.close)
        self.log.append(("B", bar.datetime, bar.open, self._num(bar.rsi), bar.index_in_session, prev))
        return self.inner.on_bar_open(bar)

    def on_bar_close(self, bar, *, entered):
        self.inner.on_bar_close(bar, entered=entered)


def bars_valid():
    return validate_bars(make_bars(days=45, seed=7))


def run(bars, cfg=None):
    cfg = cfg or Config()
    return WDOReplayEngine(cfg).run(bars)


def run_spy(bars, cfg=None):
    cfg = cfg or Config()
    spy = Spy(cfg)
    WDOReplayEngine(cfg, spy).run(bars)
    return spy.log


def view_until(log, t):
    """O que a estratégia viu até o instante t (sessões do dia de t inclusive)."""
    return [row for row in log if (row[0] == "B" and row[1] <= t) or (row[0] == "S" and row[1].date() <= t.date())]


def mutate_after(bars, t, seed=99):
    rng = np.random.RandomState(seed)
    out = bars.copy()
    idx = out.index[out.datetime > t]
    shift = rng.normal(0, 25, len(idx)).round(1)
    for col in ("open", "high", "low", "close"):
        out.loc[idx, col] = (out.loc[idx, col] + shift).round(1)
    out.loc[idx, "high"] = out.loc[idx, ["open", "high", "low", "close"]].max(axis=1) + 0.5
    out.loc[idx, "low"] = out.loc[idx, ["open", "high", "low", "close"]].min(axis=1) - 0.5
    return out


def mutate_same_bar(bars, t, delta=40.0):
    """Altera high/low/close da barra t (mantém o open); a barra continua válida."""
    out = bars.copy()
    i = out.index[out.datetime == t][0]
    out.loc[i, "close"] = out.loc[i, "close"] + delta
    out.loc[i, "high"] = max(out.loc[i, "high"], out.loc[i, "close"]) + 1.0
    out.loc[i, "low"] = min(out.loc[i, "low"], out.loc[i, "close"]) - 1.0
    return out


def probe_times(bars, result):
    """Instantes de teste não triviais: entradas do V0, primeira barra de sessões e meio de sessão."""
    entries = result.events[result.events.event == "ENTRY"].datetime.tolist()
    sessions = result.events[result.events.event == "SESSION"].datetime.tolist()
    return sorted({entries[0], entries[len(entries) // 2], entries[-2], sessions[len(sessions) // 2],
                   sessions[len(sessions) // 2] + pd.Timedelta(minutes=25), sessions[-3]})


def test_the_synthetic_scenario_is_not_vacuous():
    result = run(bars_valid())
    assert (result.events.event == "ENTRY").sum() >= 6 and (result.events.event == "SESSION").sum() >= 15


def test_future_mutation_does_not_change_past_decisions():
    bars = bars_valid()
    base = run(bars)
    for t in probe_times(bars, base):
        mutated = run(mutate_after(bars, t))
        pd.testing.assert_frame_equal(events_until(base, t), events_until(mutated, t))
        pd.testing.assert_frame_equal(equity_until(base, t), equity_until(mutated, t))


def test_truncated_history_matches_the_full_run_up_to_t():
    bars = bars_valid()
    base = run(bars)
    for t in probe_times(bars, base):
        truncated = run(bars[bars.datetime <= t].reset_index(drop=True))
        pd.testing.assert_frame_equal(events_until(base, t), events_until(truncated, t))
        pd.testing.assert_frame_equal(equity_until(base, t), equity_until(truncated, t))


def test_signal_reproducibility_state_and_decision_do_not_depend_on_later_data():
    bars = bars_valid()
    base_log = run_spy(bars)
    base = run(bars)
    for t in probe_times(bars, base):
        assert view_until(base_log, t) == view_until(run_spy(mutate_after(bars, t)), t)
        assert view_until(base_log, t) == view_until(run_spy(bars[bars.datetime <= t].reset_index(drop=True)), t)


def test_same_bar_mutation_does_not_change_what_the_strategy_sees_at_the_open():
    bars = bars_valid()
    base = run(bars)
    base_log = run_spy(bars)
    for t in probe_times(bars, base):
        assert view_until(base_log, t) == view_until(run_spy(mutate_same_bar(bars, t)), t)


def test_same_bar_mutation_does_not_change_market_entries_at_the_open():
    """Entrada a mercado (P4_RSI) é decidida com o IFR conhecido: high/low/close da própria barra não a alteram."""
    bars = bars_valid()
    base = run(bars)
    market = base.trades[base.trades.entry_reason == "P4_RSI"]
    assert len(market) >= 1                                              # o cenário sintético contém entradas a mercado
    for _, trade in market.iterrows():
        t = trade.entry_datetime
        again = run(mutate_same_bar(bars, t)).trades
        same = again[again.entry_datetime == t]
        assert len(same) == 1
        assert (same.iloc[0].side, same.iloc[0].entry_price, same.iloc[0].entry_reason) == (trade.side, trade.entry_price, trade.entry_reason)
        assert trade.entry_price == bars.loc[bars.datetime == t, "open"].iloc[0]          # a mercado = abertura da barra


# ---------------------------------------------------------------- controles negativos: os testes detectam vazamento
def _leaky(kind):
    real = engine_module.add_point_in_time_indicators

    def fn(bars, config):
        data = real(bars, config)
        close = data.set_index("datetime")["close"]
        raw = rsi_wilder(close, config.rsi_period)
        data["rsi"] = (raw if kind == "same_bar" else raw.shift(-1)).to_numpy()   # usa o close da própria barra / da próxima
        return data
    return real, fn


@pytest.mark.parametrize("kind", ["same_bar", "future"])
def test_negative_control_leaky_indicator_is_detected(kind, monkeypatch):
    bars = bars_valid()
    real, leaky = _leaky(kind)
    monkeypatch.setattr(engine_module, "add_point_in_time_indicators", leaky)
    base = run(bars)
    base_log = run_spy(bars)
    detected = False
    for t in probe_times(bars, base):
        mutated = mutate_same_bar(bars, t) if kind == "same_bar" else mutate_after(bars, t)
        if view_until(base_log, t) != view_until(run_spy(mutated), t):
            detected = True
    assert detected, f"o teste de mutação ({kind}) deveria detectar o indicador com vazamento"
