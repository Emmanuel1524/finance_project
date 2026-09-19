"""Capacidade de saída do motor 1.1.0 (ExitSpec): validação, alvo opcional, horário, trailing, gaps,
barra de entrada e ausência de vazamento. Sem ExitSpec o comportamento é o do V0 (provado em
test_engine_frozen.py e na comparação 1.0.0 × 1.1.0)."""
import math
from datetime import time

import pandas as pd
import pytest
from helpers import ScriptedStrategy, bar, equity_until, events_until
from test_leakage import bars_valid, mutate_after, mutate_same_bar, probe_times
from wdo import Config, ExitSpec, OrderIntent, WDOReplayEngine

TZ = "America/Sao_Paulo"
WHEN = pd.Timestamp("2026-03-30 09:05", tz=TZ)


def new_engine(config=None):
    return WDOReplayEngine(config or Config(), ScriptedStrategy())


def enter(engine, side=1, raw=5000.0, spec=None, when=WHEN):
    return engine.open_position(when, side, raw, "X", spec)


# ------------------------------------------------------------------ níveis a partir da ExitSpec
def test_without_exit_spec_the_config_stop_and_target_apply():
    p = enter(new_engine())
    assert (p.stop_initial, p.target_initial) == (4990, 5006) and p.trail_points is None and p.exit_deadline is None


def test_distances_are_measured_from_the_slipped_entry_price():
    engine = new_engine(Config(slippage_points=0.5))
    p = enter(engine, 1, 5000.0, ExitSpec(stop_points=7, target_points=14))
    assert (p.entry_price, p.stop_initial, p.target_initial) == (5000.5, 4993.5, 5014.5)
    q = enter(new_engine(Config(slippage_points=0.5)), -1, 5000.0, ExitSpec(stop_points=7, target_points=14))
    assert (q.entry_price, q.stop_initial, q.target_initial) == (4999.5, 5006.5, 4985.5)


def test_absolute_structure_levels_are_used_as_given():
    p = enter(new_engine(), 1, 5000.0, ExitSpec(stop_price=4995.0, target_price=5012.0))
    assert (p.stop_initial, p.target_initial) == (4995.0, 5012.0)
    q = enter(new_engine(), -1, 5000.0, ExitSpec(stop_price=5004.0, target_price=4990.0))
    assert (q.stop_initial, q.target_initial) == (5004.0, 4990.0)


def test_no_target_means_no_take_profit_and_nan_in_the_trade_log():
    engine = new_engine()
    enter(engine, 1, 5000.0, ExitSpec(stop_points=5))
    engine.process_position(bar("2026-03-30 09:10", open=5001, high=5100, low=5000))
    assert engine.position is not None                                   # sem alvo: não realiza lucro
    engine.process_position(bar("2026-03-30 09:15", open=5001, high=5002, low=4990))
    trade = engine.closed[-1]
    assert trade["exit_reason"] == "STOP_LOSS" and math.isnan(trade["target_price_inicial"])


@pytest.mark.parametrize("spec,side,message", [
    (ExitSpec(), 1, "exatamente um"),                                    # sem stop
    (ExitSpec(stop_points=5, stop_price=4995.0), 1, "exatamente um"),
    (ExitSpec(stop_points=0), 1, "> 0"),
    (ExitSpec(stop_points=0.1), 1, "lado protetivo"),                    # arredonda para a própria entrada
    (ExitSpec(stop_price=5001.0), 1, "lado protetivo"),
    (ExitSpec(stop_price=4999.0), -1, "lado protetivo"),
    (ExitSpec(stop_points=5, target_points=3, target_price=5010.0), 1, "no máximo um"),
    (ExitSpec(stop_points=5, target_points=-2), 1, "> 0"),
    (ExitSpec(stop_points=5, target_price=4999.0), 1, "lado favorável"),
    (ExitSpec(stop_points=5, trailing_points=0), 1, "> 0"),
    (ExitSpec(stop_points=5, exit_time=time(9, 5)), 1, "posterior"),
    (ExitSpec(stop_points=5, exit_time=time(9, 0)), 1, "posterior"),
])
def test_invalid_exit_specs_fail_loudly(spec, side, message):
    with pytest.raises(ValueError, match=message):
        enter(new_engine(), side, 5000.0, spec)


