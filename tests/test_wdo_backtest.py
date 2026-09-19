from types import SimpleNamespace
import pandas as pd
import pytest
from wdo import Config, Position, WDOReplayEngine, round_tick, validate_bars, build_continuous_contract


def bars(rows):
    return pd.DataFrame(rows, columns=["datetime","open","high","low","close","volume"])


def test_round_tick():
    assert round_tick(5000.26, .5) == 5000.5
    assert round_tick(5000.24, .5) == 5000.0


def test_reject_duplicate_and_bad_ohlc():
    rows=[["2026-01-02 09:00",5000,5001,4999,5000,1],["2026-01-02 09:00",5000,5001,4999,5000,1]]
    with pytest.raises(ValueError, match="duplicados"): validate_bars(bars(rows))
    with pytest.raises(ValueError, match="OHLC"):
        validate_bars(bars([["2026-01-02 09:00",5000,4999,4998,5000,1]]))


def test_rollover_rejects_overlap():
    raw=bars([["2026-01-02 09:00",5000,5001,4999,5000,1]]).assign(contract="WDOF26")
    schedule=pd.DataFrame({"contract":["WDOF26","WDOG26"],"start":["2026-01-01","2026-01-02"],"end":["2026-01-02","2026-01-03"]})
    with pytest.raises(ValueError, match="sobreposto"): build_continuous_contract(raw,schedule,"2026-01-01","2026-01-03","America/Sao_Paulo")


def test_channel_modes_and_one_operation_per_day():
    engine=WDOReplayEngine(Config(channel_mode=0))
    engine.day_state={"pdh":5010,"pdl":4990,"sup":5003,"inf":4997,"operated":False}
    engine.place_channel_orders(-1)
    assert {order.kind for order in engine.pending} == {"stop","limit"}
    when=pd.Timestamp("2026-01-02 09:05",tz="America/Sao_Paulo")
    engine.enter(when,1,5000,"P1")
    first=engine.position.trade_id
    engine.enter(when,-1,5000,"P2")
    assert engine.position.trade_id == first


def test_p2_reference_and_conservative_stop_target():
    engine=WDOReplayEngine(Config(intrabar_policy="adverse"))
    when=pd.Timestamp("2026-01-02 09:10",tz="America/Sao_Paulo")
    engine.day_state={"operated":False,"pattern":2,"reference":SimpleNamespace(low=4999,high=5001)}
    engine.signal(SimpleNamespace(datetime=when,open=5000,low=4998,high=5000,rsi=50),2)
    assert engine.position is not None and engine.position.side == 1
    engine.position=Position(1,1,when,5000,1,4990,5006)
    engine.process_position(SimpleNamespace(datetime=when,low=4989,high=5007))
    assert engine.closed[-1]["exit_reason"] == "STOP_INTRABAR_AMBIGUOUS"


def test_p4_immediate_rsi_entry():
    engine=WDOReplayEngine(Config())
    when=pd.Timestamp("2026-01-02 09:00",tz="America/Sao_Paulo")
    engine.day_state={"operated":False,"pattern":4,"direction":1,"wait":False,"open_rsi":12}
    engine.signal(SimpleNamespace(datetime=when,open=5000,low=4999,high=5001,rsi=12),0)
    assert engine.position is not None and engine.position.side == 1
