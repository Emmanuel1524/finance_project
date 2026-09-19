"""Testes de vazamento (docs 05 §11) aplicados aos candidatos da pesquisa: mutação do futuro, histórico
truncado e mutação da mesma barra, sobre o que a estratégia enxerga e sobre os eventos do replay."""
import pandas as pd
import pytest
from helpers import equity_until, events_until
from test_leakage import bars_valid, mutate_after, mutate_same_bar, probe_times, view_until
from wdo import Config, WDOReplayEngine
from wdo.strategies import OpeningMomentum, V0NoChannel, V0NoChannelVolGate, V0TrendAligned, V0VolGate

FACTORIES = {"volgate": V0VolGate, "opening_momentum": OpeningMomentum, "trend_aligned": V0TrendAligned, "no_channel": V0NoChannel, "no_channel_volgate": V0NoChannelVolGate}


class GenericSpy:
    def __init__(self, inner):
        self.inner, self.log, self.name = inner, [], "spy"

    @staticmethod
    def _num(x):
        return None if x is None or (isinstance(x, float) and x != x) else x

    def on_session_open(self, ctx):
        self.log.append(("S", pd.Timestamp(ctx.date), ctx.open, ctx.pdh, ctx.pdl, tuple(self._num(e) for e in ctx.emas), self._num(ctx.rsi)))
        return self.inner.on_session_open(ctx)

    def on_bar_open(self, bar):
        prev = None if bar.prev_bar is None else (bar.prev_bar.datetime, bar.prev_bar.high, bar.prev_bar.low, bar.prev_bar.close)
        self.log.append(("B", bar.datetime, bar.open, self._num(bar.rsi), bar.index_in_session, prev))
        return self.inner.on_bar_open(bar)

    def on_bar_close(self, bar, *, entered):
        self.inner.on_bar_close(bar, entered=entered)


def run(factory, bars):
    cfg = Config()
    return WDOReplayEngine(cfg, factory(cfg)).run(bars)


def run_spy(factory, bars):
    cfg = Config()
    spy = GenericSpy(factory(cfg))
    WDOReplayEngine(cfg, spy).run(bars)
    return spy.log


@pytest.mark.parametrize("name", list(FACTORIES))
def test_candidate_future_mutation_truncation_and_same_bar(name):
    factory, bars = FACTORIES[name], bars_valid()
    base = run(factory, bars)
    assert (base.events.event == "ENTRY").sum() >= 3, "cenário sintético vazio para este candidato"
    base_log = run_spy(factory, bars)
    for t in probe_times(bars, base):
        mutated = run(factory, mutate_after(bars, t))
        pd.testing.assert_frame_equal(events_until(base, t), events_until(mutated, t))
        pd.testing.assert_frame_equal(equity_until(base, t), equity_until(mutated, t))
        truncated = run(factory, bars[bars.datetime <= t].reset_index(drop=True))
        pd.testing.assert_frame_equal(events_until(base, t), events_until(truncated, t))
        assert view_until(base_log, t) == view_until(run_spy(factory, mutate_same_bar(bars, t)), t)
        assert view_until(base_log, t) == view_until(run_spy(factory, mutate_after(bars, t)), t)