# ------------------------------------------------------------------ saída por horário
def test_time_exit_closes_at_the_open_of_the_first_bar_at_or_after_the_deadline():
    cfg = Config(slippage_points=0.5)
    engine = new_engine(cfg)
    enter(engine, 1, 5000.0, ExitSpec(stop_points=20, exit_time=time(9, 20)))
    engine.process_position(bar("2026-03-30 09:10", open=5001, high=5003, low=4999))
    engine.process_position(bar("2026-03-30 09:15", open=5002, high=5004, low=5000))
    assert engine.position is not None                                   # antes do horário: nada
    engine.process_position(bar("2026-03-30 09:20", open=5003, high=5030, low=4900))   # movimento da barra é ignorado
    trade = engine.closed[-1]
    assert trade["exit_reason"] == "TIME_EXIT" and trade["exit_price"] == 5002.5      # abertura 5003 − slippage 0,5
    assert trade["exit_datetime"] == pd.Timestamp("2026-03-30 09:20", tz=TZ)


def test_time_exit_takes_effect_on_a_later_bar_if_the_exact_bar_is_missing():
    engine = new_engine()
    enter(engine, 1, 5000.0, ExitSpec(stop_points=20, exit_time=time(9, 20)))
    engine.process_position(bar("2026-03-30 09:25", open=5004, high=5006, low=5002))   # 09:20 não existe: 1ª barra >= 09:20
    assert engine.closed[-1]["exit_reason"] == "TIME_EXIT" and engine.closed[-1]["exit_price"] == 5004


def test_stop_before_the_deadline_wins_over_the_time_exit():
    engine = new_engine()
    enter(engine, 1, 5000.0, ExitSpec(stop_points=5, exit_time=time(9, 30)))
    engine.process_position(bar("2026-03-30 09:10", open=5000, high=5001, low=4990))
    assert engine.closed[-1]["exit_reason"] == "STOP_LOSS"


# ------------------------------------------------------------------ trailing
def test_trailing_stop_ratchets_with_closed_bars_and_never_loosens():
    engine = new_engine()
    p = enter(engine, 1, 5000.0, ExitSpec(stop_points=10, trailing_points=4))
    engine.process_position(bar("2026-03-30 09:10", open=5001, high=5010, low=5002))
    assert p.stop_current == 5006                                        # 5010 − 4, vale para a barra SEGUINTE
    engine.process_position(bar("2026-03-30 09:15", open=5008, high=5009, low=5007))
    assert p.stop_current == 5006 and engine.position is p              # máxima menor: o stop não afrouxa
    engine.process_position(bar("2026-03-30 09:20", open=5008, high=5014, low=5005))   # low <= 5006
    assert engine.closed[-1]["exit_reason"] == "TRAILING_STOP" and engine.closed[-1]["exit_price"] == 5006


def test_trailing_uses_only_previous_bars_not_the_current_one():
    engine = new_engine()
    p = enter(engine, 1, 5000.0, ExitSpec(stop_points=10, trailing_points=4))
    engine.process_position(bar("2026-03-30 09:10", open=5000, high=5020, low=4995))   # máxima 5020 e mínima 4995
    assert engine.position is p                                          # o stop de 5016 (só da barra seguinte) não vale nela
    assert p.stop_current == 5016


def test_trailing_stop_gap_fills_at_the_worse_open():
    engine = new_engine()
    enter(engine, 1, 5000.0, ExitSpec(stop_points=10, trailing_points=4))
    engine.process_position(bar("2026-03-30 09:10", open=5001, high=5010, low=5002))   # stop -> 5006
    engine.process_position(bar("2026-03-30 09:15", open=5000, high=5001, low=4998))   # abre abaixo do stop
    assert engine.closed[-1]["exit_price"] == 5000 and engine.closed[-1]["exit_reason"] == "TRAILING_STOP"


def test_trailing_ignores_the_entry_bar_extremes_and_short_side_mirrors_long():
    engine = new_engine()
    engine.session_active = True
    engine.strategy = ScriptedStrategy({0: [OrderIntent(1, "market", None, "X", exit=ExitSpec(stop_points=10, trailing_points=4))]})
    engine.process_session_bar(bar(open=5000, high=5020, low=4999, close=5010), 0)
    assert engine.position.best_price == 5000 and engine.position.stop_current == 4990   # máxima da barra de entrada ignorada
    short = new_engine()
    p = enter(short, -1, 5000.0, ExitSpec(stop_points=10, trailing_points=4))
    short.process_position(bar("2026-03-30 09:10", open=4999, high=4998, low=4990))
    assert p.stop_current == 4994                                        # 4990 + 4
    short.process_position(bar("2026-03-30 09:15", open=4993, high=4995, low=4992))
    assert short.closed[-1]["exit_reason"] == "TRAILING_STOP" and short.closed[-1]["exit_price"] == 4994


