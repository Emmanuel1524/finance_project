"""Testes de vazamento (docs 05 §11) para os candidatos da RUN-0002, incluindo ExitSpec (stop por nível, trailing,
saída por horário): mutação do futuro, histórico truncado e mutação da mesma barra (o que a estratégia enxerga)."""
import pandas as pd
import pytest
from helpers import equity_until, events_until, make_bars
from test_candidates_leakage import GenericSpy
from test_leakage import bars_valid, mutate_after, mutate_same_bar, probe_times, view_until
from wdo import Config, WDOReplayEngine, validate_bars
from wdo.strategies.candidates_run2 import (
    GapAndGoFillStop, LateDayMomentumExit, OpeningRange30Breakout, OrbAdaptiveExit, OrbFixedExit, OrbStructuralStop,
    OrbStructuralVolGate, V0NoChannelScaledRR, V0NoChannelSymmetricRR,
)

SHORT = {"orb_adaptive": OrbAdaptiveExit, "orb_fixed": OrbFixedExit, "orb_structural": OrbStructuralStop,
         "orb_structural_volgate": OrbStructuralVolGate, "or30": OpeningRange30Breakout,
         "v0_nochannel_symmetric": V0NoChannelSymmetricRR, "v0_nochannel_scaled": V0NoChannelScaledRR}
LONG_DAY = {"late_day_momentum": LateDayMomentumExit, "gap_and_go": GapAndGoFillStop}      # precisam de barras até 17:55


def scenario(kind):
    if kind == "long":
        cfg = Config(start_hour=9, start_minute=0, end_hour=18, end_minute=0)
        return validate_bars(make_bars(days=30, seed=7, bars_per_day=114)), cfg
    return bars_valid(), Config()


def run(factory, cfg, bars):
    return WDOReplayEngine(cfg, factory(cfg)).run(bars)


def run_spy(factory, cfg, bars):
    spy = GenericSpy(factory(cfg))
    WDOReplayEngine(cfg, spy).run(bars)
    return spy.log


def check(factory, kind):
    bars, cfg = scenario(kind)
    base = run(factory, cfg, bars)
    assert (base.events.event == "ENTRY").sum() >= 3, "cenário sintético vazio para este candidato"
    times = probe_times(bars, base)
    times = [times[0], times[len(times) // 2], times[-1]]
    base_log = run_spy(factory, cfg, bars)
    for t in times:
        future = run(factory, cfg, mutate_after(bars, t))
        pd.testing.assert_frame_equal(events_until(base, t), events_until(future, t))
        pd.testing.assert_frame_equal(equity_until(base, t), equity_until(future, t))
        truncated = run(factory, cfg, bars[bars.datetime <= t].reset_index(drop=True))
        pd.testing.assert_frame_equal(events_until(base, t), events_until(truncated, t))
        assert view_until(base_log, t) == view_until(run_spy(factory, cfg, mutate_same_bar(bars, t)), t)


@pytest.mark.parametrize("name", list(SHORT))
def test_run2_candidate_has_no_leakage(name):
    check(SHORT[name], "short")


@pytest.mark.parametrize("name", list(LONG_DAY))
def test_run2_full_day_candidate_has_no_leakage(name):
    check(LONG_DAY[name], "long")
