"""Testes originais (6), com a mesma intenção, adaptados à separação estratégia/simulador."""
import pandas as pd
import pytest
from helpers import ScriptedStrategy, bar, session_ctx
from wdo import (
    BarOpen, BaselineV0, Config, OrderIntent, Position, WDOReplayEngine, round_tick, validate_bars,
    build_continuous_contract,
)


def bars(rows):
    return pd.DataFrame(rows, columns=["datetime", "open", "high", "low", "close", "volume"])


def test_round_tick():
    assert round_tick(5000.26, .5) == 5000.5
    assert round_tick(5000.24, .5) == 5000.0


def test_reject_duplicate_and_bad_ohlc():
    rows = [["2026-01-02 09:00", 5000, 5001, 4999, 5000, 1], ["2026-01-02 09:00", 5000, 5001, 4999, 5000, 1]]
    with pytest.raises(ValueError, match="duplicados"):
        validate_bars(bars(rows))
    with pytest.raises(ValueError, match="OHLC"):
        validate_bars(bars([["2026-01-02 09:00", 5000, 4999, 4998, 5000, 1]]))


def test_rollover_rejects_overlap():
    raw = bars([["2026-01-02 09:00", 5000, 5001, 4999, 5000, 1]]).assign(contract="WDOF26")
    schedule = pd.DataFrame({"contract": ["WDOF26", "WDOG26"], "start": ["2026-01-01", "2026-01-02"], "end": ["2026-01-02", "2026-01-03"]})
    with pytest.raises(ValueError, match="sobreposto"):
        build_continuous_contract(raw, schedule, "2026-01-01", "2026-01-03", "America/Sao_Paulo")


def test_channel_modes_and_one_operation_per_day():
    # Padrão 3: abertura dentro do canal superior [sup, PDH] -> ordens de venda conforme o modo do canal
    ctx = session_ctx(open=5095.0, pdh=5100.0, pdl=4900.0)           # sup = 5100 - 7 = 5093
    kinds = {mode: {o.kind for o in BaselineV0(Config(channel_mode=mode)).on_session_open(ctx).orders} for mode in (0, 1, 2)}
    assert kinds == {0: {"stop", "limit"}, 1: {"stop"}, 2: {"limit"}}
    decision = BaselineV0(Config(channel_mode=0)).on_session_open(ctx)
    assert decision.label == "P3" and all(o.side == -1 and o.lifetime == "session" for o in decision.orders)

    # uma operação por dia: depois da 1ª entrada (e mesmo depois da saída), nada mais entra
    engine = WDOReplayEngine(Config(), ScriptedStrategy({
        0: [OrderIntent(1, "market", None, "P1")], 1: [OrderIntent(-1, "market", None, "P2")], 2: [OrderIntent(-1, "market", None, "P2")]}))
    engine.session_active = True
    assert engine.process_session_bar(bar("2026-03-30 09:00"), 0)
    first = engine.position.trade_id
    engine.exit(pd.Timestamp("2026-03-30 09:01", tz="America/Sao_Paulo"), 5001, "MANUAL")
    assert not engine.process_session_bar(bar("2026-03-30 09:05"), 1)
    assert not engine.process_session_bar(bar("2026-03-30 09:10"), 2)
    assert engine.trade_id == first and engine.position is None


def test_p2_reference_and_conservative_stop_target():
    strategy = BaselineV0(Config())
    assert strategy.on_session_open(session_ctx(open=5000.0)).label == "P1"        # entre os canais
    strategy.on_bar_open(BarOpen(None, 5000.0, 50.0, 0, None))                       # 1ª barra: sem toque
    prev = bar("2026-03-30 09:00", 5000, 5001, 4999, 5000)
    intents = strategy.on_bar_open(BarOpen(None, 5000.0, 50.0, 1, prev))             # Padrão 2: referência = barra anterior
    assert [(i.side, i.kind, i.price, i.tag) for i in intents] == [(1, "limit", 4999, "P2_LOW"), (-1, "limit", 5001, "P2_HIGH")]

    engine = WDOReplayEngine(Config(intrabar_policy="adverse"))
    _, price, tag = engine.select_entry(intents, bar(open=5000, high=5000, low=4998))
    assert (price, tag) == (4999, "P2_LOW")            # entra no nível da referência, e não no open da barra
    _, price, tag = engine.select_entry(intents, bar(open=5000, high=5002, low=4998))
    assert (price, tag) == (4999, "P2_AMBIGUOUS_LOW_FIRST")   # as duas pernas tocadas: convenção do V0

    when = pd.Timestamp("2026-03-30 09:10", tz="America/Sao_Paulo")
    engine.position = Position(1, 1, when, 5000, 1, 4990, 5006)
    engine.process_position(bar(open=5000, low=4989, high=5007))
    assert engine.closed[-1]["exit_reason"] == "STOP_INTRABAR_AMBIGUOUS"          # stop e alvo na mesma barra: stop


def test_p4_immediate_rsi_entry():
    strategy = BaselineV0(Config())
    decision = strategy.on_session_open(session_ctx(open=4800.0, pdh=5100.0, pdl=4900.0, rsi=12.0))   # abaixo do canal, IFR 10-16
    assert decision.label == "P4"
    engine = WDOReplayEngine(Config(), strategy)
    engine.session_active = True
    assert engine.process_session_bar(bar("2026-03-30 09:00", open=4800, high=4801, low=4799, close=4800, rsi=12.0), 0)
    assert engine.position.side == 1 and engine.position.entry_price == 4800 and engine.position.entry_reason == "P4_RSI"