# ------------------------------------------------------------------ barra de entrada e ambiguidade
def test_entry_bar_uses_the_spec_stop_with_adverse_assumption():
    engine = new_engine()
    engine.session_active = True
    engine.strategy = ScriptedStrategy({0: [OrderIntent(1, "market", None, "X", exit=ExitSpec(stop_points=3, target_points=2))]})
    engine.process_session_bar(bar(open=5000, high=5010, low=4996), 0)   # alvo (5002) e stop (4997) cabem na barra
    assert engine.closed[-1]["exit_reason"] == "STOP_LOSS_ENTRY_BAR" and engine.closed[-1]["exit_price"] == 4997


def test_stop_and_target_in_the_same_later_bar_resolve_against_the_strategy():
    engine = new_engine()
    enter(engine, 1, 5000.0, ExitSpec(stop_points=5, target_points=5))
    engine.process_position(bar("2026-03-30 09:10", open=5000, high=5006, low=4994))
    assert engine.closed[-1]["exit_reason"] == "STOP_INTRABAR_AMBIGUOUS" and engine.closed[-1]["exit_price"] == 4995


def test_the_exit_spec_of_the_chosen_intent_is_the_one_applied():
    engine = new_engine()
    engine.session_active = True
    a = OrderIntent(1, "stop", 5002, "A", exit=ExitSpec(stop_points=10))
    b = OrderIntent(1, "limit", 4997, "B", exit=ExitSpec(stop_points=20))
    engine.strategy = ScriptedStrategy({0: [a, b]})
    engine.process_session_bar(bar(open=5000, high=5003, low=4996, close=5000), 0)   # as duas tocadas: vale a pior (5002)
    assert engine.position.entry_reason == "A" and engine.position.stop_initial == 4992


# ------------------------------------------------------------------ sem vazamento: replay completo com saídas adaptativas
class AdaptiveExitStrategy:
    """Entra a mercado na 2ª barra na direção do corpo da 1ª e usa saída adaptativa calculada só com a barra anterior."""
    name = "adaptive_exit_test"

    def on_session_open(self, ctx):
        from wdo import SessionDecision
        return SessionDecision(label="ADAPTIVE")

    def on_bar_open(self, bar_open):
        prev = bar_open.prev_bar
        if bar_open.index_in_session != 1 or prev is None or prev.close == prev.open:
            return []
        side = 1 if prev.close > prev.open else -1
        distance = max(3.0, 1.5 * (prev.high - prev.low))                 # ATR de 1 barra fechada: point-in-time
        return [OrderIntent(side, "market", None, "ADAPTIVE", exit=ExitSpec(stop_points=distance, trailing_points=distance, exit_time=time(12, 0)))]

    def on_bar_close(self, bar_close, *, entered):
        pass


def run_adaptive(bars):
    return WDOReplayEngine(Config(slippage_points=0.5, commission_per_contract=0.8, fees_per_contract=0.2), AdaptiveExitStrategy()).run(bars)


def test_adaptive_exits_do_not_depend_on_future_or_same_bar_data():
    bars = bars_valid()
    base = run_adaptive(bars)
    assert (base.events.event == "ENTRY").sum() >= 6
    assert {"TIME_EXIT", "TRAILING_STOP", "STOP_LOSS"} & set(base.trades.exit_reason)   # o cenário exercita as saídas novas
    for t in probe_times(bars, base):
        pd.testing.assert_frame_equal(events_until(base, t), events_until(run_adaptive(mutate_after(bars, t)), t))
        pd.testing.assert_frame_equal(equity_until(base, t), equity_until(run_adaptive(mutate_after(bars, t)), t))
        pd.testing.assert_frame_equal(events_until(base, t), events_until(run_adaptive(bars[bars.datetime <= t].reset_index(drop=True)), t))
    for _, trade in base.trades.iterrows():
        t = trade.entry_datetime
        again = run_adaptive(mutate_same_bar(bars, t)).trades
        same = again[again.entry_datetime == t]
        assert len(same) == 1 and (same.iloc[0].side, same.iloc[0].entry_price) == (trade.side, trade.entry_price)   # entrada a mercado não muda
        break
