"""Regras de execução do simulador (docs 05 §3–§5): nível de toque, gap, barra de entrada, custos."""
import pandas as pd
import pytest
from helpers import ScriptedStrategy, bar
from wdo import Config, OrderIntent, Position, WDOReplayEngine

WHEN = pd.Timestamp("2026-03-30 09:10", tz="America/Sao_Paulo")


def engine_with(config=None, script=None, session_orders=()):
    engine = WDOReplayEngine(config or Config(), ScriptedStrategy(script, session_orders))
    engine.session_active = True
    return engine


# ------------------------------------------------------------------ preço de execução de ordens a nível
@pytest.mark.parametrize("intent,b,expected", [
    (OrderIntent(1, "stop", 5001), bar(open=5000, high=5002, low=4999), 5001),        # rompimento: no nível
    (OrderIntent(1, "stop", 5001), bar(open=5003, high=5004, low=5002), 5003),        # gap além do nível: na abertura (pior)
    (OrderIntent(1, "stop", 5001), bar(open=5000, high=5000.5, low=4999), None),      # não tocada
    (OrderIntent(-1, "stop", 4999), bar(open=5000, high=5001, low=4998), 4999),
    (OrderIntent(-1, "stop", 4999), bar(open=4997, high=4998, low=4996), 4997),
    (OrderIntent(1, "limit", 4999), bar(open=5000, high=5001, low=4998), 4999),       # fade: no nível
    (OrderIntent(1, "limit", 4999), bar(open=4997, high=4999, low=4996), 4997),       # abre já além do nível: na abertura
    (OrderIntent(-1, "limit", 5001), bar(open=5000, high=5002, low=4999), 5001),
    (OrderIntent(-1, "limit", 5001), bar(open=5003, high=5004, low=5002), 5003),
])
def test_level_fill(intent, b, expected):
    assert WDOReplayEngine.level_fill(intent, b) == expected


def test_level_entry_is_never_outside_the_bar_range_and_not_the_open_unless_gapped():
    engine = engine_with()
    b = bar(open=5000, high=5003, low=4996)
    for level in (4996, 4997.5, 4999.5):                                  # compras a nível abaixo da abertura
        _, price, _ = engine.select_entry([OrderIntent(1, "limit", level)], b)
        assert b.low <= price <= b.high and price == level and price != b.open


def test_same_side_orders_touched_in_one_bar_use_the_worst_price():
    engine = engine_with()
    b = bar(open=5000, high=5003, low=4996)
    buy = [OrderIntent(1, "stop", 5002, "STOP"), OrderIntent(1, "limit", 4997, "LIMIT")]
    assert engine.select_entry(buy, b)[1:] == (5002, "STOP")                   # compra: o mais caro
    sell = [OrderIntent(-1, "stop", 4997, "STOP"), OrderIntent(-1, "limit", 5002, "LIMIT")]
    assert engine.select_entry(sell, b)[1:] == (4997, "STOP")                  # venda: o mais barato


def test_market_intent_fills_at_the_open_regardless_of_the_bar_range():
    narrow, wide = bar(open=5000, high=5000.5, low=4999.5, close=5000), bar(open=5000, high=5005, low=4995, close=5002)
    entries = []
    for b in (narrow, wide):
        e = engine_with(script={0: [OrderIntent(1, "market", None, "P4_RSI")]})
        e.process_session_bar(b, 0)
        entries.append((e.position.side, e.position.entry_price, e.position.entry_reason))
    assert entries[0] == entries[1] == (1, 5000, "P4_RSI")             # o range da barra não altera a decisão


# ------------------------------------------------------------------ barra de entrada (R9)
def test_entry_bar_stop_is_evaluated_and_target_is_not_credited():
    stop_case = engine_with(script={0: [OrderIntent(1, "market", None, "X")]})
    stop_case.process_session_bar(bar(open=5000, high=5001, low=4989, close=5000), 0)      # stop = 4990
    assert stop_case.position is None and stop_case.closed[-1]["exit_reason"] == "STOP_LOSS_ENTRY_BAR"

    target_case = engine_with(script={0: [OrderIntent(1, "market", None, "X")]})
    target_case.process_session_bar(bar(open=5000, high=5010, low=5000, close=5008), 0)    # alvo = 5006 dentro do range
    assert target_case.position is not None and not target_case.closed                     # não creditado na barra de entrada
    assert target_case.position.mfe == 8                                                   # MFE só pelo fechamento


# ------------------------------------------------------------------ gaps na saída (R4)
def test_stop_gap_fills_at_the_worse_open_and_target_gap_at_the_better_open():
    engine = engine_with()
    engine.position = Position(1, 1, WHEN, 5000, 1, 4990, 5006)
    engine.process_position(bar(open=4985, high=4988, low=4980))
    assert engine.closed[-1]["exit_price"] == 4985 and engine.closed[-1]["exit_reason"] == "STOP_LOSS"

    engine.position = Position(2, 1, WHEN, 5000, 1, 4990, 5006)
    engine.process_position(bar(open=5010, high=5012, low=5009))
    assert engine.closed[-1]["exit_price"] == 5010 and engine.closed[-1]["exit_reason"] == "TAKE_PROFIT"

    engine.position = Position(3, -1, WHEN, 5000, 1, 5010, 4994)                          # venda
    engine.process_position(bar(open=5015, high=5018, low=5013))
    assert engine.closed[-1]["exit_price"] == 5015


def test_target_first_policy_only_changes_the_ambiguous_case():
    engine = engine_with(Config(intrabar_policy="target_first"))
    engine.position = Position(1, 1, WHEN, 5000, 1, 4990, 5006)
    engine.process_position(bar(open=5000, high=5007, low=4989))
    assert engine.closed[-1]["exit_reason"] == "TARGET_INTRABAR_AMBIGUOUS" and engine.closed[-1]["exit_price"] == 5006


# ------------------------------------------------------------------ slippage, custos, limite diário
def test_slippage_and_costs_are_applied_against_the_trader():
    cfg = Config(slippage_points=0.5, commission_per_contract=0.8, fees_per_contract=0.2, point_value_brl=10.0)
    engine = engine_with(cfg, script={0: [OrderIntent(1, "market", None, "X")]})
    engine.process_session_bar(bar(open=5000, high=5000.5, low=4999.5, close=5000), 0)
    assert engine.position.entry_price == 5000.5                                      # compra paga slippage
    engine.exit(WHEN, 5006, "TAKE_PROFIT")
    trade = engine.closed[-1]
    assert trade["exit_price"] == 5005.5                                              # venda recebe menos
    assert trade["gross_pnl"] == 50.0 and trade["costs"] == 2.0 and trade["net_pnl"] == 48.0
    assert engine.cash == cfg.initial_capital + 48.0


def test_max_trades_per_day_is_a_config_rule():
    script = {0: [OrderIntent(1, "market", None, "A")], 1: [OrderIntent(1, "market", None, "B")]}
    engine = engine_with(Config(max_trades_per_day=2), script=script)
    engine.process_session_bar(bar(open=5000, high=5000.5, low=4999.5), 0)
    engine.exit(WHEN, 5000, "MANUAL")
    assert engine.process_session_bar(bar("2026-03-30 09:05"), 1) and engine.trade_id == 2


def test_strategy_never_sees_the_current_bar_range():
    strategy = ScriptedStrategy({0: []})
    engine = engine_with()
    engine.strategy = strategy
    engine.process_session_bar(bar(open=5000, high=5099, low=4901, close=5050), 0)
    seen = strategy.seen[0]
    assert not any(hasattr(seen, name) for name in ("high", "low", "close"))         # contrato point-in-time (R8)
