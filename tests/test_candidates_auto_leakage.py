"""Testes de vazamento AUTOMÁTICOS (docs 05 §11): descobre toda classe de estratégia em
`wdo.strategies.candidates*` que ainda não tenha teste explícito e aplica a bateria (mutação do futuro, histórico
truncado, mutação da mesma barra). Um candidato novo passa a ser coberto sem escrever teste.

Atributos opcionais da classe do candidato:
- `leakage_scenario = "long"`: precisa de barras até 17:55 (janela 09:00–18:00); padrão "short" (09:00–12:55).
- `leakage_config = {...}`: overrides de `Config` (ex.: `max_trades_per_day`).

Checagem rápida de UM candidato (segundos):  pytest tests/test_candidates_auto_leakage.py -k NomeDaClasse
"""
import importlib
import inspect
import pkgutil
from dataclasses import replace

import pandas as pd
import pytest
from helpers import equity_until, events_until, make_bars
from test_candidates_leakage import FACTORIES as RUN1_EXPLICIT, GenericSpy
from test_candidates_run2_leakage import LONG_DAY as RUN2_LONG, SHORT as RUN2_SHORT
from test_leakage import mutate_after, mutate_same_bar, probe_times, view_until
from wdo import Config, WDOReplayEngine, validate_bars
import wdo.strategies as strategies_pkg

EXPLICIT = set(RUN1_EXPLICIT.values()) | set(RUN2_SHORT.values()) | set(RUN2_LONG.values())
HINTS = {"LateDayMomentum": {"leakage_scenario": "long"}}    # candidatos antigos, sem alterar o código deles
SEEDS = (7, 11, 21, 3, 5)                    # cenários sintéticos alternativos até haver entradas suficientes


def discover():
    found = {}
    for info in pkgutil.iter_modules(strategies_pkg.__path__):
        if not info.name.startswith("candidates"):
            continue
        module = importlib.import_module(f"wdo.strategies.{info.name}")
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module.__name__ and hasattr(cls, "on_bar_open") and hasattr(cls, "on_session_open"):
                if cls not in EXPLICIT:
                    found[name] = cls
    return found


CANDIDATES = discover()


def scenario(cls, seed):
    hints = HINTS.get(cls.__name__, {})
    overrides = dict(hints.get("leakage_config", getattr(cls, "leakage_config", {})))
    if hints.get("leakage_scenario", getattr(cls, "leakage_scenario", "short")) == "long":
        overrides = {"start_hour": 9, "start_minute": 0, "end_hour": 18, "end_minute": 0, **overrides}
        return validate_bars(make_bars(days=30, seed=seed, bars_per_day=114)), replace(Config(), **overrides)
    return validate_bars(make_bars(days=45, seed=seed)), replace(Config(), **overrides)


def run(cls, cfg, bars):
    return WDOReplayEngine(cfg, cls(cfg)).run(bars)


def run_spy(cls, cfg, bars):
    spy = GenericSpy(cls(cfg))
    WDOReplayEngine(cfg, spy).run(bars)
    return spy.log


def test_at_least_one_candidate_is_discovered_or_all_are_explicit():
    assert isinstance(CANDIDATES, dict)


@pytest.mark.parametrize("name", sorted(CANDIDATES))
def test_auto_discovered_candidate_has_no_leakage(name):
    cls = CANDIDATES[name]
    for seed in SEEDS:
        bars, cfg = scenario(cls, seed)
        base = run(cls, cfg, bars)
        if (base.events.event == "ENTRY").sum() >= 3:
            break
    else:
        pytest.fail(f"{name}: cenário sintético sem entradas suficientes (>= 3); defina leakage_scenario/leakage_config")
    times = probe_times(bars, base)
    times = [times[0], times[len(times) // 2], times[-1]]
    base_log = run_spy(cls, cfg, bars)
    for t in times:
        future = run(cls, cfg, mutate_after(bars, t))
        pd.testing.assert_frame_equal(events_until(base, t), events_until(future, t))
        pd.testing.assert_frame_equal(equity_until(base, t), equity_until(future, t))
        truncated = run(cls, cfg, bars[bars.datetime <= t].reset_index(drop=True))
        pd.testing.assert_frame_equal(events_until(base, t), events_until(truncated, t))
        assert view_until(base_log, t) == view_until(run_spy(cls, cfg, mutate_same_bar(bars, t)), t)
