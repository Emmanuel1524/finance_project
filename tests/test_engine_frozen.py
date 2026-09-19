"""Regressão do motor congelado (docs 05 §10).

Este teste é a trava de congelamento: qualquer mudança de comportamento do simulador ou do V0 quebra
o resultado abaixo. Se a mudança for uma correção aprovada, o procedimento é: aprovar, subir
`ENGINE_VERSION`, atualizar os valores de referência e reexecutar o V0 e os candidatos relevantes.
"""
import hashlib

from helpers import make_bars
from wdo import ENGINE_VERSION, Config, WDOReplayEngine, validate_bars

REFERENCE = {
    "engine_version": "1.0.0",
    "n_trades": 21,
    "entry_reasons": {"P2_HIGH": 1, "P2_LOW": 1, "P3_LIMIT": 10, "P3_STOP": 7, "P4_RSI": 2},
    "exit_reasons": {"END_OF_DATA": 1, "STOP_LOSS": 9, "TAKE_PROFIT": 11},
    "net_pnl": -437.0,
    "final_cash": 9620.0,
    "n_events": 66,
    "trades_hash": "b9bbe1b7bba95c74",
}


def test_frozen_engine_regression_on_synthetic_data():
    cfg = Config(slippage_points=0.5, commission_per_contract=0.8, fees_per_contract=0.2)
    result = WDOReplayEngine(cfg).run(validate_bars(make_bars(days=45, seed=7)))
    t = result.trades
    got = {
        "engine_version": ENGINE_VERSION,
        "n_trades": int(len(t)),
        "entry_reasons": t.entry_reason.value_counts().sort_index().to_dict(),
        "exit_reasons": t.exit_reason.value_counts().sort_index().to_dict(),
        "net_pnl": round(float(t.net_pnl.sum()), 2),
        "final_cash": round(float(result.equity.cash.iloc[-1]), 2),
        "n_events": int(len(result.events)),
        "trades_hash": hashlib.sha256(t[["entry_datetime", "side", "entry_price", "exit_datetime", "exit_price"]]
                                      .astype(str).to_csv(index=False).encode()).hexdigest()[:16],
    }
    assert got == REFERENCE
    assert result.engine_version == ENGINE_VERSION and result.strategy_name == "baseline_v0"
